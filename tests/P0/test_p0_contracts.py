import json
from datetime import datetime, timezone
import pytest
from app.contracts.keys import HypothesisID, EvidenceKey
from app.contracts.models import (
    Ticket,
    Incident,
    Evidence,
    ToolArgs,
    ToolSpec,
    Dossier,
    Action,
    Decision,
    Delivery,
    OutboundMessage,
)
from app.contracts.interfaces import (
    TicketRepo,
    IncidentRepo,
    EvidenceRepo,
    ToolRegistry,
    Notifier,
    ClusterDetector,
)
from app.llm import FakeLLM
from app.tools._registry import discover, get_registry
from app.stubs.in_memory_repos import InMemoryTicketRepo, InMemoryIncidentRepo, InMemoryEvidenceRepo
from app.stubs.console_notifier import ConsoleNotifier
from app.stubs.fake_tool_registry import FakeToolRegistry


def test_keys_enums_defined():
    assert len(HypothesisID) >= 6
    assert HypothesisID.RAIN_OVERWHELM == "RAIN_OVERWHELM"
    assert HypothesisID.DRAIN_BLOCKAGE == "DRAIN_BLOCKAGE"
    assert HypothesisID.POWER_LED_STP_OVERFLOW == "POWER_LED_STP_OVERFLOW"
    assert HypothesisID.PIPE_BURST == "PIPE_BURST"
    assert HypothesisID.LAKE_OVERFLOW == "LAKE_OVERFLOW"
    assert HypothesisID.TRAFFIC_ONLY == "TRAFFIC_ONLY"

    assert len(EvidenceKey) >= 15
    assert EvidenceKey.RAIN_GT_40 == "RAIN_GT_40"
    assert EvidenceKey.RAIN_GT_25 == "RAIN_GT_25"
    assert EvidenceKey.RAIN_LT_15 == "RAIN_LT_15"
    assert EvidenceKey.RAIN_LT_5 == "RAIN_LT_5"
    assert EvidenceKey.SUSTAINED_RAIN_24H == "SUSTAINED_RAIN_24H"
    assert EvidenceKey.LOW_LYING == "LOW_LYING"
    assert EvidenceKey.KNOWN_HOTSPOT == "KNOWN_HOTSPOT"
    assert EvidenceKey.NEAR_LAKE == "NEAR_LAKE"
    assert EvidenceKey.LARGE_STP_SITE_NEARBY == "LARGE_STP_SITE_NEARBY"
    assert EvidenceKey.DEBRIS_TICKETS_NEARBY == "DEBRIS_TICKETS_NEARBY"
    assert EvidenceKey.LOCALIZED_SPREAD == "LOCALIZED_SPREAD"
    assert EvidenceKey.LINEAR_SPREAD == "LINEAR_SPREAD"
    assert EvidenceKey.POWER_TICKETS_PRECEDE_SEWAGE == "POWER_TICKETS_PRECEDE_SEWAGE"
    assert EvidenceKey.OUTAGE_REPORTED == "OUTAGE_REPORTED"
    assert EvidenceKey.NO_WATER_POWER_SIGNAL == "NO_WATER_POWER_SIGNAL"
    assert EvidenceKey.TRAFFIC_SLOWDOWN == "TRAFFIC_SLOWDOWN"
    assert EvidenceKey.DRY_WEATHER == "DRY_WEATHER"


def test_models_json_roundtrip():
    now = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Ticket
    ticket = Ticket(
        id="t-001",
        ts=now,
        channel="telegram",
        lang="kn",
        text_original="ರಸ್ತೆ ಜಲಾವೃತವಾಗಿದೆ",
        text_en="Road is waterlogged",
        category="waterlogging",
        severity=4,
        lat=12.935,
        lon=77.682,
        geo_confidence=0.9,
        h3_r8="886189255bfffff",
        photo_depth="knee",
        reporter_chat_id="123456",
        is_synthetic=True,
    )
    ticket_json = ticket.model_dump_json()
    assert Ticket.model_validate_json(ticket_json) == ticket

    # 2. Incident
    incident = Incident(
        id="inc-101",
        opened_at=now,
        status="open",
        ticket_ids=["t-001"],
        centroid=(12.935, 77.682),
        cells=["886189255bfffff"],
        category_mix={"waterlogging": 1},
    )
    inc_json = incident.model_dump_json()
    assert Incident.model_validate_json(inc_json) == incident

    # 3. Evidence
    evidence = Evidence(
        id="ev-01",
        tool="rainfall",
        ts=now,
        summary="Rainfall exceeded 40mm/hr",
        keys=[EvidenceKey.RAIN_GT_40],
        source="Open-Meteo",
        provenance="real",
        raw={"hourly_max": 42.5},
    )
    ev_json = evidence.model_dump_json()
    assert Evidence.model_validate_json(ev_json) == evidence

    # 4. ToolArgs
    args = ToolArgs(
        incident_id="inc-101",
        lat=12.935,
        lon=77.682,
        t0=now,
        t1=now,
        cells=["886189255bfffff"],
    )
    args_json = args.model_dump_json()
    assert ToolArgs.model_validate_json(args_json) == args

    # 5. Dossier
    dossier = Dossier(
        incident_id="inc-101",
        ranked=[(HypothesisID.RAIN_OVERWHELM, 0.85), (HypothesisID.DRAIN_BLOCKAGE, 0.15)],
        evidence=[evidence],
        conclusive=True,
        stop_reason="Confidence threshold exceeded",
        trace=[{"step": 1, "tool": "rainfall", "why": "Check rain intensity"}],
    )
    dos_json = dossier.model_dump_json()
    assert Dossier.model_validate_json(dos_json) == dossier

    # 6. Action
    action = Action(
        dept="stormwater",
        action="Clear culvert and deploy mobile pumps",
        target_latlon=(12.935, 77.682),
        priority="P1",
        rationale="Severe flooding near major junction",
        evidence_ids=["ev-01"],
        confidence=0.85,
        needs_field_verification=False,
    )
    action_json = action.model_dump_json()
    assert Action.model_validate_json(action_json) == action

    # 7. Decision
    decision = Decision(
        incident_id="inc-101",
        approved_action_ids=["act-01"],
        edits={},
        rejected={},
        officer="Officer Kumar",
    )
    dec_json = decision.model_dump_json()
    assert Decision.model_validate_json(dec_json) == decision

    # 8. Delivery
    delivery = Delivery(
        incident_id="inc-101",
        action_id="act-01",
        channel="telegram",
        status="sent",
        sent_at=now,
        error=None,
    )
    del_json = delivery.model_dump_json()
    assert Delivery.model_validate_json(del_json) == delivery


