from datetime import datetime
from typing import Protocol, runtime_checkable, Optional
from app.contracts.models import (
    Ticket,
    Incident,
    Evidence,
    ToolArgs,
    ToolSpec,
    Delivery,
    OutboundMessage,
)


@runtime_checkable
class TicketRepo(Protocol):
    def add(self, t: Ticket) -> None:
        """Add a ticket to storage."""
        ...

    def window(self, cells: list[str], t0: datetime, t1: datetime) -> list[Ticket]:
        """Query tickets within specified cells and time window."""
        ...


@runtime_checkable
class IncidentRepo(Protocol):
    def upsert(self, i: Incident) -> None:
        """Insert or update an incident."""
        ...

    def get(self, id: str) -> Optional[Incident]:
        """Fetch an incident by id."""
        ...

    def open(self) -> list[Incident]:
        """Fetch all currently open/active incidents."""
        ...


@runtime_checkable
class EvidenceRepo(Protocol):
    def add(self, e: Evidence) -> None:
        """Add an evidence item to storage."""
        ...

    def for_incident(self, incident_id: str) -> list[Evidence]:
        """Fetch all evidence linked to an incident."""
        ...


@runtime_checkable
class ToolRegistry(Protocol):
    def specs(self) -> list[ToolSpec]:
        """List all available tool specifications."""
        ...

    def run(self, name: str, args: ToolArgs) -> Evidence:
        """Execute a tool by name with arguments and return Evidence."""
        ...


@runtime_checkable
class Notifier(Protocol):
    def send(self, dept: str, message: OutboundMessage) -> Delivery:
        """Send outbound notification to a department channel."""
        ...


@runtime_checkable
class ClusterDetector(Protocol):
    def ingest(self, t: Ticket) -> Optional[Incident]:
        """Ingest a ticket and emit or update an Incident if threshold met."""
        ...
