from datetime import datetime
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field
from app.contracts.keys import HypothesisID, EvidenceKey


class Ticket(BaseModel):
    id: str
    ts: datetime
    channel: Literal["telegram", "web", "synthetic"]
    lang: str
    text_original: str
    text_en: str
    category: Literal[
        "waterlogging",
        "power",
        "sewage",
        "water_supply",
        "traffic",
        "garbage_debris",
        "road_damage",
        "other",
    ]
    severity: int  # 1-5
    lat: float
    lon: float
    geo_confidence: float
    h3_r8: str
    photo_depth: Optional[Literal["ankle", "knee", "waist", "vehicle"]] = None
    reporter_chat_id: Optional[str] = None
    is_synthetic: bool = False


class Incident(BaseModel):
    id: str
    opened_at: datetime
    status: Literal[
        "open",
        "investigating",
        "awaiting_approval",
        "dispatched",
        "resolving",
        "closed",
        "escalated",
    ] = "open"
    ticket_ids: list[str] = Field(default_factory=list)
    centroid: tuple[float, float]
    cells: list[str] = Field(default_factory=list)
    category_mix: dict[str, int] = Field(default_factory=dict)
    reinvestigate: bool = False


class Evidence(BaseModel):
    id: str
    tool: str
    ts: datetime
    summary: str
    keys: list[EvidenceKey]
    source: str
    provenance: Literal["real", "simulated", "derived"]
    raw: dict[str, Any] = Field(default_factory=dict)


class ToolArgs(BaseModel):
    incident_id: str
    lat: float
    lon: float
    t0: datetime
    t1: datetime
    cells: list[str] = Field(default_factory=list)


class ToolSpec(BaseModel):
    name: str
    description: str
    args_model: type[ToolArgs]
    provenance: Literal["real", "simulated", "derived"]
    discriminates: list[HypothesisID]


class Hypothesis(BaseModel):
    id: HypothesisID
    expected_signature: str
    departments: list[str]


class Dossier(BaseModel):
    incident_id: str
    ranked: list[tuple[HypothesisID, float]]  # [(HypothesisID, posterior_probability)]
    evidence: list[Evidence] = Field(default_factory=list)
    conclusive: bool
    stop_reason: str
    trace: list[dict[str, Any]] = Field(default_factory=list)


class Action(BaseModel):
    dept: Literal[
        "stormwater",
        "power_utility",
        "sewerage",
        "traffic_police",
        "solid_waste",
        "water_board",
    ]
    action: str
    target_latlon: Optional[tuple[float, float]] = None
    priority: Literal["P1", "P2", "P3"]
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float
    needs_field_verification: bool = False
    id: Optional[str] = None


class Decision(BaseModel):
    incident_id: str
    approved_action_ids: list[str] = Field(default_factory=list)
    edits: dict[str, str] = Field(default_factory=dict)
    rejected: dict[str, str] = Field(default_factory=dict)
    officer: str


class Delivery(BaseModel):
    incident_id: str
    action_id: str
    channel: Literal["telegram", "email", "sms", "console"]
    status: Literal["sent", "failed", "dry_run"]
    sent_at: datetime
    error: Optional[str] = None


class OutboundMessage(BaseModel):
    recipient: str
    subject: Optional[str] = None
    body: str
    metadata: dict[str, Any] = Field(default_factory=dict)
