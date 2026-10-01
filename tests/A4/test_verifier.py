from datetime import datetime, timezone
import pytest

from app.contracts.models import Incident, Ticket
from app.verifier.verifier import assess


def sample_incident() -> Incident:
    return Incident(
        id="inc-verif-01",
        opened_at=datetime.now(timezone.utc),
        status="awaiting_approval",
        centroid=(12.928, 77.682),
        cells=["886189255bfffff"],
        ticket_ids=["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"],  # 8 initial tickets
    )


def test_assess_resolving():
    """Ticket count decays by > 50% and rainfall stopped -> resolving."""
    inc = sample_incident()
    # 2 new tickets (< 50% of 8) and rain 1.2 mm/hr (< 5.0), traffic recovered to 0.75
    new_tickets = [
        Ticket(
            id="t-new-1",
            ts=datetime.now(timezone.utc),
            channel="web",
            lang="en",
            text_original="Water receded slightly",
            text_en="Water receded slightly",
            category="waterlogging",
            severity=2,
            lat=12.928,
            lon=77.682,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        )
    ]
    status = assess(
        incident=inc,
        new_tickets=new_tickets,
        rainfall_now=1.2,
        traffic_ratio=0.75,
    )
    assert status == "resolving"


def test_assess_escalated_heavy_rain():
    """Persistent heavy rain or incoming tickets -> escalated."""
    inc = sample_incident()
    # Heavy rain >= 25 mm/hr and low traffic ratio
    status = assess(
        incident=inc,
        new_tickets=[],
        rainfall_now=35.0,
        traffic_ratio=0.25,
    )
    assert status == "escalated"


def test_assess_escalated_ticket_surge():
    """Surge of new severe tickets -> escalated."""
    inc = sample_incident()
    # 10 new tickets (> initial 8)
    new_tickets = [
        Ticket(
            id=f"t-surge-{i}",
            ts=datetime.now(timezone.utc),
            channel="web",
            lang="en",
            text_original="Flooding worsening",
            text_en="Flooding worsening",
            category="waterlogging",
            severity=5,
            lat=12.928,
            lon=77.682,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        )
        for i in range(10)
    ]
    status = assess(
        incident=inc,
        new_tickets=new_tickets,
        rainfall_now=15.0,
        traffic_ratio=0.4,
    )
    assert status == "escalated"


def test_assess_closed():
    """No new tickets, dry weather, normal traffic flow -> closed."""
    inc = sample_incident()
    status = assess(
        incident=inc,
        new_tickets=[],
        rainfall_now=0.0,
        traffic_ratio=0.95,
    )
    assert status == "closed"
