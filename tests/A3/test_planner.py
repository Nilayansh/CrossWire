from datetime import datetime, timezone
import pytest

from app.contracts.keys import EvidenceKey, HypothesisID
from app.contracts.models import Action, Dossier, Evidence, Incident
from app.llm import FakeLLM
from app.planner.planner import PlanDraft, Planner


def sample_incident() -> Incident:
    return Incident(
        id="inc-stp-01",
        opened_at=datetime.now(timezone.utc),
        status="open",
        centroid=(12.928, 77.682),
        cells=["886189255bfffff"],
        category_mix={"power": 5, "sewage": 4},
    )


def sample_power_stp_dossier() -> Dossier:
    ev1 = Evidence(
        id="ev-stp-01",
        tool="history",
        ts=datetime.now(timezone.utc),
        summary="Power complaints preceded sewage overflow",
        keys=[EvidenceKey.POWER_TICKETS_PRECEDE_SEWAGE],
        source="tickets",
        provenance="real",
        raw={},
    )
    ev2 = Evidence(
        id="ev-stp-02",
        tool="outage",
        ts=datetime.now(timezone.utc),
        summary="11kV feeder trip confirmed",
        keys=[EvidenceKey.OUTAGE_REPORTED],
        source="bescom",
        provenance="simulated",
        raw={},
    )
    return Dossier(
        incident_id="inc-stp-01",
        ranked=[
            (HypothesisID.POWER_LED_STP_OVERFLOW, 0.88),
            (HypothesisID.DRAIN_BLOCKAGE, 0.08),
            (HypothesisID.RAIN_OVERWHELM, 0.02),
            (HypothesisID.TRAFFIC_ONLY, 0.02),
        ],
        evidence=[ev1, ev2],
        conclusive=True,
        stop_reason="conclusive",
        trace=[],
    )


def test_plan_fixture_dossier_generates_valid_actions():
    dossier = sample_power_stp_dossier()
    incident = sample_incident()
    osm_ctx = {"hospital_dist_m": 400.0, "school_dist_m": 500.0, "on_arterial": True}

    fake_llm = FakeLLM([
        PlanDraft(
            actions=[
                Action(
                    dept="power_utility",
                    action="Restore 11kV substation feeder power to tech park STP",
                    priority="P1",
                    rationale="Restore power to stop STP backflow",
                    evidence_ids=["ev-stp-01", "ev-stp-02"],
                    confidence=0.88,
                ),
                Action(
                    dept="sewerage",
                    action="Deploy suction jetting machines to clear overflow",
                    priority="P1",
                    rationale="Clear sewage backup along service road",
                    evidence_ids=["ev-stp-01"],
                    confidence=0.88,
                ),
            ]
        )
    ])

    planner = Planner(llm=fake_llm)
    actions = planner.plan(dossier=dossier, incident=incident, osm_ctx=osm_ctx)

    assert len(actions) == 2
    assert all(a.priority in ("P1", "P2", "P3") for a in actions)
    assert actions[0].dept == "power_utility"
    assert actions[1].dept == "sewerage"
    assert actions[0].id is not None


def test_planner_rejects_hallucinated_evidence_id():
    dossier = sample_power_stp_dossier()
    incident = sample_incident()
    osm_ctx = {"on_arterial": False}

    fake_llm = FakeLLM([
        PlanDraft(
            actions=[
                Action(
                    dept="power_utility",
                    action="Dispatch repair team",
                    priority="P2",
                    rationale="Outage detected",
                    evidence_ids=["ev-stp-999-hallucinated"],  # Not in dossier
                    confidence=0.88,
                ),
                Action(
                    dept="sewerage",
                    action="Deploy vacuum truck",
                    priority="P2",
                    rationale="Sewage spill",
                    evidence_ids=["ev-stp-01"],
                    confidence=0.88,
                ),
            ]
        )
    ])

    planner = Planner(llm=fake_llm)
    actions = planner.plan(dossier=dossier, incident=incident, osm_ctx=osm_ctx)

    # First action rejected, second action accepted
    assert len(actions) == 1
    assert actions[0].dept == "sewerage"


def test_planner_demotes_low_confidence_actions():
    dossier = Dossier(
        incident_id="inc-stp-01",
        ranked=[
            (HypothesisID.POWER_LED_STP_OVERFLOW, 0.45),  # Low confidence < 0.6
            (HypothesisID.DRAIN_BLOCKAGE, 0.40),
        ],
        evidence=[
            Evidence(
                id="ev-stp-01",
                tool="history",
                ts=datetime.now(timezone.utc),
                summary="Some power tickets",
                keys=[EvidenceKey.POWER_TICKETS_PRECEDE_SEWAGE],
                source="tickets",
                provenance="real",
                raw={},
            )
        ],
        conclusive=False,
        stop_reason="inconclusive",
        trace=[],
    )
    incident = sample_incident()
    osm_ctx = {"on_arterial": False}

    fake_llm = FakeLLM([
        PlanDraft(
            actions=[
                Action(
                    dept="power_utility",
                    action="Deploy major emergency transformer replacement",
                    priority="P2",
                    rationale="Investigate suspected trip",
                    evidence_ids=["ev-stp-01"],
                    confidence=0.45,
                )
            ]
        )
    ])

    planner = Planner(llm=fake_llm)
    actions = planner.plan(dossier=dossier, incident=incident, osm_ctx=osm_ctx)

    assert len(actions) == 1
    assert actions[0].needs_field_verification is True
    assert actions[0].action.lower().startswith("inspect and verify")


def test_planner_run_cli():
    import subprocess
    import sys

    res = subprocess.run(
        [sys.executable, "-m", "app.planner.run", "--scenario", "power_led_stp"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "DISPATCH PLAN" in res.stdout
    assert "POWER_LED_STP_OVERFLOW" in res.stdout
    assert "power_utility" in res.stdout

