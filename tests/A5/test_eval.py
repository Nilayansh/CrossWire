import json
from pathlib import Path
import time
import pytest

from app.contracts.keys import HypothesisID
from app.contracts.models import Evidence, Ticket
from backtest.eval import calculate_metrics, load_all_scenarios, run_eval


def test_scenarios_schema_validation():
    scenarios = load_all_scenarios(Path("backtest/scenarios"))
    assert len(scenarios) >= 15, f"Expected at least 15 scenarios, found {len(scenarios)}"

    valid_hypotheses = {h.value for h in HypothesisID}
    traffic_scenarios = 0
    ambiguous_scenarios = 0

    for sc in scenarios:
        assert "id" in sc and isinstance(sc["id"], str)
        assert "tickets" in sc and isinstance(sc["tickets"], list)
        assert len(sc["tickets"]) > 0
        for t in sc["tickets"]:
            Ticket.model_validate(t)

        assert "evidence_overrides" in sc and isinstance(sc["evidence_overrides"], list)
        for ev in sc["evidence_overrides"]:
            Evidence.model_validate(ev)

        gt_hyp = sc["ground_truth_hypothesis"]
        assert gt_hyp in valid_hypotheses
        if gt_hyp == HypothesisID.TRAFFIC_ONLY.value:
            traffic_scenarios += 1
        if "ambiguous" in sc["id"]:
            ambiguous_scenarios += 1

        assert "ground_truth_depts" in sc and isinstance(sc["ground_truth_depts"], list)
        assert len(sc["ground_truth_depts"]) > 0

    assert traffic_scenarios >= 1, "Must include TRAFFIC_ONLY scenarios"
    assert ambiguous_scenarios >= 2, "Must include at least 2 ambiguous scenarios"


def test_metrics_calculation_handmade_set():
    predictions = [
        {
            "scenario_id": "s1",
            "gt_hypothesis": "RAIN_OVERWHELM",
            "gt_depts": ["stormwater", "traffic_police"],
            "pred_top1": "RAIN_OVERWHELM",
            "pred_top2": "DRAIN_BLOCKAGE",
            "pred_depts": ["stormwater"],
            "confidence": 0.90,
            "baseline_pred": "RAIN_OVERWHELM",
            "baseline_depts": ["stormwater"],
        },
        {
            "scenario_id": "s2",
            "gt_hypothesis": "POWER_LED_STP_OVERFLOW",
            "gt_depts": ["power_utility", "sewerage"],
            "pred_top1": "DRAIN_BLOCKAGE",
            "pred_top2": "POWER_LED_STP_OVERFLOW",
            "pred_depts": ["power_utility"],
            "confidence": 0.70,
            "baseline_pred": "DRAIN_BLOCKAGE",
            "baseline_depts": ["solid_waste"],
        },
        {
            "scenario_id": "s3",
            "gt_hypothesis": "PIPE_BURST",
            "gt_depts": ["water_board"],
            "pred_top1": "RAIN_OVERWHELM",
            "pred_top2": "LAKE_OVERFLOW",
            "pred_depts": ["stormwater"],
            "confidence": 0.50,
            "baseline_pred": "DRAIN_BLOCKAGE",
            "baseline_depts": ["stormwater"],
        },
    ]

    metrics = calculate_metrics(predictions)
    assert abs(metrics["top1_accuracy"] - (1.0 / 3.0)) < 1e-4
    assert abs(metrics["top2_accuracy"] - (2.0 / 3.0)) < 1e-4
    assert abs(metrics["dept_routing_accuracy"] - (2.0 / 3.0)) < 1e-4
    assert abs(metrics["dept_precision"] - (2.0 / 3.0)) < 1e-4
    assert abs(metrics["dept_recall"] - 0.4) < 1e-4
    assert abs(metrics["dept_f1"] - 0.5) < 1e-4
    assert metrics["dept_exact_match"] == 0.0
    assert abs(metrics["baseline_top1_accuracy"] - (1.0 / 3.0)) < 1e-4
    assert metrics["mean_confidence_correct"] > metrics["mean_confidence_incorrect"]


def test_eval_runs_offline_under_60s():
    t0 = time.time()
    results = run_eval(Path("backtest/scenarios"))
    elapsed = time.time() - t0

    assert elapsed < 60.0, f"Eval took {elapsed:.2f}s, expected < 60s"
    assert "metrics" in results
    assert results["metrics"]["top1_accuracy"] >= 0.70
    assert results["metrics"]["top2_accuracy"] >= 0.85


def test_department_prediction_uses_only_top_cause():
    results = run_eval(Path("backtest/scenarios"))
    by_id = {p["scenario_id"]: p for p in results["predictions"]}
    # The runner-up for this pipe burst is DRAIN_BLOCKAGE, whose departments
    # must not be added to the primary route.
    assert set(by_id["scen_pipe_ejipura_10"]["pred_depts"]) == {"water_board"}