def test_fake_llm_structured():
    fake = FakeLLM()
    now = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
    expected_decision = Decision(
        incident_id="inc-999",
        approved_action_ids=["a1"],
        edits={"a1": "Edited action description"},
        rejected={},
        officer="Chief Engineer",
    )
    fake.set_responses([expected_decision])
    result = fake.structured(Decision, "Approve or edit actions", tier="fast")
    assert result == expected_decision
    assert len(fake.call_history) == 1
    assert fake.call_history[0]["schema"] == Decision


def test_discover_empty_tools():
    # Calling discover() without registered tools should succeed cleanly
    registry = discover()
    assert isinstance(registry, dict)


def test_in_memory_stubs():
    now = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
    # Ticket Repo
    t_repo: TicketRepo = InMemoryTicketRepo()
    t = Ticket(
        id="t-1",
        ts=now,
        channel="web",
        lang="en",
        text_original="Flooding on ORR",
        text_en="Flooding on ORR",
        category="waterlogging",
        severity=3,
        lat=12.93,
        lon=77.68,
        geo_confidence=1.0,
        h3_r8="886189255bfffff",
    )
    t_repo.add(t)
    tickets = t_repo.window(["886189255bfffff"], now, now)
    assert len(tickets) == 1
    assert tickets[0].id == "t-1"

    # Incident Repo
    i_repo: IncidentRepo = InMemoryIncidentRepo()
    inc = Incident(
        id="inc-1",
        opened_at=now,
        centroid=(12.93, 77.68),
        cells=["886189255bfffff"],
    )
    i_repo.upsert(inc)
    assert i_repo.get("inc-1") is not None
    assert len(i_repo.open()) == 1

    # Notifier
    notifier: Notifier = ConsoleNotifier()
    msg = OutboundMessage(recipient="stormwater_chat", body="Deploy pump")
    delivery = notifier.send("stormwater", msg)
    assert delivery.status in ("sent", "dry_run")

    # Fake Tool Registry
    fake_tool_reg: ToolRegistry = FakeToolRegistry()
    assert isinstance(fake_tool_reg.specs(), list)


def test_fixtures_load_and_validate():
    import pathlib
    fixtures_dir = pathlib.Path(__file__).parent.parent / "fixtures"

    # 1. Tickets fixture
    tickets_path = fixtures_dir / "tickets_bellandur_flood.json"
    assert tickets_path.exists()
    with open(tickets_path, "r", encoding="utf-8") as f:
        tickets_data = json.load(f)
    assert len(tickets_data) == 14
    tickets = [Ticket.model_validate(t) for t in tickets_data]
    assert len(tickets) == 14

    # 2. Rain overwhelm evidence
    rain_path = fixtures_dir / "evidence_rain_overwhelm.json"
    assert rain_path.exists()
    with open(rain_path, "r", encoding="utf-8") as f:
        rain_data = json.load(f)
    rain_ev = [Evidence.model_validate(e) for e in rain_data]
    assert len(rain_ev) == 3

    # 3. Power STP evidence
    stp_path = fixtures_dir / "evidence_power_led_stp.json"
    assert stp_path.exists()
    with open(stp_path, "r", encoding="utf-8") as f:
        stp_data = json.load(f)
    stp_ev = [Evidence.model_validate(e) for e in stp_data]
    assert len(stp_ev) == 3

    # 4. Inconclusive evidence
    incon_path = fixtures_dir / "evidence_inconclusive.json"
    assert incon_path.exists()
    with open(incon_path, "r", encoding="utf-8") as f:
        incon_data = json.load(f)
    incon_ev = [Evidence.model_validate(e) for e in incon_data]
    assert len(incon_ev) == 2
