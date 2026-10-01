from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
)
from app.db.engine import Base
from app.contracts.models import Ticket, Incident, Evidence
from app.contracts.keys import EvidenceKey


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class TicketModel(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    channel = Column(String, nullable=False)
    lang = Column(String, nullable=False)
    text_original = Column(Text, nullable=False)
    text_en = Column(Text, nullable=False)
    category = Column(String, nullable=False, index=True)
    severity = Column(Integer, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    geo_confidence = Column(Float, nullable=False)
    h3_r8 = Column(String, nullable=False, index=True)
    photo_depth = Column(String, nullable=True)
    reporter_chat_id = Column(String, nullable=True)
    is_synthetic = Column(Boolean, default=False)

    def to_pydantic(self) -> Ticket:
        return Ticket(
            id=self.id,
            ts=_ensure_utc(self.ts),
            channel=self.channel,
            lang=self.lang,
            text_original=self.text_original,
            text_en=self.text_en,
            category=self.category,
            severity=self.severity,
            lat=self.lat,
            lon=self.lon,
            geo_confidence=self.geo_confidence,
            h3_r8=self.h3_r8,
            photo_depth=self.photo_depth,
            reporter_chat_id=self.reporter_chat_id,
            is_synthetic=self.is_synthetic,
        )

    @classmethod
    def from_pydantic(cls, t: Ticket) -> "TicketModel":
        ts_val = t.ts
        if ts_val.tzinfo is not None:
            ts_val = ts_val.astimezone(timezone.utc).replace(tzinfo=None)
        return cls(
            id=t.id,
            ts=ts_val,
            channel=t.channel,
            lang=t.lang,
            text_original=t.text_original,
            text_en=t.text_en,
            category=t.category,
            severity=t.severity,
            lat=t.lat,
            lon=t.lon,
            geo_confidence=t.geo_confidence,
            h3_r8=t.h3_r8,
            photo_depth=t.photo_depth,
            reporter_chat_id=t.reporter_chat_id,
            is_synthetic=t.is_synthetic,
        )


class IncidentModel(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, index=True)
    opened_at = Column(DateTime, nullable=False, index=True)
    status = Column(String, default="open", nullable=False, index=True)
    ticket_ids = Column(JSON, default=list, nullable=False)
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    cells = Column(JSON, default=list, nullable=False)
    category_mix = Column(JSON, default=dict, nullable=False)
    reinvestigate = Column(Boolean, default=False, nullable=False)

    def to_pydantic(self) -> Incident:
        return Incident(
            id=self.id,
            opened_at=_ensure_utc(self.opened_at),
            status=self.status,
            ticket_ids=list(self.ticket_ids or []),
            centroid=(self.centroid_lat, self.centroid_lon),
            cells=list(self.cells or []),
            category_mix=dict(self.category_mix or {}),
            reinvestigate=self.reinvestigate,
        )

    @classmethod
    def from_pydantic(cls, i: Incident) -> "IncidentModel":
        opened_at_val = i.opened_at
        if opened_at_val.tzinfo is not None:
            opened_at_val = opened_at_val.astimezone(timezone.utc).replace(tzinfo=None)
        return cls(
            id=i.id,
            opened_at=opened_at_val,
            status=i.status,
            ticket_ids=list(i.ticket_ids),
            centroid_lat=i.centroid[0],
            centroid_lon=i.centroid[1],
            cells=list(i.cells),
            category_mix=dict(i.category_mix),
            reinvestigate=i.reinvestigate,
        )


class EvidenceModel(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, index=True)
    tool = Column(String, nullable=False)
    ts = Column(DateTime, nullable=False)
    summary = Column(Text, nullable=False)
    keys = Column(JSON, default=list, nullable=False)
    source = Column(String, nullable=False)
    provenance = Column(String, nullable=False)
    raw = Column(JSON, default=dict, nullable=False)

    def to_pydantic(self) -> Evidence:
        parsed_keys = []
        for k in self.keys or []:
            try:
                parsed_keys.append(EvidenceKey(k))
            except ValueError:
                pass
        return Evidence(
            id=self.id,
            tool=self.tool,
            ts=_ensure_utc(self.ts),
            summary=self.summary,
            keys=parsed_keys,
            source=self.source,
            provenance=self.provenance,
            raw=dict(self.raw or {}),
        )

    @classmethod
    def from_pydantic(cls, e: Evidence) -> "EvidenceModel":
        ts_val = e.ts
        if ts_val.tzinfo is not None:
            ts_val = ts_val.astimezone(timezone.utc).replace(tzinfo=None)
        serialized_keys = [k.value if isinstance(k, EvidenceKey) else str(k) for k in e.keys]
        return cls(
            id=e.id,
            tool=e.tool,
            ts=ts_val,
            summary=e.summary,
            keys=serialized_keys,
            source=e.source,
            provenance=e.provenance,
            raw=dict(e.raw or {}),
        )


class IncidentEvidenceModel(Base):
    __tablename__ = "incident_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String, nullable=False, index=True)
    evidence_id = Column(String, nullable=False, index=True)
