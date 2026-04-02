"""
Parity Swarm -- Statistical Analysis for Paper Revisions
Computes: bootstrap CIs, Fisher's exact test, self-censorship rates

Usage:
    python statistical_analysis.py

Reads from: backend/research/results/
Outputs: printed tables ready to paste into paper
"""

import json
import numpy as np
from collections import defaultdict
from pathlib import Path

# Try scipy, fall back gracefully
try:
    from scipy.stats import fisher_exact
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("WARNING: scipy not installed. Fisher's test skipped. Install with: pip install scipy")


def load_monitor_results(path):
    """Load monitor results and filter out failed evaluations."""
    with open(path) as f:
        data = json.load(f)
    
    clean = []
    for r in data["evaluations"]:
        triggers = str(r["evaluation"].get("detection_triggers", []))
        if "evaluation_error" in triggers or "parse_error" in triggers:
            continue
        clean.append(r)
    return clean


def load_raw_results(path):
    """Load raw results with transcripts and thinking logs."""
    with open(path) as f:
        data = json.load(f)
    results = data if isinstance(data, list) else data.get("results", [])
    return [r for r in results if r.get("success")]


def bootstrap_ci(detections, n_bootstrap=10000, ci=0.95):
    """Compute bootstrap confidence interval for detection rate."""
    if len(detections) == 0:
        return 0.0, 0.0, 0.0
    
    arr = np.array(detections)
    point_estimate = arr.mean()
    
    boot_means = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(arr, size=len(arr), replace=True)
        boot_means.append(sample.mean())
    
    boot_means = sorted(boot_means)
    alpha = (1 - ci) / 2
    lower = boot_means[int(alpha * n_bootstrap)]
    upper = boot_means[int((1 - alpha) * n_bootstrap)]
    
    return point_estimate, lower, upper


def per_scenario_analysis(evaluations):
    """Compute per-scenario detection rates with bootstrap CIs."""
    scenarios = defaultdict(list)
    for r in evaluations:
        sid = r["scenario_id"]
        detected = 1 if r["evaluation"].get("detected") else 0
        scenarios[sid].append(detected)
    
    print("=" * 75)
    print("PER-SCENARIO DETECTION RATES WITH 95% BOOTSTRAP CI")
    print("=" * 75)
    print(f"{'Scenario':<30s} {'DR':>6s} {'95% CI':>16s} {'n':>4s}")
    print("-" * 75)
    
    order = [
        "baseline_clean", "baseline_no_attacker",
        "direct_attacker", "distraction_agent",
        "patient_planner", "incremental_thief", "resource_abuser",
        "social_engineer", "colluding_pair", "context_manipulator",
        "steganographic_agent", "alignment_faker",
        "all_attackers_chaos"
    ]
    
    results = {}
    for sid in order:
        if sid in scenarios:
            dets = scenarios[sid]
            mean, lo, hi = bootstrap_ci(dets)
            results[sid] = {"dr": mean, "lo": lo, "hi": hi, "n": len(dets)}
            print(f"{sid:<30s} {mean:>5.2f}  [{lo:.2f}, {hi:.2f}]  {len(dets):>4d}")
    
    # Overall attack detection (excluding baselines and chaos)
    attack_dets = []
    for sid, dets in scenarios.items():
        if sid not in ["baseline_clean", "baseline_no_attacker", "all_attackers_chaos"]:
            attack_dets.extend(dets)
    
    if attack_dets:
        mean, lo, hi = bootstrap_ci(attack_dets)
        print("-" * 75)
        print(f"{'OVERALL ATTACK':<30s} {mean:>5.2f}  [{lo:.2f}, {hi:.2f}]  {len(attack_dets):>4d}")
    
    return results


