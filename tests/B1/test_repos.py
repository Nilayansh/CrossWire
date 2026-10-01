import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import sessionmaker

from app.contracts.models import Ticket, Incident, Evidence
from app.contracts.keys import EvidenceKey
from app.stubs.in_memory_repos import InMemoryTicketRepo, InMemoryIncidentRepo, InMemoryEvidenceRepo
from app.db.engine import get_engine, init_db
from app.db.repos import SqlTicketRepo, SqlIncidentRepo, SqlEvidenceRepo


@pytest.fixture(params=["in_memory", "sql"])
def ticket_repo(request):
    if request.param == "in_memory":
        return InMemoryTicketRepo()
    else:
        eng = get_engine("sqlite:///:memory:")
        init_db(eng)
        return SqlTicketRepo(sessionmaker(bind=eng))


@pytest.fixture(params=["in_memory", "sql"])
def incident_repo(request):
    if request.param == "in_memory":
        return InMemoryIncidentRepo()
    else:
        eng = get_engine("sqlite:///:memory:")
        init_db(eng)
        return SqlIncidentRepo(sessionmaker(bind=eng))


@pytest.fixture(params=["in_memory", "sql"])
def evidence_repo(request):
    if request.param == "in_memory":
        return InMemoryEvidenceRepo()
    else:
        eng = get_engine("sqlite:///:memory:")
        init_db(eng)
        return SqlEvidenceRepo(sessionmaker(bind=eng))


def test_ticket_repo_contract(ticket_repo):
    t0 = datetime(2026, 9, 5, 7, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 9, 5, 7, 30, 0, tzinfo=timezone.utc)
    t_out = datetime(2026, 9, 5, 8, 30, 0, tzinfo=timezone.utc)

    ticket_in = Ticket(
        id="t-1",
        ts=t1,
        channel="telegram",
        lang="en",
        text_original="waterlogging",
        text_en="waterlogging",
        category="waterlogging",
        severity=4,
        lat=12.926,
        lon=77.683,
        geo_confidence=0.9,
        h3_r8="886189255bfffff",
    )
    ticket_outside_time = Ticket(
        id="t-2",
        ts=t_out,
        channel="web",
        lang="en",
        text_original="traffic",
        text_en="traffic",
        category="traffic",
        severity=3,
        lat=12.926,
        lon=77.683,
        geo_confidence=0.9,
        h3_r8="886189255bfffff",
    )
    ticket_outside_cell = Ticket(
        id="t-3",
        ts=t1,
        channel="web",
        lang="en",
        text_original="other cell",
        text_en="other cell",
        category="waterlogging",
        severity=2,
        lat=13.0,
        lon=77.5,
        geo_confidence=0.9,
        h3_r8="886189254dfffff",
    )

    ticket_repo.add(ticket_in)
    ticket_repo.add(ticket_outside_time)
    ticket_repo.add(ticket_outside_cell)

    window_results = ticket_repo.window(
        cells=["886189255bfffff"],
        t0=t0,
        t1=t1 + timedelta(minutes=10),
    )

    assert len(window_results) == 1
    assert window_results[0].id == "t-1"


def test_incident_repo_contract(incident_repo):
    now = datetime(2026, 9, 5, 7, 30, 0, tzinfo=timezone.utc)
    inc = Incident(
        id="inc-001",
        opened_at=now,
        status="open",
        ticket_ids=["t-1", "t-2"],
        centroid=(12.926, 77.683),
        cells=["886189255bfffff"],
        category_mix={"waterlogging": 2},
        reinvestigate=True,
    )

    incident_repo.upsert(inc)

    fetched = incident_repo.get("inc-001")
    assert fetched is not None
    assert fetched.id == "inc-001"
    assert fetched.status == "open"
    assert fetched.centroid == (12.926, 77.683)
    assert fetched.category_mix == {"waterlogging": 2}
    assert fetched.reinvestigate is True

    open_incs = incident_repo.open()
    assert len(open_incs) == 1
    assert open_incs[0].id == "inc-001"

    # Update to closed
    inc.status = "closed"
    incident_repo.upsert(inc)

    open_after_close = incident_repo.open()
    assert len(open_after_close) == 0


def test_evidence_repo_contract(evidence_repo):
    now = datetime(2026, 9, 5, 7, 30, 0, tzinfo=timezone.utc)
    ev = Evidence(
        id="ev-001",
        tool="rainfall",
        ts=now,
        summary="Rainfall exceeded 40mm/hr",
        keys=[EvidenceKey.RAIN_GT_40],
        source="open-meteo",
        provenance="real",
        raw={"hourly_rain": 42.5},
    )

    evidence_repo.add(ev)
    evidence_repo.link_incident("inc-001", "ev-001")

    linked = evidence_repo.for_incident("inc-001")
    assert len(linked) == 1
    assert linked[0].id == "ev-001"
    assert linked[0].tool == "rainfall"
    assert EvidenceKey.RAIN_GT_40 in linked[0].keys
    assert linked[0].raw["hourly_rain"] == 42.5

    # Other incident has no linked evidence
    empty = evidence_repo.for_incident("inc-other")
    assert len(empty) == 0
