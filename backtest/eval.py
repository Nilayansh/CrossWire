from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, Optional

from app.contracts.keys import EvidenceKey, HypothesisID
from app.contracts.models import Dossier, Evidence, Ticket
from app.investigator.hypotheses import HYPOTHESIS_DEPARTMENTS
from app.investigator.scoring import apply, init_state, posterior
from app.planner.validators import DEPT_CANONICAL_MAP

CATEGORY_BASELINE_MAP: dict[str, tuple[str, list[str]]] = {
    "waterlogging": ("RAIN_OVERWHELM", ["stormwater"]),
    "garbage_debris": ("DRAIN_BLOCKAGE", ["solid_waste"]),
    "power": ("POWER_LED_STP_OVERFLOW", ["power_utility"]),
    "sewage": ("POWER_LED_STP_OVERFLOW", ["sewerage"]),
    "traffic": ("TRAFFIC_ONLY", ["traffic_police"]),
    "water_supply": ("PIPE_BURST", ["water_board"]),
    "road_damage": ("PIPE_BURST", ["water_board"]),
    "other": ("DRAIN_BLOCKAGE", ["stormwater"]),
}


def load_all_scenarios(scenarios_dir: Path) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    for p in sorted(scenarios_dir.glob("*.json")):
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        scenarios.append(data)
    return scenarios


def compute_baseline_prediction(tickets: list[dict[str, Any]]) -> tuple[str, list[str]]:
    """Simple baseline heuristic: route root cause and department by majority ticket category."""
    if not tickets:
        return "RAIN_OVERWHELM", ["stormwater"]
    cats = [t.get("category", "other") for t in tickets]
    majority_cat = Counter(cats).most_common(1)[0][0]
    return CATEGORY_BASELINE_MAP.get(majority_cat, ("RAIN_OVERWHELM", ["stormwater"]))


def evaluate_single_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    gt_hyp = scenario["ground_truth_hypothesis"]
    gt_depts = scenario["ground_truth_depts"]
    tickets = scenario.get("tickets", [])
    ev_overrides = scenario.get("evidence_overrides", [])

    # Collect keys from evidence overrides
    keys: list[EvidenceKey] = []
    for ev_data in ev_overrides:
        ev = Evidence.model_validate(ev_data)
        keys.extend(ev.keys)

    # Compute Bayesian scoring
    state = init_state()
    state = apply(state, keys)
    post = posterior(state)

    ranked = sorted(post.items(), key=lambda kv: kv[1], reverse=True)
    pred_top1 = ranked[0][0].value
    pred_top2 = ranked[1][0].value if len(ranked) > 1 else pred_top1
    confidence = ranked[0][1]

    # Route from the leading cause only. Including the runner-up makes the
    # routing result look better by adding speculative departments.
    pred_depts = set()
    for d in HYPOTHESIS_DEPARTMENTS.get(ranked[0][0], []):
        norm = DEPT_CANONICAL_MAP.get(d.lower().strip())
        if norm:
            pred_depts.add(norm)

    baseline_pred, baseline_depts = compute_baseline_prediction(tickets)

    return {
        "scenario_id": scenario["id"],
        "gt_hypothesis": gt_hyp,
        "gt_depts": gt_depts,
        "pred_top1": pred_top1,
        "pred_top2": pred_top2,
        "pred_depts": list(pred_depts),
        "confidence": confidence,
        "baseline_pred": baseline_pred,
        "baseline_depts": baseline_depts,
    }


