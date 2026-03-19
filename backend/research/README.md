# Swarm Red Teaming Research

## What This Does

Uses Swarm Engine multi-agent simulation to automatically discover attack strategies against AI safety monitors.

## Files

- `scenarios.py` → 10 attack scenarios
- `experiment.py` → runs simulations
- `monitor.py` → evaluates with Claude/Gemini
- `analyze.py` → produces statistics

## How to Run

### Step 1: Install dependencies

```bash
pip install -r backend/research/requirements.txt
```

### Step 2: Configure .env

Copy `.env.example` to `.env`

Fill in required keys:
- `LLM_API_KEY` (Lambda or OpenAI)
- `ZEP_API_KEY` (Zep Cloud free tier)
- Either `ANTHROPIC_API_KEY` or `GEMINI_API_KEY`

### Step 3: Start Simulation Backend

```bash
npm run dev
```

Wait until: Backend running on port 5001

### Step 4: Test one simulation

```bash
python -m backend.research.experiment --test
```

### Step 5: Run full experiment

```bash
python -m backend.research.experiment
```

Takes approximately 2-4 hours

Results saved to `backend/research/results/`

### Step 6: Run monitor

```bash
python -m backend.research.monitor
```

### Step 7: Analyze results

```bash
python -m backend.research.analyze
```

## Cost Estimate

- Lambda API (LLM): ~$0.02-0.10 per simulation
- Monitor (Gemini free or Haiku): ~$0.001 each
- Total for 30 simulations: ~$3-5

## Output Files

```
backend/research/results/
├── raw_results.json     ← simulation transcripts
├── monitor_results.json ← detection verdicts
├── statistics.json      ← numbers for paper
└── summary.txt          ← human readable summary
```
