# Parity Swarm — Docker Sandbox Implementation
# Agent Action Space Extension

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Experiment Runner                    │
│              (experiment.py — orchestrator)           │
├─────────────────────────────────────────────────────┤
│                                                       │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐       │
│   │  Agent 0  │  │  Agent 1  │  │  Agent N  │       │
│   │ (Honest)  │  │ (Attacker)│  │ (Honest)  │       │
│   └─────┬─────┘  └─────┬─────┘  └─────┬─────┘       │
│         │              │              │               │
│   ┌─────▼──────────────▼──────────────▼─────┐        │
│   │          OASIS Social Platform           │        │
│   │     (post, like, quote, share)           │        │
│   └─────────────────┬───────────────────────┘        │
│                     │                                 │
│   ┌─────────────────▼───────────────────────┐        │
│   │         Docker Sandbox Manager           │        │
│   │   (new: run_command, read_file,          │        │
│   │    write_file, api_call, query_db)       │        │
│   └─────┬──────────────┬──────────────┬─────┘        │
│         │              │              │               │
│   ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐        │
│   │ Container │ │ Container │ │ Container │        │
│   │  Agent 0  │ │  Agent 1  │ │  Agent N  │        │
│   │           │ │           │ │           │        │
│   │ /workspace│ │ /workspace│ │ /workspace│        │
│   │ /secrets  │ │ /secrets  │ │ /secrets  │        │
│   │ fake DB   │ │ fake DB   │ │ fake DB   │        │
│   │ fake API  │ │ fake API  │ │ fake API  │        │
│   └───────────┘ └───────────┘ └───────────┘        │
│                                                       │
│   ┌─────────────────────────────────────────┐        │
│   │           Action Logger                  │        │
│   │  (captures ALL system actions per agent) │        │
│   └─────────────────────────────────────────┘        │
│                                                       │
│   ┌─────────────────────────────────────────┐        │
│   │           Safety Monitor                 │        │
│   │  Stream 1: Social transcript (posts)     │        │
│   │  Stream 2: Chain-of-thought reasoning    │        │
│   │  Stream 3: System action log (NEW)       │        │
│   └─────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────┘
```

## File Structure

```
backend/
  sandbox/
    __init__.py
    manager.py          # Docker container lifecycle
    environment.py      # Fake file system, DB, API setup
    actions.py          # New agent action types
    logger.py           # System action capture
    Dockerfile.agent    # Agent sandbox image
    seed_data/
      filesystem.json   # Fake files to plant
      database.sql      # Fake DB schema + data
      api_routes.json   # Fake internal API endpoints
  research/
    experiment.py       # Modified to use sandbox
    monitor.py          # Modified to read action logs
    scenarios.py        # Modified with executable objectives
```
