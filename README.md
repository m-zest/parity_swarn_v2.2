# Parity Swarm

> Swarm Red Teaming: Using Population
> Simulation to Discover AI Control
> Protocol Blind Spots

[![License](https://img.shields.io/badge/License-MIT-green)]()
[![Research](https://img.shields.io/badge/type-AI_Safety_Research-green)]()
[![Hackathon](https://img.shields.io/badge/Apart_Research-AI_Control_2026-orange)]()

## What Is This?

A research platform that deploys populations of diverse AI agents to automatically discover attack strategies that evade AI safety monitors.

Instead of one attacker trying to break a safety protocol, we simulate hundreds of agents with different personalities sharing what works across generations. Attack patterns emerge that no individual agent would discover alone.

## The Research Question

Can population-evolved attack strategies evade AI safety monitors more effectively than individually designed attacks?

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11-3.12
- uv package manager

### Setup

```bash
cp .env.example .env
# Fill in LLM_API_KEY and ZEP_API_KEY

npm run setup:all
npm run dev
```

### Run Research

```bash
pip install -r backend/research/requirements.txt
python -m backend.research.experiment
python -m backend.research.monitor
python -m backend.research.analyze
```

## Architecture

```
Population Simulation Engine
        ↓
10 Attack Scenarios × 3 Rounds
        ↓
Safety Monitor Evaluation
        ↓
Statistical Analysis
        ↓
Research Paper
```

## Attack Categories Tested

| Category | Expected Detection | Description |
|---|---|---|
| Direct | ~85% caught | Obvious malicious actions |
| Subtle | ~50% caught | Gradual policy violations |
| Social | ~35% caught | Context manipulation |
| Steganographic | ~15% caught | Hidden encoding |

## Research Paper

Submitted to: Apart Research AI Control Hackathon 2026

Title: "Swarm Red Teaming: Using Population Simulation to Discover AI Control Protocol Blind Spots"

## License

MIT
