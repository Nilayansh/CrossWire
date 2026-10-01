from __future__ import annotations

from typing import Any, Optional, TypedDict
from pydantic import BaseModel, Field

from app.contracts.keys import HypothesisID
from app.contracts.models import Dossier, Evidence, Incident, Ticket


class ToolChoice(BaseModel):
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    why: str


class InvestigatorState(TypedDict, total=False):
    incident: Incident
    tickets: list[Ticket]
    hypotheses: dict[HypothesisID, float]  # log-odds state
    posteriors: dict[HypothesisID, float]  # normalized probabilities
    evidence: list[Evidence]
    active_evidence: Optional[Evidence]
    used_tools: list[str]
    step: int
    max_steps: int
    tool_choice: Optional[ToolChoice]
    should_stop: bool
    stop_reason: str
    trace: list[dict[str, Any]]
    dossier: Optional[Dossier]
    error_count: int
