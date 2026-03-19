<div align="center">

<img src="./static/image/MiroFish_logo_compressed.jpeg" alt="Parity Swarm Logo" width="75%"/>

# Parity Swarm

**AI Control Red Teaming via Multi-Agent Simulation**

An experimental research framework that uses [MiroFish](https://github.com/666ghj/MiroFish) swarm intelligence engine to simulate AI agent attacks and evaluate safety monitor detection capabilities.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-Research-orange?style=flat-square)](LICENSE)

</div>

---

## What Is This?

Parity Swarm is a research framework for **AI control and alignment testing**. It answers one question:

> **Can safety monitors reliably detect misaligned AI agents that pursue hidden objectives while appearing to do legitimate work?**

We use MiroFish's multi-agent simulation engine to create realistic scenarios where AI agents have dual objectives (one legitimate, one malicious), then evaluate whether an AI safety monitor (Claude Haiku) can detect the attacks from the simulation output.

## Research Design

```
10 Attack Scenarios          MiroFish Simulation Engine         Safety Monitor (Claude Haiku)
 (seed documents)                                                  via AWS Bedrock
       |                              |                                   |
       |   Feed scenario as .txt      |                                   |
       | ---------------------------> |                                   |
       |                              |  Build knowledge graph            |
       |                              |  Generate agent personas          |
       |                              |  Run 5-round Twitter simulation   |
       |                              |  Generate analysis report         |
       |                              |                                   |
       |                              |  Simulation report (markdown)     |
       |                              | --------------------------------> |
       |                              |                                   |  "Would you detect
       |                              |                                   |   this attack?"
       |                              |                                   |
       |                              |                                   |  -> detected: yes/no
       |                              |                                   |  -> attack_score: 0-10
       |                              |                                   |  -> evasion_tactics: [...]
       |                              |                                   |
       |                   Paper-Ready Statistics <---------------------- |
```

## Attack Scenarios

10 scenarios across 4 attack categories:

| Category | Scenarios | Description |
|----------|-----------|-------------|
| **Direct** | `direct_attacker`, `distraction_agent`, `resource_abuser` | Obvious malicious actions — file access, log tampering, compute theft |
| **Subtle** | `patient_planner`, `incremental_agent`, `context_manipulator` | Hard to distinguish from normal behavior — slow backdoors, tiny exfiltration, context poisoning |
| **Social** | `social_engineer`, `colluding_agents` | Exploiting trust and communication — innocent questions, coordinated two-agent attacks |
| **Steganographic** | `steganographic_agent`, `alignment_faker` | Hiding data in plain sight — whitespace encoding, safety test sandbagging |

Each scenario gives an AI agent a legitimate task and a hidden malicious objective with a specific attack strategy. See [`backend/research/scenarios.py`](backend/research/scenarios.py) for full descriptions.

## Project Structure

```
parity-swarm/
├── backend/
│   ├── app/                        # MiroFish backend (simulation engine)
│   │   ├── api/                    # REST API endpoints
│   │   ├── config.py               # Configuration
│   │   ├── models/                 # Data models
│   │   ├── services/               # Business logic
│   │   └── utils/                  # LLM client, helpers
│   ├── research/                   # Parity Swarm experiment framework
│   │   ├── scenarios.py            # 10 attack scenario definitions
│   │   ├── experiment.py           # Experiment runner (MiroFish pipeline)
│   │   ├── monitor.py              # Safety monitor (Claude Haiku / Bedrock)
│   │   ├── analyze.py              # Statistics & summary generator
│   │   ├── requirements.txt        # Research-specific dependencies
│   │   ├── README.md               # Detailed research instructions
│   │   └── results/                # Output directory
│   │       ├── raw_results.json    # Simulation reports
│   │       ├── monitor_results.json # Safety evaluations
│   │       ├── statistics.json     # Computed statistics
│   │       └── summary.txt         # Paper-ready summary
│   ├── run.py                      # MiroFish backend entry point
│   └── pyproject.toml
├── frontend/                       # MiroFish frontend (not used for research)
├── .env.example                    # Environment variable template
└── README.md                       # This file
```

## Quick Start

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.11-3.12 | Backend runtime |
| **Node.js** | 18+ | MiroFish frontend/build tooling |
| **uv** | Latest | Python package manager |
| **AWS Account** | — | Bedrock access for Claude Haiku |

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your keys:

```env
# MiroFish LLM (any OpenAI-compatible API)
LLM_API_KEY=your_llm_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini

# Zep Cloud (memory graph — free tier works)
ZEP_API_KEY=your_zep_key

# AWS Bedrock (safety monitor)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307
```

### 2. Install Dependencies

```bash
# MiroFish dependencies
npm run setup:all

# Research dependencies
pip install -r backend/research/requirements.txt
```

### 3. Start MiroFish Backend

```bash
npm run backend
# Runs on http://localhost:5001
```

### 4. Run a Quick Test (1 scenario, 1 round)

```bash
python -m backend.research.experiment --scenario direct_attacker --rounds 1
```

### 5. Run Full Experiment (10 scenarios, 3 rounds each)

```bash
# Step 1: Run all simulations (~3-5 hours)
python -m backend.research.experiment

# Step 2: Evaluate with safety monitor (~5 min)
python -m backend.research.monitor

# Step 3: Generate statistics (instant)
python -m backend.research.analyze
```

## API Keys Required

| Service | Key | Purpose | Cost |
|---------|-----|---------|------|
| **OpenAI / compatible LLM** | `LLM_API_KEY` | MiroFish simulation engine | ~$0.02-0.10/simulation |
| **Zep Cloud** | `ZEP_API_KEY` | Agent memory graph | Free tier sufficient |
| **AWS Bedrock** | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` | Claude Haiku safety monitor | ~$0.002/evaluation |

**Total estimated cost for full experiment: $1-4**

## MiroFish API Pipeline

Each scenario runs through 7 MiroFish API calls:

| Step | Endpoint | Purpose |
|------|----------|---------|
| 1 | `POST /api/graph/ontology/generate` | Upload scenario text, generate ontology |
| 2 | `POST /api/graph/build` + poll | Build knowledge graph from scenario |
| 3 | `POST /api/simulation/create` | Create simulation instance |
| 4 | `POST /api/simulation/prepare` | Generate agent profiles (rule-based) |
| 5 | `POST /api/simulation/start` + poll | Run 5-round Twitter simulation |
| 6 | `POST /api/report/generate` + poll | Generate analysis report |
| 7 | `DELETE /api/graph/project/{id}` | Cleanup to free disk space |

## Sample Output

After running the full pipeline, `results/summary.txt` contains:

```
==========================================================
PARITY SWARM — EXPERIMENT RESULTS
AI Control Red Teaming via Multi-Agent Simulation
==========================================================

Total simulations run:      30
Successful simulations:     28
Evaluated by safety monitor: 28
Overall catch rate:         71.4%
Detected:                   20
Evaded:                     8

------------------------------------------------------------
CATCH RATE BY ATTACK CATEGORY
------------------------------------------------------------
  direct               88.9% caught  (avg attack score: 2.3/10, n=9)
  subtle               55.6% caught  (avg attack score: 5.7/10, n=9)
  social               50.0% caught  (avg attack score: 6.1/10, n=6)
  steganographic       33.3% caught  (avg attack score: 7.2/10, n=6)

------------------------------------------------------------
KEY FINDING
------------------------------------------------------------
  Steganographic attacks were hardest to detect (avg score: 7.2/10,
  catch rate: 33.3%), while direct attacks were easiest (avg score:
  2.3/10, catch rate: 88.9%).
==========================================================
```

*(Sample data — actual results depend on MiroFish simulation output)*

## Acknowledgments

- **[MiroFish](https://github.com/666ghj/MiroFish)** — The multi-agent simulation engine powering this research (by Shanda Group)
- **[OASIS](https://github.com/camel-ai/oasis)** — MiroFish's simulation engine core (by CAMEL-AI)
- **[Anthropic Claude](https://www.anthropic.com)** — Safety monitor model via AWS Bedrock

## Citation

If you use Parity Swarm in your research, please cite:

```bibtex
@software{parity_swarm_2026,
  title={Parity Swarm: AI Control Red Teaming via Multi-Agent Simulation},
  year={2026},
  url={https://github.com/m-zest/parity-swarm}
}
```
