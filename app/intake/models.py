from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class RawInput(BaseModel):
    """Raw citizen submission before intake normalization."""
    channel: Literal["telegram", "web", "synthetic"] = "telegram"
    text: Optional[str] = None
    voice_bytes: Optional[bytes] = None
    photo_bytes: Optional[bytes] = None
    pin: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    reporter_chat_id: Optional[str] = None
    ts: Optional[datetime] = None


class TicketDraft(BaseModel):
    """Structured extraction output from LLM."""
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
    severity: int = Field(ge=1, le=5)
    location_hint: Optional[str] = None
    text_en: str


class DepthEstimate(BaseModel):
    """Multimodal vision output for flood water depth."""
    bucket: Optional[Literal["ankle", "knee", "waist", "vehicle"]] = None
    confidence: float = 0.85