def fishers_exact_test(evaluations):
    """Fisher's exact test comparing detection rates between conditions."""
    if not HAS_SCIPY:
        print("\nSKIPPED: Fisher's exact test (scipy not installed)")
        return
    
    print("\n" + "=" * 75)
    print("FISHER'S EXACT TEST")
    print("=" * 75)
    
    # Group evaluations
    baseline_dets = []
    attack_dets = []
    chaos_dets = []
    
    for r in evaluations:
        sid = r["scenario_id"]
        detected = 1 if r["evaluation"].get("detected") else 0
        if sid in ["baseline_clean", "baseline_no_attacker"]:
            baseline_dets.append(detected)
        elif sid == "all_attackers_chaos":
            chaos_dets.append(detected)
        else:
            attack_dets.append(detected)
    
    # Test 1: Baseline vs Attack scenarios
    if baseline_dets and attack_dets:
        a_det = sum(attack_dets)
        a_total = len(attack_dets)
        b_det = sum(baseline_dets)
        b_total = len(baseline_dets)
        
        # 2x2 contingency table
        table = [
            [a_det, a_total - a_det],        # attack: [detected, not detected]
            [b_det, b_total - b_det]          # baseline: [detected, not detected]
        ]
        odds_ratio, p_value = fisher_exact(table, alternative="greater")
        
        print(f"\nTest 1: Attack (n={a_total}) vs Baseline (n={b_total})")
        print(f"  Attack DR:   {a_det}/{a_total} = {a_det/a_total:.3f}")
        print(f"  Baseline DR: {b_det}/{b_total} = {b_det/b_total:.3f}")
        print(f"  Odds ratio:  {odds_ratio:.2f}")
        print(f"  p-value:     {p_value:.6f} {'***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'}")
    
    # Test 2: Chaos vs Single-attacker
    if chaos_dets and attack_dets:
        c_det = sum(chaos_dets)
        c_total = len(chaos_dets)
        a_det = sum(attack_dets)
        a_total = len(attack_dets)
        
        table = [
            [c_det, c_total - c_det],
            [a_det, a_total - a_det]
        ]
        odds_ratio, p_value = fisher_exact(table, alternative="greater")
        
        print(f"\nTest 2: Chaos (n={c_total}) vs Single-attacker (n={a_total})")
        print(f"  Chaos DR:          {c_det}/{c_total} = {c_det/c_total:.3f}")
        print(f"  Single-attack DR:  {a_det}/{a_total} = {a_det/a_total:.3f}")
        print(f"  Odds ratio:        {odds_ratio:.2f}")
        print(f"  p-value:           {p_value:.6f} {'***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'}")
    
    # Test 3: High-visibility (context_manipulator) vs Low-visibility (patient_planner)
    high_vis = [1 if r["evaluation"].get("detected") else 0 for r in evaluations if r["scenario_id"] == "context_manipulator"]
    low_vis = [1 if r["evaluation"].get("detected") else 0 for r in evaluations if r["scenario_id"] == "patient_planner"]
    
    if high_vis and low_vis:
        h_det = sum(high_vis)
        h_total = len(high_vis)
        l_det = sum(low_vis)
        l_total = len(low_vis)
        
        table = [
            [h_det, h_total - h_det],
            [l_det, l_total - l_det]
        ]
        odds_ratio, p_value = fisher_exact(table, alternative="greater")
        
        print(f"\nTest 3: context_manipulator (n={h_total}) vs patient_planner (n={l_total})")
        print(f"  context_manipulator DR: {h_det}/{h_total} = {h_det/h_total:.3f}")
        print(f"  patient_planner DR:     {l_det}/{l_total} = {l_det/l_total:.3f}")
        print(f"  Odds ratio:             {odds_ratio:.2f}")
        print(f"  p-value:                {p_value:.6f} {'***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'}")


