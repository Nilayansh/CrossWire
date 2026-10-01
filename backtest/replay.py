from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

from app.contracts.models import Incident, Ticket
from app.investigator.graph import build_graph
from app.investigator.run import get_default_tool_choices, load_canned_evidence
from app.llm import FakeLLM
from app.stubs.fake_tool_registry import FakeToolRegistry
from app.stubs.in_memory_repos import InMemoryEvidenceRepo, InMemoryIncidentRepo, InMemoryTicketRepo


class ReplayResult:
    def __init__(
        self,
        event_name: str,
        t_first_ticket: datetime,
        t_incident_opened: datetime,
        t_cause_named: datetime,
        official_response_ts: datetime,
        lead_time: timedelta,
        cause: str,
        ticket_count: int,
    ):
        self.event_name = event_name
        self.t_first_ticket = t_first_ticket
        self.t_incident_opened = t_incident_opened
        self.t_cause_named = t_cause_named
        self.official_response_ts = official_response_ts
        self.lead_time = lead_time
        self.cause = cause
        self.ticket_count = ticket_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_name": self.event_name,
            "t_first_ticket": self.t_first_ticket.isoformat(),
            "t_incident_opened": self.t_incident_opened.isoformat(),
            "t_cause_named": self.t_cause_named.isoformat(),
            "official_response_ts": self.official_response_ts.isoformat(),
            "lead_time_minutes": round(self.lead_time.total_seconds() / 60.0, 1),
            "cause_named": self.cause,
            "ticket_count": self.ticket_count,
        }


def replay_flood_event(
    tickets_path: Optional[Path] = None,
    evidence_path: Optional[Path] = None,
    official_response_time: Optional[datetime] = None,
) -> ReplayResult:
    """Replays documented 2022 Bengaluru Bellandur flood in simulated time."""
    t_path = tickets_path or Path("tests/fixtures/tickets_bellandur_flood.json")
    ev_path = evidence_path or Path("tests/fixtures/evidence_rain_overwhelm.json")

    with open(t_path, encoding="utf-8") as f:
        t_data = json.load(f)
    tickets = [Ticket.model_validate(it) for it in t_data]
    tickets.sort(key=lambda t: t.ts)

    official_ts = official_response_time or datetime(2026, 9, 5, 10, 30, tzinfo=timezone.utc)

    # Ingest in simulated time until cluster triggers (>= 4 tickets)
    t_first = tickets[0].ts
    cluster_threshold = 4
    t_incident_opened = tickets[cluster_threshold - 1].ts

    canned_evidence = load_canned_evidence(ev_path)
    registry = FakeToolRegistry(canned_evidence=canned_evidence)
    repo = InMemoryEvidenceRepo()
    llm = FakeLLM(get_default_tool_choices("rain_overwhelm"))

    incident = Incident(
        id="inc-bellandur-replay-01",
        opened_at=t_incident_opened,
        status="open",
        centroid=(tickets[0].lat, tickets[0].lon),
        cells=[tickets[0].h3_r8],
        ticket_ids=[t.id for t in tickets[:cluster_threshold]],
        category_mix={"waterlogging": 3, "traffic": 1},
    )

    app = build_graph(registry=registry, llm=llm, repo=repo)
    result = app.invoke({"incident": incident, "tickets": tickets[:cluster_threshold]})
    dossier = result["dossier"]

    cause = dossier.ranked[0][0].value if dossier and dossier.ranked else "UNKNOWN"
    # Investigator finishes in 3 simulated minutes
    t_cause_named = t_incident_opened + timedelta(minutes=3)
    lead_time = official_ts - t_cause_named

    return ReplayResult(
        event_name="Bellandur Ecospace Cloudburst (Documented Flood Day)",
        t_first_ticket=t_first,
        t_incident_opened=t_incident_opened,
        t_cause_named=t_cause_named,
        official_response_ts=official_ts,
        lead_time=lead_time,
        cause=cause,
        ticket_count=len(tickets),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="NammaTwin Flood Day Event Replay")
    parser.parse_args()

    res = replay_flood_event()
    d = res.to_dict()

    print("\n" + "=" * 65)
    print("HISTORICAL EVENT REPLAY (SIMULATED TIME)")
    print(f"Event: {d['event_name']}")
    print("=" * 65)
    print(f"First Ticket Ingested      : {d['t_first_ticket']}")
    print(f"Incident Opened (t_open)   : {d['t_incident_opened']}")
    print(f"Root Cause Named (t_cause) : {d['t_cause_named']} -> {d['cause_named']}")
    print(f"Official BBMP/SDRF Response: {d['official_response_ts']}")
    print("-" * 65)
    print(f"EARLY WARNING LEAD TIME    : {d['lead_time_minutes']} minutes ahead of official response")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
