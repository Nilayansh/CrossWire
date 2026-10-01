from datetime import datetime
from typing import Optional
from app.contracts.models import Ticket, Incident, Evidence
from app.contracts.interfaces import TicketRepo, IncidentRepo, EvidenceRepo


class InMemoryTicketRepo(TicketRepo):
    """In-memory ticket repository for offline tests."""

    def __init__(self):
        self._tickets: dict[str, Ticket] = {}

    def add(self, t: Ticket) -> None:
        self._tickets[t.id] = t

    def window(self, cells: list[str], t0: datetime, t1: datetime) -> list[Ticket]:
        cell_set = set(cells)
        results: list[Ticket] = []
        for t in self._tickets.values():
            if t.h3_r8 in cell_set and (t0 <= t.ts <= t1):
                results.append(t)
        return results

    def all(self) -> list[Ticket]:
        return list(self._tickets.values())


class InMemoryIncidentRepo(IncidentRepo):
    """In-memory incident repository for offline tests."""

    def __init__(self):
        self._incidents: dict[str, Incident] = {}

    def upsert(self, i: Incident) -> None:
        self._incidents[i.id] = i

    def get(self, id: str) -> Optional[Incident]:
        return self._incidents.get(id)

    def open(self) -> list[Incident]:
        return [i for i in self._incidents.values() if i.status not in ("closed", "resolving")]

    def all(self) -> list[Incident]:
        return list(self._incidents.values())


class InMemoryEvidenceRepo(EvidenceRepo):
    """In-memory evidence repository for offline tests."""

    def __init__(self):
        self._evidence: dict[str, Evidence] = {}
        self._incident_map: dict[str, list[str]] = {}

    def add(self, e: Evidence) -> None:
        self._evidence[e.id] = e

    def link_incident(self, incident_id: str, evidence_id: str) -> None:
        self._incident_map.setdefault(incident_id, []).append(evidence_id)

    def for_incident(self, incident_id: str) -> list[Evidence]:
        ev_ids = self._incident_map.get(incident_id, [])
        return [self._evidence[eid] for eid in ev_ids if eid in self._evidence]

    def all(self) -> list[Evidence]:
        return list(self._evidence.values())