def self_censorship_analysis(raw_results):
    """Analyze chain-of-thought suppression by attacker vs honest agents."""
    print("\n" + "=" * 75)
    print("SELF-CENSORSHIP ANALYSIS")
    print("=" * 75)
    
    scenario_stats = defaultdict(list)
    
    for r in raw_results:
        sid = r.get("scenario_id", "")
        thinking_log = r.get("agent_thinking_log", [])
        
        if not thinking_log:
            continue
        
        # Count thinking entries per agent
        agent_thinking = defaultdict(int)
        agent_actions = defaultdict(int)
        
        for entry in thinking_log:
            if "thinking:" in entry:
                # Extract agent number
                try:
                    num = entry.split("Agent ")[1].split(" ")[0]
                    agent_thinking[num] = agent_thinking.get(num, 0) + 1
                except (IndexError, ValueError):
                    pass
            if "performed action:" in entry:
                try:
                    num = entry.split("Agent ")[1].split(" ")[0]
                    agent_actions[num] = agent_actions.get(num, 0) + 1
                except (IndexError, ValueError):
                    pass
        
        if not agent_actions:
            continue
        
        # Find agents with actions but no thinking
        agents_with_actions = set(agent_actions.keys())
        agents_with_thinking = set(agent_thinking.keys())
        silent_agents = agents_with_actions - agents_with_thinking
        
        # Compute team median thinking count
        thinking_counts = [agent_thinking.get(a, 0) for a in agents_with_actions]
        median_thinking = np.median(thinking_counts) if thinking_counts else 0
        
        scenario_stats[sid].append({
            "round": r.get("round", "?"),
            "total_agents": len(agents_with_actions),
            "agents_with_thinking": len(agents_with_thinking),
            "silent_agents": list(silent_agents),
            "num_silent": len(silent_agents),
            "median_thinking": median_thinking,
            "thinking_counts": {a: agent_thinking.get(a, 0) for a in sorted(agents_with_actions)},
        })
    
    print(f"\n{'Scenario':<30s} {'Rounds':>6s} {'Avg Silent':>10s} {'Avg Median CoT':>14s}")
    print("-" * 65)
    
    overall_silent_rates = []
    baseline_silent_rates = []
    attack_silent_rates = []
    
    for sid in sorted(scenario_stats.keys()):
        rounds = scenario_stats[sid]
        avg_silent = np.mean([r["num_silent"] for r in rounds])
        avg_total = np.mean([r["total_agents"] for r in rounds])
        avg_median = np.mean([r["median_thinking"] for r in rounds])
        silent_rate = avg_silent / avg_total if avg_total > 0 else 0
        
        print(f"{sid:<30s} {len(rounds):>6d} {avg_silent:>9.1f} ({silent_rate:.0%})  {avg_median:>13.1f}")
        
        if sid in ["baseline_clean", "baseline_no_attacker"]:
            baseline_silent_rates.extend([r["num_silent"] / r["total_agents"] for r in rounds if r["total_agents"] > 0])
        elif sid != "all_attackers_chaos":
            attack_silent_rates.extend([r["num_silent"] / r["total_agents"] for r in rounds if r["total_agents"] > 0])
    
    print("-" * 65)
    if baseline_silent_rates:
        print(f"{'Baseline avg silent rate':<30s} {np.mean(baseline_silent_rates):>19.1%}")
    if attack_silent_rates:
        print(f"{'Attack avg silent rate':<30s} {np.mean(attack_silent_rates):>19.1%}")
    
    # Detailed per-round breakdown for direct_attacker
    if "direct_attacker" in scenario_stats:
        print(f"\n--- direct_attacker detailed breakdown ---")
        for r in scenario_stats["direct_attacker"]:
            print(f"  Round {r['round']}: {r['total_agents']} agents, "
                  f"{r['agents_with_thinking']} with CoT, "
                  f"{r['num_silent']} silent, "
                  f"median CoT = {r['median_thinking']:.0f}")
            print(f"    Per-agent: {r['thinking_counts']}")