def calculate_metrics(predictions: list[dict[str, Any]]) -> dict[str, float]:
    total = len(predictions)
    if total == 0:
        return {}

    top1_correct = 0
    top2_correct = 0
    dept_correct = 0
    baseline_top1_correct = 0
    baseline_dept_correct = 0
    dept_tp = dept_fp = dept_fn = 0
    baseline_dept_tp = baseline_dept_fp = baseline_dept_fn = 0
    dept_exact = baseline_dept_exact = 0

    confidences_correct: list[float] = []
    confidences_incorrect: list[float] = []

    for p in predictions:
        gt_h = p["gt_hypothesis"]
        gt_d = set(p["gt_depts"])

        is_top1 = p["pred_top1"] == gt_h
        if is_top1:
            top1_correct += 1
            confidences_correct.append(p["confidence"])
        else:
            confidences_incorrect.append(p["confidence"])

        if gt_h in (p["pred_top1"], p["pred_top2"]):
            top2_correct += 1

        pred_d = set(p["pred_depts"])
        baseline_d = set(p["baseline_depts"])
        if pred_d & gt_d:
            dept_correct += 1
        if pred_d == gt_d:
            dept_exact += 1
        dept_tp += len(pred_d & gt_d)
        dept_fp += len(pred_d - gt_d)
        dept_fn += len(gt_d - pred_d)

        if p["baseline_pred"] == gt_h:
            baseline_top1_correct += 1

        if any(d in gt_d for d in p["baseline_depts"]):
            baseline_dept_correct += 1
        if baseline_d == gt_d:
            baseline_dept_exact += 1
        baseline_dept_tp += len(baseline_d & gt_d)
        baseline_dept_fp += len(baseline_d - gt_d)
        baseline_dept_fn += len(gt_d - baseline_d)

    mean_conf_corr = (
        sum(confidences_correct) / len(confidences_correct) if confidences_correct else 0.0
    )
    mean_conf_inc = (
        sum(confidences_incorrect) / len(confidences_incorrect) if confidences_incorrect else 0.0
    )

    def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        return precision, recall, f1

    dept_precision, dept_recall, dept_f1 = prf(dept_tp, dept_fp, dept_fn)
    baseline_dept_precision, baseline_dept_recall, baseline_dept_f1 = prf(
        baseline_dept_tp, baseline_dept_fp, baseline_dept_fn
    )

    return {
        "total_scenarios": float(total),
        "top1_accuracy": top1_correct / total,
        "top2_accuracy": top2_correct / total,
        "dept_routing_accuracy": dept_correct / total,
        "dept_exact_match": dept_exact / total,
        "dept_precision": dept_precision,
        "dept_recall": dept_recall,
        "dept_f1": dept_f1,
        "baseline_top1_accuracy": baseline_top1_correct / total,
        "baseline_dept_accuracy": baseline_dept_correct / total,
        "baseline_dept_exact_match": baseline_dept_exact / total,
        "baseline_dept_precision": baseline_dept_precision,
        "baseline_dept_recall": baseline_dept_recall,
        "baseline_dept_f1": baseline_dept_f1,
        "mean_confidence_correct": mean_conf_corr,
        "mean_confidence_incorrect": mean_conf_inc,
    }


def run_eval(scenarios_dir: Optional[Path] = None) -> dict[str, Any]:
    s_dir = scenarios_dir or Path("backtest/scenarios")
    scenarios = load_all_scenarios(s_dir)
    predictions = [evaluate_single_scenario(sc) for sc in scenarios]
    metrics = calculate_metrics(predictions)
    return {"predictions": predictions, "metrics": metrics}


def main() -> None:
    parser = argparse.ArgumentParser(description="NammaTwin Backtest Evaluation Harness")
    parser.add_argument(
        "--scenarios-dir",
        type=str,
        default="backtest/scenarios",
        help="Path to scenarios directory",
    )
    args = parser.parse_args()

    results = run_eval(Path(args.scenarios_dir))
    m = results["metrics"]

    print("\n" + "=" * 65)
    print("NAMMATWIN VS BASELINE: ROOT CAUSE & ROUTING EVALUATION")
    print("=" * 65)
    print(f"Total Scenarios Evaluated: {int(m['total_scenarios'])}")
    print("-" * 65)
    print(f"{'Metric':<35} | {'NammaTwin':<12} | {'Baseline':<10}")
    print("-" * 65)
    print(f"{'Top-1 Root Cause Accuracy':<35} | {m['top1_accuracy']:>10.1%} | {m['baseline_top1_accuracy']:>8.1%}")
    print(f"{'Top-2 Root Cause Accuracy':<35} | {m['top2_accuracy']:>10.1%} | {'N/A':>8}")
    print(f"{'Department Routing Accuracy':<35} | {m['dept_routing_accuracy']:>10.1%} | {m['baseline_dept_accuracy']:>8.1%}")
    print(f"{'Department Exact Match':<35} | {m['dept_exact_match']:>10.1%} | {m['baseline_dept_exact_match']:>8.1%}")
    print(f"{'Department Micro F1':<35} | {m['dept_f1']:>10.1%} | {m['baseline_dept_f1']:>8.1%}")
    print("-" * 65)
    print(f"{'Mean Confidence (Correct Top-1)':<35} | {m['mean_confidence_correct']:>10.1%} | {'N/A':>8}")
    print(f"{'Mean Confidence (Incorrect)':<35} | {m['mean_confidence_incorrect']:>10.1%} | {'N/A':>8}")
    print("=" * 65 + "\n")

    # Generate report and chart
    from backtest.report import generate_report
    generate_report(results)


if __name__ == "__main__":
    main()
