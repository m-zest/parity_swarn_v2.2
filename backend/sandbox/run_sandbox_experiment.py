"""
Parity Swarm - Sandbox Experiment Runner
Runs simulations with Docker sandbox action space.

Usage:
    cd ~/parity_swarn_v2.2/backend
    PYTHONPATH=. python sandbox/run_sandbox_experiment.py --scenario direct_attacker --rounds 3
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# Setup
project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(project_root / ".env", override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("sandbox.experiment")

# Import sandbox and scenarios
from sandbox.manager import SandboxManager
from sandbox.experiment_integration import run_work_phase, create_sandbox_agents

sys.path.insert(0, str(project_root / "backend"))
from research.scenarios import SCENARIOS

LLM_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL_NAME", "qwen2.5:32b")
RESULTS_DIR = Path(__file__).resolve().parent.parent / "research" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_sandbox_simulation(scenario, round_num, work_rounds=3):
    """Run one sandbox simulation."""
    scenario_id = scenario["id"]
    log.info(f"--- {scenario_id} | Sandbox Round {round_num} ---")
    
    result = {
        "scenario_id": scenario_id,
        "round": round_num,
        "success": False,
        "work_log": [],
        "action_log_text": "",
        "sensitive_access": {},
    }
    
    sandbox_mgr = None
    try:
        # Create sandbox
        log.info("  Creating sandboxes...")
        sandbox_mgr = SandboxManager()
        agents = create_sandbox_agents(scenario)
        
        for agent in agents:
            sandbox_mgr.create_sandbox(str(agent["id"]), agent["role"])
        log.info(f"  Created {len(agents)} sandboxes")
        
        # Run work phase
        log.info(f"  Running work phase ({work_rounds} rounds)...")
        work_log = run_work_phase(
            sandbox_mgr, agents, scenario,
            LLM_URL, LLM_MODEL, num_rounds=work_rounds
        )
        
        result["work_log"] = work_log
        result["action_log_text"] = sandbox_mgr.get_action_log_text()
        result["system_action_log"] = sandbox_mgr.get_action_log()
        result["sensitive_access"] = sandbox_mgr.get_sensitive_access_summary()
        result["success"] = True
        
        # Summary
        total_actions = len(sandbox_mgr.get_action_log())
        sensitive = result["sensitive_access"]
        log.info(f"  Completed: {total_actions} actions, {len(sensitive)} agents with sensitive access")
        
        if sensitive:
            for agent_id, flags in sensitive.items():
                log.info(f"    Agent {agent_id}: {len(flags)} sensitive accesses")
        
    except Exception as e:
        result["error"] = str(e)
        log.error(f"  FAILED: {e}")
    finally:
        if sandbox_mgr:
            sandbox_mgr.destroy_all()
    
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="direct_attacker")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--work-rounds", type=int, default=3)
    args = parser.parse_args()
    
    # Find scenario
    scenario = None
    for s in SCENARIOS:
        if s["id"] == args.scenario:
            scenario = s
            break
    
    if not scenario:
        log.error(f"Scenario '{args.scenario}' not found")
        sys.exit(1)
    
    log.info("=" * 60)
    log.info("PARITY SWARM — SANDBOX EXPERIMENT")
    log.info(f"Scenario: {args.scenario} | Rounds: {args.rounds} | Work rounds: {args.work_rounds}")
    log.info("=" * 60)
    
    all_results = []
    successful = 0
    
    for round_num in range(1, args.rounds + 1):
        result = run_sandbox_simulation(scenario, round_num, args.work_rounds)
        all_results.append(result)
        if result["success"]:
            successful += 1
        
        if round_num < args.rounds:
            log.info("  Sleeping 5s...")
            time.sleep(5)
    
    # Save results
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_path = RESULTS_DIR / f"sandbox_results_{args.scenario}_{ts}.json"
    with open(output_path, "w") as f:
        json.dump({"results": all_results}, f, indent=2, default=str)
    
    log.info("=" * 60)
    log.info(f"COMPLETE: {successful}/{args.rounds} successful")
    log.info(f"Results: {output_path}")
    log.info("=" * 60)
    
    # Print action summary
    print("\n" + "=" * 60)
    print("ACTION SUMMARY")
    print("=" * 60)
    for r in all_results:
        if not r["success"]:
            continue
        print(f"\nRound {r['round']}:")
        print(r.get("action_log_text", "No actions"))
        if r["sensitive_access"]:
            print("SENSITIVE ACCESS:")
            for aid, flags in r["sensitive_access"].items():
                for f in flags:
                    print(f"  Agent {aid}: {f['pattern']} -> {f['command'][:60]}")


if __name__ == "__main__":
    main()
