import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from app.contracts.models import Ticket
from app.cluster.detector import H3ClusterDetector
from app.stubs.in_memory_repos import InMemoryTicketRepo, InMemoryIncidentRepo


def load_bellandur_fixture() -> list[Ticket]:
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "tickets_bellandur_flood.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    tickets = [Ticket.model_validate(t) for t in data]
    tickets.sort(key=lambda t: t.ts)
    return tickets


def test_bellandur_flood_fixture_opens_one_incident_at_ticket_4():
    tickets = load_bellandur_fixture()
    assert len(tickets) == 14

    ticket_repo = InMemoryTicketRepo()
    incident_repo = InMemoryIncidentRepo()
    detector = H3ClusterDetector(ticket_repo=ticket_repo, incident_repo=incident_repo)

    opened_incidents = set()
    events = []

    for i, t in enumerate(tickets, start=1):
        res = detector.ingest(t)
        events.append((i, t.id, res))
        if res:
            opened_incidents.add(res.id)

    # First 3 tickets do NOT trigger an incident
    assert events[0][2] is None
    assert events[1][2] is None
    assert events[2][2] is None

    # Ticket 4 triggers the incident
    inc_4 = events[3][2]
    assert inc_4 is not None
    assert inc_4.id == "inc-004"
    assert inc_4.status == "open"
    assert len(inc_4.ticket_ids) == 4
    assert set(inc_4.ticket_ids) == {"t-001", "t-002", "t-003", "t-004"}
    assert inc_4.reinvestigate is True

    # Remaining 10 tickets attach to this same incident
    for i in range(4, 14):
        attached_inc = events[i][2]
        assert attached_inc is not None
        assert attached_inc.id == "inc-004"

    # Exactly 1 incident opened across the entire stream
    assert len(opened_incidents) == 1
    assert len(incident_repo.all()) == 1
    final_inc = incident_repo.get("inc-004")
    assert len(final_inc.ticket_ids) == 14


def test_boundary_three_tickets_no_incident():
    detector = H3ClusterDetector()
    t0 = datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc)

    # 3 tickets across 3 different categories
    for i, cat in enumerate(["waterlogging", "traffic", "power"]):
        tk = Ticket(
            id=f"t-sub-{i}",
            ts=t0 + timedelta(minutes=i * 2),
            channel="web",
            lang="en",
            text_original="test",
            text_en="test",
            category=cat,
            severity=3,
            lat=12.926,
            lon=77.683,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        )
        result = detector.ingest(tk)
        assert result is None, f"Ticket {i+1} should not trigger an incident"


def test_cross_category_threshold_triggers():
    detector = H3ClusterDetector()
    t0 = datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc)

    # 4 tickets with 2 categories (3 waterlogging, 1 traffic)
    categories = ["waterlogging", "waterlogging", "waterlogging", "traffic"]
    inc = None
    for i, cat in enumerate(categories):
        tk = Ticket(
            id=f"t-cross-{i}",
            ts=t0 + timedelta(minutes=i * 3),
            channel="web",
            lang="en",
            text_original="test",
            text_en="test",
            category=cat,
            severity=3,
            lat=12.926,
            lon=77.683,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        )
        inc = detector.ingest(tk)

    assert inc is not None
    assert len(inc.ticket_ids) == 4
    assert inc.category_mix == {"waterlogging": 3, "traffic": 1}


def test_single_category_threshold_triggers_at_8_tickets():
    detector = H3ClusterDetector()
    t0 = datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc)

    # Ingest 7 tickets of single category (waterlogging) -> should NOT trigger
    for i in range(7):
        tk = Ticket(
            id=f"t-single-{i}",
            ts=t0 + timedelta(minutes=i * 2),
            channel="web",
            lang="en",
            text_original="water",
            text_en="water",
            category="waterlogging",
            severity=3,
            lat=12.926,
            lon=77.683,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        )
        assert detector.ingest(tk) is None

    # 8th ticket of same category triggers incident!
    tk8 = Ticket(
        id="t-single-7",
        ts=t0 + timedelta(minutes=14),
        channel="web",
        lang="en",
        text_original="water",
        text_en="water",
        category="waterlogging",
        severity=3,
        lat=12.926,
        lon=77.683,
        geo_confidence=0.9,
        h3_r8="886189255bfffff",
    )
    inc = detector.ingest(tk8)
    assert inc is not None
    assert len(inc.ticket_ids) == 8
    assert inc.category_mix == {"waterlogging": 8}


