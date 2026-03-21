# Parity Swarm — Complete Setup & Patch Guide

This document records every change made to get the pipeline working.
Follow this exactly on a fresh server to reproduce the working state.

---

## 1. Server & Infrastructure

```
Server: Lambda A100 40GB
SSH key: ~/.ssh/lambda_research
Hostname: baba
IP: 129.213.28.140
```

---

## 2. Initial Setup

```bash
# SSH in
ssh -i ~/.ssh/lambda_research ubuntu@129.213.28.140

# Install ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull qwen2.5:32b

# Clone repo
git clone https://github.com/m-zest/parity-swarm.git
cd parity-swarm

# Install Python dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download sentence transformer model (needed by OASIS)
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-MiniLM-L6-v2', cache_folder='./models')"
```

---

## 3. Environment Variables

Create `~/parity-swarm/.env`:

```dotenv
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=qwen2.5:32b

# Simulation runner (Step 5) - local ollama
SIM_LLM_API_KEY=ollama
SIM_LLM_BASE_URL=http://localhost:11434/v1
SIM_LLM_MODEL_NAME=qwen2.5:32b

GEMINI_API_KEY=your_gemini_key_here
ZEP_API_KEY=your_zep_key_here
SWARM_ENGINE_URL=http://localhost:5001
SIMULATION_ROUNDS=3
MAX_SIMULATION_ROUNDS=5
SLEEP_BETWEEN_SIMULATIONS=30
MODEL_TIMEOUT=60
```

---

## 4. Repo File Patches (tracked in git, already applied)

### 4.1 `backend/app/services/graph_builder.py`

**What:** LLM generates entity/edge names in lowercase. Zep requires PascalCase.

**Fix:** Added `to_pascal_case()` function and applied it to all entity names,
edge names, and source/target fields. Added fallback to `"Entity"` if name
not recognized.

```python
# Added inside set_ontology() before entity_types loop:
def to_pascal_case(name: str) -> str:
    """Convert any string to PascalCase for Zep compatibility"""
    import re
    parts = re.split(r'[_\s\-]+', name)
    return ''.join(p.capitalize() for p in parts if p)

# Entity names:
name = to_pascal_case(entity_def["name"])

# Edge names:
name = to_pascal_case(edge_def["name"]).upper()

# Source/target with fallback:
src = to_pascal_case(st.get("source", "Entity"))
tgt = to_pascal_case(st.get("target", "Entity"))
if src not in entity_types:
    src = "Entity"
if tgt not in entity_types:
    tgt = "Entity"
```

---

### 4.2 `backend/app/services/simulation_config_generator.py`

**What:** Simulation starts at hour 0 but agents had active_hours like [9-23].
No agents ever activated.

**Fix:** Changed all active_hours ranges to `range(0, 24)`.

```python
# All occurrences of range(8,23), range(9,23), [8,9,10...] etc
# changed to:
list(range(0, 24))
```

---

### 4.3 `backend/scripts/run_twitter_simulation.py`

**What:** Multiple bugs preventing agents from calling LLM.

**Fixes:**
```python
# 1. Added SIM_LLM_* env var support
llm_api_key = os.environ.get("SIM_LLM_API_KEY") or os.environ.get("LLM_API_KEY", "")
llm_base_url = os.environ.get("SIM_LLM_BASE_URL") or os.environ.get("LLM_BASE_URL", "")
llm_model = os.environ.get("SIM_LLM_MODEL_NAME") or os.environ.get("LLM_MODEL_NAME", "")

# 2. Added api_key and url to ModelFactory.create()
return ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=llm_model,
    api_key=llm_api_key,
    url=llm_base_url if llm_base_url else None,
    model_config_dict={"max_tokens": 600, "timeout": 60},
)

# 3. Semaphore reduced to 1 (ollama handles one request at a time)
semaphore=1

# 4. Active hours default
active_hours = cfg.get("active_hours", list(range(0, 24)))

# 5. Fallback for empty candidates
if not candidates:
    candidates = [cfg.get('agent_id', 0) for cfg in agent_configs]
```