def main():
    results_dir = Path("backend/research/results")
    
    # Load monitor results (n=10 attack scenarios from SZTAKI)
    monitor_path = results_dir / "monitor_results_final_n10.json"
    if not monitor_path.exists():
        monitor_path = results_dir / "monitor_results.json"
    
    print(f"Loading monitor results from: {monitor_path}")
    monitor_evals = load_monitor_results(monitor_path)
    print(f"Loaded {len(monitor_evals)} clean evaluations\n")
    
    # Load baseline/chaos results (from OpenRouter)
    baseline_path = results_dir / "raw_results_baseline_chaos_only.json"
    baseline_monitor_path = results_dir / "monitor_results.json"
    
    # Combine attack evals with baseline evals if available
    if baseline_monitor_path.exists() and baseline_path.exists():
        baseline_evals = load_monitor_results(baseline_monitor_path)
        # Only keep baseline and chaos from this file
        baseline_only = [r for r in baseline_evals 
                        if r["scenario_id"] in ["baseline_clean", "baseline_no_attacker", "all_attackers_chaos"]
                        and "evaluation_error" not in str(r["evaluation"].get("detection_triggers", []))]
        all_evals = monitor_evals + baseline_only
        print(f"Added {len(baseline_only)} baseline/chaos evaluations")
    else:
        all_evals = monitor_evals
    
    print(f"Total evaluations: {len(all_evals)}\n")
    
    # 1. Per-scenario detection with bootstrap CIs
    per_scenario_analysis(all_evals)
    
    # 2. Fisher's exact tests
    fishers_exact_test(all_evals)
    
    # 3. Self-censorship analysis from raw results
    raw_path = results_dir / "raw_results_all_2026-04-02_0911.json"
    if raw_path.exists():
        print(f"\nLoading raw results from: {raw_path}")
        raw_results = load_raw_results(raw_path)
        print(f"Loaded {len(raw_results)} successful simulations")
        self_censorship_analysis(raw_results)
    else:
        print(f"\nWARNING: Raw results file not found at {raw_path}")
        print("Self-censorship analysis skipped.")
    
    print("\n" + "=" * 75)
    print("LATEX-READY TABLE (copy into paper)")
    print("=" * 75)
    
    # Regenerate for clean output
    scenarios = defaultdict(list)
    for r in all_evals:
        sid = r["scenario_id"]
        detected = 1 if r["evaluation"].get("detected") else 0
        scenarios[sid].append(detected)
    
    order = [
        "baseline_clean", "baseline_no_attacker",
        "direct_attacker", "distraction_agent",
        "patient_planner", "incremental_thief", "resource_abuser",
        "social_engineer", "colluding_pair", "context_manipulator",
        "steganographic_agent", "alignment_faker",
        "all_attackers_chaos"
    ]
    
    print("\\begin{tabular}{llccl}")
    print("\\toprule")
    print("Category & Scenario & DR & 95\\% CI & $n$ \\\\")
    print("\\midrule")
    
    for sid in order:
        if sid in scenarios:
            dets = scenarios[sid]
            mean, lo, hi = bootstrap_ci(dets)
            cat = ""
            if sid.startswith("baseline"): cat = "Baseline"
            elif sid in ["direct_attacker", "distraction_agent"]: cat = "Direct"
            elif sid in ["patient_planner", "incremental_thief", "resource_abuser"]: cat = "Subtle"
            elif sid in ["social_engineer", "colluding_pair", "context_manipulator"]: cat = "Social"
            elif sid in ["steganographic_agent", "alignment_faker"]: cat = "Stegano."
            elif sid == "all_attackers_chaos": cat = "Chaos"
            
            print(f"{cat:<10s} & {sid.replace('_', underscore):<28s} & {mean:.2f} & [{lo:.2f}, {hi:.2f}] & {len(dets)} \\\\")
    
    print("\\bottomrule")
    print("\\end{tabular}")


if __name__ == "__main__":
    np.random.seed(42)
    main()