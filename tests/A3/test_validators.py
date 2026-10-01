from datetime import datetime, timezone
import pytest

from app.contracts.keys import EvidenceKey, HypothesisID
from app.contracts.models import Action, Dossier, Evidence
from app.planner.validators import validate_actions


def sample_dossier() -> Dossier:
    ev1 = Evidence(
        id="ev-rain-01",
        tool="rainfall",
        ts=datetime.now(timezone.utc),
        summary="High rainfall recorded",
        keys=[EvidenceKey.RAIN_GT_40],
        source="open_meteo",
        provenance="real",
        raw={},
    )
    ev2 = Evidence(
        id="ev-rain-02",
        tool="elevation",
        ts=datetime.now(timezone.utc),
        summary="Low elevation bowl",
        keys=[EvidenceKey.LOW_LYING],
        source="srtm",
        provenance="real",
        raw={},
    )
    return Dossier(
        incident_id="inc-test-01",
        ranked=[
            (HypothesisID.RAIN_OVERWHELM, 0.85),
            (HypothesisID.DRAIN_BLOCKAGE, 0.10),
            (HypothesisID.LAKE_OVERFLOW, 0.03),
            (HypothesisID.TRAFFIC_ONLY, 0.02),
        ],
        evidence=[ev1, ev2],
        conclusive=True,
        stop_reason="conclusive",
        trace=[],
    )


def test_reject_empty_evidence_ids():
    dossier = sample_dossier()
    actions = [
        Action(
            dept="stormwater",
            action="Clear culvert",
            priority="P1",
            rationale="Waterlogging issue",
            evidence_ids=[],  # empty
            confidence=0.85,
        )
    ]
    valid = validate_actions(actions, dossier)
    assert len(valid) == 0


def test_reject_hallucinated_evidence_id():
    dossier = sample_dossier()
    actions = [
        Action(
            dept="stormwater",
            action="Clear culvert",
            priority="P1",
            rationale="Waterlogging issue",
            evidence_ids=["ev-nonexistent-99"],  # not in dossier
            confidence=0.85,
        )
    ]
    valid = validate_actions(actions, dossier)
    assert len(valid) == 0


def test_accept_valid_evidence_ids():
    dossier = sample_dossier()
    actions = [
        Action(
            dept="stormwater",
            action="Deploy high-capacity dewatering pumps",
            priority="P1",
            rationale="Flooding at low lying area",
            evidence_ids=["ev-rain-01"],
            confidence=0.85,
        )
    ]
    valid = validate_actions(actions, dossier)
    assert len(valid) == 1
    assert valid[0].dept == "stormwater"


def test_reject_department_outside_top2_hypotheses():
    dossier = sample_dossier()
    # Top-2 hypotheses in sample_dossier are RAIN_OVERWHELM and DRAIN_BLOCKAGE:
    # allowed depts: stormwater, traffic_police, solid_waste
    # water_board belongs to PIPE_BURST (rank 4+), should be rejected
    actions = [
        Action(
            dept="water_board",
            action="Repair mainline water pipeline",
            priority="P2",
            rationale="Pipe burst hypothesis",
            evidence_ids=["ev-rain-01"],
            confidence=0.75,
        ),
        Action(
            dept="solid_waste",
            action="Clear debris from secondary drain",
            priority="P2",
            rationale="Drain blockage mitigation",
            evidence_ids=["ev-rain-02"],
            confidence=0.75,
        ),
    ]
    valid = validate_actions(actions, dossier)
    assert len(valid) == 1
    assert valid[0].dept == "solid_waste"


def test_low_confidence_demotes_and_rewrites_remedy_verbs():
    dossier = sample_dossier()
    actions = [
        Action(
            dept="stormwater",
            action="Deploy backhoe and excavate blockage",
            priority="P2",
            rationale="Suspected debris",
            evidence_ids=["ev-rain-01"],
            confidence=0.45,  # Low confidence < 0.6
            needs_field_verification=False,
        )
    ]
    valid = validate_actions(actions, dossier)
    assert len(valid) == 1
    action = valid[0]
    assert action.needs_field_verification is True
    assert action.action.lower().startswith("inspect and verify")
