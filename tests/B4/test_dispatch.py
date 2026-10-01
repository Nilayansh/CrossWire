import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from app.contracts.models import Action, Evidence, OutboundMessage, Delivery
from app.contracts.keys import EvidenceKey
from app.dispatch.templates import render_citizen_message, render_department_dispatch, CITIZEN_TEMPLATES
from app.dispatch.notifier import MultiChannelNotifier
from app.dispatch.telegram import TelegramChannel
from app.dispatch.email import EmailChannel


def test_template_snapshots_en_and_kn():
    # Verify all expected statuses exist in both languages
    expected_statuses = {"received", "investigating", "dispatched", "resolving", "closed"}
    assert set(CITIZEN_TEMPLATES["en"].keys()) == expected_statuses
    assert set(CITIZEN_TEMPLATES["kn"].keys()) == expected_statuses

    # English render check
    msg_en = render_citizen_message(
        ticket_id="t-001",
        category="waterlogging",
        status="dispatched",
        dept="stormwater",
        officer="Inspector Ravi",
        lang="en",
    )
    assert "t-001" in msg_en
    assert "waterlogging" in msg_en
    assert "Inspector Ravi" in msg_en
    assert "Stormwater" in msg_en

    # Kannada render check
    msg_kn = render_citizen_message(
        ticket_id="t-002",
        category="waterlogging",
        status="dispatched",
        dept="stormwater",
        officer="ರವಿ",
        lang="kn",
    )
    assert "t-002" in msg_kn
    assert "ರವಿ" in msg_kn
    assert "ಕ್ರಮ ಅನುಮೋದಿಸಲಾಗಿದೆ" in msg_kn


def test_department_dispatch_template_structure():
    action = Action(
        id="act-test-01",
        dept="stormwater",
        action="Deploy submersible pumps at Ecospace",
        target_latlon=(12.926, 77.683),
        priority="P1",
        rationale="Overwhelming cloudburst causing low-lying accumulation",
        evidence_ids=["ev-01"],
        confidence=0.92,
        needs_field_verification=True,
    )
    ev = Evidence(
        id="ev-01",
        tool="rainfall",
        ts=datetime(2026, 9, 5, 8, 0, 0, tzinfo=timezone.utc),
        summary="Rainfall exceeded 40 mm/hr",
        keys=[EvidenceKey.RAIN_GT_40],
        source="Open-Meteo",
        provenance="real",
    )

    rendered = render_department_dispatch(
        incident_id="inc-test-01",
        action=action,
        officer="Officer Ramesh",
        evidence_list=[ev],
    )

    assert "🚨 OFFICIAL DISPATCH ORDER | INCIDENT inc-test-01" in rendered
    assert "Department:       STORMWATER" in rendered
    assert "Priority Band:    P1" in rendered
    assert "12.9260, 77.6830" in rendered
    assert "Deploy submersible pumps at Ecospace" in rendered
    assert "⚠️  DIRECTIVE: Immediate on-site inspection" in rendered
    assert "Authorized by Officer Officer Ramesh" in rendered
    assert "[REAL] rainfall" in rendered
    assert "RAIN_GT_40" in rendered


def test_idempotency_second_send_is_noop(tmp_path, monkeypatch):
    outbox_file = tmp_path / "outbox.jsonl"
    monkeypatch.setattr("app.dispatch.notifier._get_outbox_path", lambda: outbox_file)

    notifier = MultiChannelNotifier(dry_run=True)
    msg = OutboundMessage(
        recipient="stormwater",
        subject="Deploy pumps",
        body="Order details",
        metadata={"incident_id": "inc-idemp-1", "action_id": "act-idemp-1"},
    )

    # First send
    deliv1 = notifier.send("stormwater", msg)
    assert deliv1.status == "dry_run"
    assert deliv1.channel == "telegram"
    assert len(notifier.history) == 1

    # Second send with same incident_id and action_id
    deliv2 = notifier.send("stormwater", msg)
    assert deliv1 == deliv2
    assert len(notifier.history) == 1  # No duplicate execution or history entry

    # Verify only 1 line written to outbox file
    with open(outbox_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) == 1


def test_dry_run_writes_jsonl(tmp_path, monkeypatch):
    outbox_file = tmp_path / "outbox.jsonl"
    monkeypatch.setattr("app.dispatch.notifier._get_outbox_path", lambda: outbox_file)

    notifier = MultiChannelNotifier(dry_run=True)
    msg = OutboundMessage(
        recipient="power_utility",
        subject="Isolate feeder",
        body="Isolate feeder F-01",
        metadata={"incident_id": "inc-dry-01", "action_id": "act-dry-01"},
    )

    deliv = notifier.send("power_utility", msg)
    assert deliv.status == "dry_run"

    assert outbox_file.exists()
    with open(outbox_file, "r", encoding="utf-8") as f:
        record = json.loads(f.readline())

    assert record["incident_id"] == "inc-dry-01"
    assert record["action_id"] == "act-dry-01"
    assert record["department"] == "power_utility"
    assert record["channel"] == "telegram"
    assert record["status"] == "dry_run"
    assert "Isolate feeder F-01" in record["body"]


def test_channel_failure_degrades_to_email():
    mock_tg = MagicMock(spec=TelegramChannel)
    # Simulate Telegram failure
    mock_tg.send.return_value = (False, "Telegram network timeout connection refused")

    mock_email = MagicMock(spec=EmailChannel)
    # Email succeeds
    mock_email.send.return_value = (True, None)

    notifier = MultiChannelNotifier(
        dry_run=False,
        telegram_channel=mock_tg,
        email_channel=mock_email,
    )

    msg = OutboundMessage(
        recipient="traffic_police",
        subject="Divert traffic",
        body="Divert traffic order",
        metadata={"incident_id": "inc-degrade-01", "action_id": "act-degrade-01"},
    )

    deliv = notifier.send("traffic_police", msg)

    assert deliv.channel == "email"
    assert deliv.status == "sent"
    assert deliv.error is not None
    assert "Telegram" in deliv.error
    assert "degraded to email" in deliv.error

    mock_tg.send.assert_called_once()
    mock_email.send.assert_called_once()
