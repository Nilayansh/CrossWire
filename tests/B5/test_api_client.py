from __future__ import annotations

from app.contracts.models import Decision, Ticket
from ui.api_client import ApiClient, parse_sse_stream


def test_parse_sse_stream():
    sample_sse = [
        "data: {\"step\": 1, \"tool\": \"rainfall\"}\n",
        "\n",
        "data: {\"step\": 2, \"tool\": \"elevation\"}\n",
        "\n",
        "event: end\n",
        "data: {}\n",
    ]
    events = parse_sse_stream(sample_sse)
    assert len(events) == 2
    assert events[0]["step"] == 1
    assert events[0]["tool"] == "rainfall"
    assert events[1]["step"] == 2
    assert events[1]["tool"] == "elevation"


def test_api_client_mock_mode():
    client = ApiClient(use_mock=True)

    # Health
    assert client.is_healthy() is True

    # Incidents list
    incidents = client.get_incidents()
    assert len(incidents) >= 1
    inc_id = incidents[0].id

    # Incident detail
    detail = client.get_incident(inc_id)
    assert detail.incident.id == inc_id
    assert detail.dossier is not None
    assert len(detail.actions) >= 1

    # Ingest ticket
    sample_ticket = Ticket(
        id="t-mock-test",
        ts="2026-09-05T08:00:00Z",
        channel="web",
        lang="en",
        text_original="Water rising",
        text_en="Water rising",
        category="waterlogging",
        severity=4,
        lat=12.928,
        lon=77.683,
        geo_confidence=0.9,
        h3_r8="886189255bfffff",
    )
    res_ingest = client.ingest_ticket(sample_ticket)
    assert res_ingest.ticket_id == "t-mock-test"

    # Submit decision
    decision = Decision(
        incident_id=inc_id,
        approved_action_ids=["act-001"],
        rejected={},
        edits={},
        officer="Inspector General",
    )
    res_decision = client.submit_decision(inc_id, decision)
    assert res_decision["status"] == "dispatched"

    # Verify incident
    res_verify = client.verify_incident(inc_id, fast_forward_min=45)
    assert res_verify.status == "resolving"
    assert res_verify.fast_forward_min == 45

    # Trace events
    trace = client.get_trace_events(inc_id)
    assert len(trace) >= 1
    assert trace[0]["step"] == 1


def test_api_client_automatic_fallback():
    # Attempting to connect to an invalid port falls back to mock without raising
    client = ApiClient(base_url="http://localhost:65530", use_mock=False, timeout=0.5)
    incidents = client.get_incidents()
    assert len(incidents) >= 1
    assert client.is_mock_fallback is True