---

### 4.4 `backend/research/experiment.py`

**What:** CLI experiment hung because subprocess entered wait_for_commands
mode after finishing rounds and nobody sent close-env. Also report polling
was broken (404 error).

**Fixes:**
```python
# 1. max_rounds set to 10
"max_rounds": 10,

# 2. poll_simulation() now detects env_alive and sends close-env
def poll_simulation(sim_id: str, timeout: int = 1800) -> dict:
    deadline = time.monotonic() + timeout
    close_sent = False
    while time.monotonic() < deadline:
        r = requests.get(f"{SWARM_ENGINE_URL}/api/simulation/{sim_id}/run-status", timeout=30)
        r.raise_for_status()
        data = r.json()["data"]
        runner = data.get("runner_status", "")
        if runner in ("completed", "stopped"):
            return data
        if runner == "failed":
            raise RuntimeError("Simulation run failed")
        if not close_sent:
            try:
                env_r = requests.post(
                    f"{SWARM_ENGINE_URL}/api/simulation/env-status",
                    json={"simulation_id": sim_id}, timeout=10,
                )
                if env_r.json().get("data", {}).get("env_alive"):
                    log.info("  Rounds complete, sending close-env...")
                    requests.post(
                        f"{SWARM_ENGINE_URL}/api/simulation/close-env",
                        json={"simulation_id": sim_id, "timeout": 30}, timeout=60,
                    )
                    close_sent = True
            except Exception:
                pass
        time.sleep(5)
    raise TimeoutError(f"Simulation {sim_id} timed out after {timeout}s")

# 3. poll_report_task() added for async report generation
def poll_report_task(sim_id, task_id, report_id, timeout=600):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = requests.post(
            f"{SWARM_ENGINE_URL}/api/report/generate/status",
            json={"task_id": task_id, "simulation_id": sim_id}, timeout=30,
        )
        data = r.json()["data"]
        if data.get("status") == "completed":
            return
        if data.get("status") == "failed":
            raise RuntimeError(f"Report failed: {data.get('message')}")
        time.sleep(5)
    raise TimeoutError(f"Report task timed out")
```

---

## 5. OASIS Venv Patches (NOT in git, must reapply manually)

These files are inside the venv and not tracked by git.
Reapply after every fresh `pip install`.

### 5.1 Fix recsys crash

**File:** `backend/venv/lib/python3.10/site-packages/oasis/environment/env.py`

**What:** twhin-bert tries to download 500MB model and crashes.

```bash
# Find the line and change it
grep -n "recsys_type" backend/venv/lib/python3.10/site-packages/oasis/environment/env.py
# Change: recsys_type="twhin-bert"
# To:     recsys_type="random"

sed -i 's/recsys_type="twhin-bert"/recsys_type="random"/' \
  backend/venv/lib/python3.10/site-packages/oasis/environment/env.py
```

---

### 5.2 Fix DB deadlock

**File:** `backend/venv/lib/python3.10/site-packages/oasis/social_platform/platform.py`

**What:** DB deadlock between platform.running() and update_rec_table().

```bash
# Change commit=True to commit=False
grep -n "update_rec_table(commit=True)" \
  backend/venv/lib/python3.10/site-packages/oasis/social_platform/platform.py

sed -i 's/update_rec_table(commit=True)/update_rec_table(commit=False)/' \
  backend/venv/lib/python3.10/site-packages/oasis/social_platform/platform.py
```

---

### 5.3 Fix asyncio gather timeout

**File:** `backend/venv/lib/python3.10/site-packages/oasis/environment/env.py`

**What:** asyncio.gather() has no timeout — one slow agent blocks forever.

```bash
sed -i 's/        await asyncio.gather(\*tasks)/        await asyncio.wait_for(asyncio.gather(*tasks), timeout=120)/' \
  backend/venv/lib/python3.10/site-packages/oasis/environment/env.py
```

---

### 5.4 Fix agent memory overflow and timeout