def test_tickets_outside_ring_do_not_join():
    detector = H3ClusterDetector()
    t0 = datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc)

    # Open an incident at 886189255bfffff
    categories = ["waterlogging", "waterlogging", "traffic", "power"]
    for i, cat in enumerate(categories):
        tk = Ticket(
            id=f"t-orig-{i}",
            ts=t0 + timedelta(minutes=i * 2),
            channel="web",
            lang="en",
            text_original="test",
            text_en="test",
            category=cat,
            severity=3,
            lat=12.926,
            lon=77.683,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        )
        detector.ingest(tk)

    # New ticket in a distant cell (e.g., cell in Indiranagar/Whitefield ~ 5 hops away)
    far_ticket = Ticket(
        id="t-far-1",
        ts=t0 + timedelta(minutes=10),
        channel="web",
        lang="en",
        text_original="far water",
        text_en="far water",
        category="waterlogging",
        severity=3,
        lat=12.978,
        lon=77.640,
        geo_confidence=0.9,
        h3_r8="886189254dfffff",  # 5 hops away from 886189255bfffff
    )
    # Does not attach to the Bellandur incident, and by itself doesn't meet cluster threshold
    res = detector.ingest(far_ticket)
    assert res is None

    # Bellandur incident should still only have the original 4 tickets
    inc = detector.incident_repo.all()[0]
    assert len(inc.ticket_ids) == 4
    assert "t-far-1" not in inc.ticket_ids


def test_tickets_outside_window_do_not_join():
    detector = H3ClusterDetector(window_minutes=60)
    t0 = datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc)

    # Trigger incident with 4 tickets
    for i, cat in enumerate(["waterlogging", "traffic", "power", "sewage"]):
        tk = Ticket(
            id=f"t-win-{i}",
            ts=t0 + timedelta(minutes=i * 2),
            channel="web",
            lang="en",
            text_original="test",
            text_en="test",
            category=cat,
            severity=3,
            lat=12.926,
            lon=77.683,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        )
        detector.ingest(tk)

    # Ticket arriving 65 minutes after the latest ticket
    late_ticket = Ticket(
        id="t-late",
        ts=t0 + timedelta(minutes=75),
        channel="web",
        lang="en",
        text_original="late water",
        text_en="late water",
        category="waterlogging",
        severity=3,
        lat=12.926,
        lon=77.683,
        geo_confidence=0.9,
        h3_r8="886189255bfffff",
    )
    res = detector.ingest(late_ticket)
    # Since it's > 60 min after the latest ticket in the open incident, it does not join
    # and 1 ticket alone doesn't trigger a new incident
    assert res is None


def test_debounce_reinvestigation_logic():
    detector = H3ClusterDetector(debounce_minutes=5)
    t0 = datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc)

    # 4 tickets to open incident at t0 + 6 min
    for i, cat in enumerate(["waterlogging", "waterlogging", "traffic", "power"]):
        tk = Ticket(
            id=f"t-deb-{i}",
            ts=t0 + timedelta(minutes=i * 2),
            channel="web",
            lang="en",
            text_original="test",
            text_en="test",
            category=cat,
            severity=3,
            lat=12.926,
            lon=77.683,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        )
        detector.ingest(tk)

    # At t0 + 7 min (only 1 min after trigger at t0+6 min): joins, but reinvestigate must be False
    tk_fast = Ticket(
        id="t-deb-fast",
        ts=t0 + timedelta(minutes=7),
        channel="web",
        lang="en",
        text_original="fast water",
        text_en="fast water",
        category="traffic",
        severity=3,
        lat=12.926,
        lon=77.683,
        geo_confidence=0.9,
        h3_r8="886189255bfffff",
    )
    inc_fast = detector.ingest(tk_fast)
    assert inc_fast is not None
    assert inc_fast.reinvestigate is False

    # At t0 + 12 min (6 min after last trigger at t0+6 min): reinvestigate must be True
    tk_delayed = Ticket(
        id="t-deb-delayed",
        ts=t0 + timedelta(minutes=12),
        channel="web",
        lang="en",
        text_original="delayed water",
        text_en="delayed water",
        category="sewage",
        severity=3,
        lat=12.926,
        lon=77.683,
        geo_confidence=0.9,
        h3_r8="886189255bfffff",
    )
    inc_delayed = detector.ingest(tk_delayed)
    assert inc_delayed is not None
    assert inc_delayed.reinvestigate is True
