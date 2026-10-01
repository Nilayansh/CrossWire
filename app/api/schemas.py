from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.contracts.models import Action, Decision, Dossier, Incident, Ticket


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TicketIngestResponse(BaseModel):
    ticket_id: str
    incident_id: Optional[str] = None
    message: str = "Ticket successfully ingested"


class IncidentDetailResponse(BaseModel):
    incident: Incident
    status: str
    dossier: Optional[Dossier] = None
    actions: list[Action] = Field(default_factory=list)
    tickets: list[Ticket] = Field(default_factory=list)


class VerifyResponse(BaseModel):
    incident_id: str
    status: str
    verify_result: str
    fast_forward_min: int
