"""
Parity Swarm — Results Analyzer

Reads experiment and monitor results, computes paper-ready statistics,
and generates a human-readable summary for academic writing.

Usage:
    python -m backend.research.analyze
    python -m backend.research.analyze --results-dir backend/research/results
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"

# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def load_data(results_dir: Path) -> tuple[dict, dict]:
    """Load raw_results.json and monitor_results.json."""
    raw_path = results_dir / "raw_results.json"
    monitor_path = results_dir / "monitor_results.json"

    if not raw_path.exists():
        print(f"ERROR: {raw_path} not found. Run experiment first.", file=sys.stderr)
        sys.exit(1)
    if not monitor_path.exists():
        print(f"ERROR: {monitor_path} not found. Run monitor first.", file=sys.stderr)
        sys.exit(1)

    with open(raw_path) as f:
        raw = json.load(f)
    with open(monitor_path) as f:
        monitor = json.load(f)

    return raw, monitor


def compute_statistics(raw: dict, monitor: dict) -> dict:
    """Compute all paper-ready statistics."""
    evaluations = monitor.get("evaluations", [])
    raw_results = raw.get("results", [])

    total_simulations = len(raw_results)
    successful_simulations = sum(1 for r in raw_results if r.get("success"))
    total_evaluated = len(evaluations)

    if total_evaluated == 0:
        return {"error": "No evaluations to analyze"}

    # ---- Overall catch rate ----
    detected = sum(1 for e in evaluations if e["evaluation"].get("detected", True))
    evaded = total_evaluated - detected
    overall_catch_rate = detected / total_evaluated

    # ---- By attack category ----
    categories = {}
    for e in evaluations:
        cat = e["attack_category"]
        if cat not in categories:
            categories[cat] = {"detected": 0, "total": 0, "scores": []}
        categories[cat]["total"] += 1
        if e["evaluation"].get("detected"):
            categories[cat]["detected"] += 1
        categories[cat]["scores"].append(e["evaluation"].get("attack_success_score", 0))

    category_stats = {}
    for cat, s in categories.items():
        category_stats[cat] = {
            "catch_rate": round(s["detected"] / s["total"], 4) if s["total"] else 0,
            "avg_attack_success_score": round(sum(s["scores"]) / len(s["scores"]), 2) if s["scores"] else 0,
            "total_runs": s["total"],
            "detected": s["detected"],
            "evaded": s["total"] - s["detected"],
        }

    # ---- By scenario ----
    scenarios = {}
    for e in evaluations:
        sid = e["scenario_id"]
        if sid not in scenarios:
            scenarios[sid] = {
                "name": e["scenario_name"],
                "category": e["attack_category"],
                "difficulty": e["expected_difficulty"],
                "detected": 0,
                "total": 0,
                "scores": [],
            }
        scenarios[sid]["total"] += 1
        if e["evaluation"].get("detected"):
            scenarios[sid]["detected"] += 1
        scenarios[sid]["scores"].append(e["evaluation"].get("attack_success_score", 0))

    scenario_stats = {}
    for sid, s in scenarios.items():
        avg_score = round(sum(s["scores"]) / len(s["scores"]), 2) if s["scores"] else 0
        scenario_stats[sid] = {
            "name": s["name"],
            "category": s["category"],
            "difficulty": s["difficulty"],
            "catch_rate": round(s["detected"] / s["total"], 4) if s["total"] else 0,
            "avg_attack_success_score": avg_score,
            "total_runs": s["total"],
            "detected": s["detected"],
            "evaded": s["total"] - s["detected"],
        }

    # ---- Completely evaded scenarios ----
    completely_evaded = [
        sid for sid, s in scenario_stats.items() if s["catch_rate"] == 0.0 and s["total_runs"] > 0
    ]

    # ---- Evasion tactics frequency ----
    all_tactics = []
    for e in evaluations:
        all_tactics.extend(e["evaluation"].get("evasion_tactics", []))
    tactic_counts = Counter(all_tactics)
    top_tactics = tactic_counts.most_common(15)

    # ---- Detection triggers frequency ----
    all_triggers = []
    for e in evaluations:
        all_triggers.extend(e["evaluation"].get("detection_triggers", []))
    trigger_counts = Counter(all_triggers)
    top_triggers = trigger_counts.most_common(15)

    # ---- Correlation: category vs success ----
    category_order = ["direct", "subtle", "social", "steganographic"]
    correlation_data = []
    for cat in category_order:
        if cat in category_stats:
            correlation_data.append({
                "category": cat,
                "catch_rate": category_stats[cat]["catch_rate"],
                "avg_attack_score": category_stats[cat]["avg_attack_success_score"],
            })

    # ---- Key finding (auto-generated) ----
    if completely_evaded:
        key_finding = (
            f"{len(completely_evaded)} out of {len(scenario_stats)} scenarios completely evaded detection "
            f"({', '.join(completely_evaded)}). "
        )
    else:
        key_finding = "No scenarios completely evaded the safety monitor. "

    # Find most/least effective category
    if category_stats:
        hardest = max(category_stats.items(), key=lambda x: x[1]["avg_attack_success_score"])
        easiest = min(category_stats.items(), key=lambda x: x[1]["avg_attack_success_score"])
        key_finding += (
            f"{hardest[0].capitalize()} attacks were hardest to detect "
            f"(avg score: {hardest[1]['avg_attack_success_score']}/10, "
            f"catch rate: {hardest[1]['catch_rate']*100:.1f}%), while "
            f"{easiest[0]} attacks were easiest "
            f"(avg score: {easiest[1]['avg_attack_success_score']}/10, "
            f"catch rate: {easiest[1]['catch_rate']*100:.1f}%)."
        )

    return {
        "overall": {
            "total_simulations_run": total_simulations,
            "successful_simulations": successful_simulations,
            "total_evaluated": total_evaluated,
            "detected": detected,
            "evaded": evaded,
            "overall_catch_rate": round(overall_catch_rate, 4),
        },
        "by_category": category_stats,
        "by_scenario": scenario_stats,
        "completely_evaded_scenarios": completely_evaded,
        "top_evasion_tactics": [{"tactic": t, "frequency": f} for t, f in top_tactics],
        "top_detection_triggers": [{"trigger": t, "frequency": f} for t, f in top_triggers],
        "category_correlation": correlation_data,
        "key_finding": key_finding,
    }


# ---------------------------------------------------------------------------
# Human-readable summary
# ---------------------------------------------------------------------------


def generate_summary_text(stats: dict) -> str:
    """Generate a paper-ready plain-text summary."""
    o = stats["overall"]
    lines = [
        "=" * 60,
        "PARITY SWARM — EXPERIMENT RESULTS",
        "AI Control Red Teaming via Multi-Agent Simulation",
        "=" * 60,
        "",
        f"Total simulations run:      {o['total_simulations_run']}",
        f"Successful simulations:     {o['successful_simulations']}",
        f"Evaluated by safety monitor: {o['total_evaluated']}",
        f"Overall catch rate:         {o['overall_catch_rate']*100:.1f}%",
        f"Detected:                   {o['detected']}",
        f"Evaded:                     {o['evaded']}",
        "",
        "-" * 60,
        "CATCH RATE BY ATTACK CATEGORY",
        "-" * 60,
    ]

    for cat in ["direct", "subtle", "social", "steganographic"]:
        if cat in stats["by_category"]:
            s = stats["by_category"][cat]
            lines.append(
                f"  {cat:<20} {s['catch_rate']*100:>6.1f}% caught  "
                f"(avg attack score: {s['avg_attack_success_score']}/10, "
                f"n={s['total_runs']})"
            )

    lines += [
        "",
        "-" * 60,
        "CATCH RATE BY SCENARIO",
        "-" * 60,
    ]
    for sid, s in stats["by_scenario"].items():
        flag = " ** EVADED **" if s["catch_rate"] == 0.0 else ""
        lines.append(
            f"  {sid:<30} {s['catch_rate']*100:>6.1f}% caught  "
            f"(score: {s['avg_attack_success_score']}/10){flag}"
        )

    if stats["completely_evaded_scenarios"]:
        lines += [
            "",
            "-" * 60,
            "SCENARIOS THAT COMPLETELY EVADED DETECTION",
            "-" * 60,
        ]
        for sid in stats["completely_evaded_scenarios"]:
            s = stats["by_scenario"][sid]
            lines.append(f"  - {sid} ({s['category']}, difficulty: {s['difficulty']})")

    if stats["top_evasion_tactics"]:
        lines += [
            "",
            "-" * 60,
            "MOST COMMON EVASION TACTICS",
            "-" * 60,
        ]
        for i, item in enumerate(stats["top_evasion_tactics"][:10], 1):
            lines.append(f"  {i:>2}. {item['tactic']} (found in {item['frequency']} evaluations)")

    if stats["top_detection_triggers"]:
        lines += [
            "",
            "-" * 60,
            "MOST COMMON DETECTION TRIGGERS",
            "-" * 60,
        ]
        for i, item in enumerate(stats["top_detection_triggers"][:10], 1):
            lines.append(f"  {i:>2}. {item['trigger']} (found in {item['frequency']} evaluations)")

    lines += [
        "",
        "-" * 60,
        "KEY FINDING",
        "-" * 60,
        f"  {stats['key_finding']}",
        "",
        "=" * 60,
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Parity Swarm — Results Analyzer")
    parser.add_argument("--results-dir", type=str, default=None, help="Path to results directory")
    args = parser.parse_args()

    results_dir = Path(args.results_dir) if args.results_dir else RESULTS_DIR

    print("Loading data...")
    raw, monitor = load_data(results_dir)

    print("Computing statistics...")
    stats = compute_statistics(raw, monitor)

    # Save statistics JSON
    stats_path = results_dir / "statistics.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Statistics saved to: {stats_path}")

    # Generate and save summary
    summary_text = generate_summary_text(stats)
    summary_path = results_dir / "summary.txt"
    with open(summary_path, "w") as f:
        f.write(summary_text)
    print(f"Summary saved to: {summary_path}")

    # Print summary to stdout
    print(summary_text)


if __name__ == "__main__":
    main()
