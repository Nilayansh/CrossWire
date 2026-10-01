from typing import Optional
from app.contracts.models import Ticket, Incident
from app.contracts.interfaces import TicketRepo, ClusterDetector
from app.intake.models import RawInput
from app.intake.extract import to_ticket
from app.db.repos import SqlTicketRepo


class IntakePipeline:
    """Intake pipeline turning raw citizen reports into tickets and triggering clustering."""

    def __init__(
        self,
        ticket_repo: Optional[TicketRepo] = None,
        cluster_detector: Optional[ClusterDetector] = None,
        llm=None,
    ):
        self.ticket_repo = ticket_repo or SqlTicketRepo()
        self.cluster_detector = cluster_detector
        self.llm = llm

    def process(self, raw: RawInput) -> tuple[Ticket, Optional[Incident]]:
        """Process a raw submission into a Ticket, save it, and ingest into cluster detector."""
        ticket = to_ticket(raw, llm=self.llm)
        self.ticket_repo.add(ticket)

        incident = None
        if self.cluster_detector is not None:
            incident = self.cluster_detector.ingest(ticket)

        return ticket, incident