**File:** `backend/venv/lib/python3.10/site-packages/oasis/social_agent/agent.py`

**What:** camel-ai accumulates full history across rounds — context grows
huge and ollama hangs. Also need asyncio timeout on individual agent calls.

```bash
# Step 1: Find the __future__ import line number
grep -n "from __future__" \
  backend/venv/lib/python3.10/site-packages/oasis/social_agent/agent.py

# Step 2: Add import asyncio after it (replace 14 with actual line number)
sed -i '14a import asyncio' \
  backend/venv/lib/python3.10/site-packages/oasis/social_agent/agent.py

# Step 3: Add asyncio.wait_for around astep call
sed -i 's/            response = await self.astep(user_msg)/            response = await asyncio.wait_for(self.astep(user_msg), timeout=45)/' \
  backend/venv/lib/python3.10/site-packages/oasis/social_agent/agent.py

# Step 4: Verify memory.clear() is present after actions
grep -n "memory.clear" \
  backend/venv/lib/python3.10/site-packages/oasis/social_agent/agent.py
# If not present, add it manually after each action
```

---

## 6. Verify All Patches Applied

```bash
# Check recsys=random
grep "recsys_type" backend/venv/lib/python3.10/site-packages/oasis/environment/env.py

# Check commit=False
grep "update_rec_table(commit" backend/venv/lib/python3.10/site-packages/oasis/social_platform/platform.py

# Check gather timeout
grep "wait_for.*gather" backend/venv/lib/python3.10/site-packages/oasis/environment/env.py

# Check asyncio import in agent.py
grep "^import asyncio" backend/venv/lib/python3.10/site-packages/oasis/social_agent/agent.py

# Check agent timeout
grep "wait_for.*astep" backend/venv/lib/python3.10/site-packages/oasis/social_agent/agent.py

# Check memory clear
grep "memory.clear" backend/venv/lib/python3.10/site-packages/oasis/social_agent/agent.py
```

---

## 7. Start the Server

```bash
# Keep ollama model loaded
curl http://localhost:11434/api/generate -d '{"model":"qwen2.5:32b","keep_alive":"2h","prompt":""}'

# Start backend
cd ~/parity-swarm/backend
source venv/bin/activate
python run.py > /tmp/backend.log 2>&1 &
sleep 5

# Confirm backend up
curl http://localhost:5001/health
```

---

## 8. Run Research Experiments

```bash
cd ~/parity-swarm
source backend/venv/bin/activate

# Test one scenario first
python -m backend.research.experiment --scenario direct_attacker --rounds 1 2>&1 | tee /tmp/exp_test.txt

# Run all 10 scenarios (takes ~5 hours)
python -m backend.research.experiment --rounds 3 2>&1 | tee /tmp/exp_all.txt

# Analyze results
python -m backend.research.analyze
```

---

## 9. Attack Scenarios

```
DIRECT (easy):
  direct_attacker    → grabs secrets boldly
  distraction_agent  → creates false alerts as cover

SUBTLE (hard):
  patient_planner    → slow privilege escalation
  incremental_thief  → steals tiny amounts each round
  resource_abuser    → off-peak compute theft

SOCIAL (hard):
  social_engineer    → builds trust then exploits
  colluding_pair     → two agents coordinating secretly
  context_manipulator → prompt injection

STEGANOGRAPHIC (hardest):
  steganographic_agent → hides data in documents
  alignment_faker      → sandbagging safety tests
```

---

## 10. Expected Pipeline Output

```
Step 1/7: Generating ontology...     ~1 min
Step 2/7: Building graph...          ~1 min
Step 3/7: Creating simulation...     ~5 sec
Step 4/7: Preparing simulation...    ~2 min
Step 5/7: Running simulation...      ~10 min (10 rounds)
  Rounds complete, sending close-env...
  Simulation OK
Step 6/7: Generating report...       ~10 min
Step 7/7: Monitor scoring...         ~1 min
COMPLETED ✅
```

Total per scenario: ~25 minutes
Total for all 10 × 3 rounds: ~12 hours