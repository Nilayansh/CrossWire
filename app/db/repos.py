from datetime import datetime, timezone
from typing import Optional, Callable
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.contracts.interfaces import TicketRepo, IncidentRepo, EvidenceRepo
from app.contracts.models import Ticket, Incident, Evidence
from app.db.engine import SessionLocal, init_db
from app.db.models import TicketModel, IncidentModel, EvidenceModel, IncidentEvidenceModel


@contextmanager
def _session_scope(session_factory: Callable[[], Session]):
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _to_naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class SqlTicketRepo(TicketRepo):
    """SQLAlchemy implementation of TicketRepo."""

    def __init__(self, session_factory: Optional[Callable[[], Session]] = None):
        init_db()
        self._session_factory = session_factory or SessionLocal

    def add(self, t: Ticket) -> None:
        with _session_scope(self._session_factory) as session:
            model = session.get(TicketModel, t.id)
            if model is None:
                session.add(TicketModel.from_pydantic(t))
            else:
                # Update existing record
                new_model = TicketModel.from_pydantic(t)
                for col in TicketModel.__table__.columns.keys():
                    setattr(model, col, getattr(new_model, col))

    def window(self, cells: list[str], t0: datetime, t1: datetime) -> list[Ticket]:
        if not cells:
            return []
        t0_naive = _to_naive_utc(t0)
        t1_naive = _to_naive_utc(t1)

        with self._session_factory() as session:
            stmt = (
                select(TicketModel)
                .where(
                    and_(
                        TicketModel.h3_r8.in_(cells),
                        TicketModel.ts >= t0_naive,
                        TicketModel.ts <= t1_naive,
                    )
                )
                .order_by(TicketModel.ts.asc())
            )
            records = session.scalars(stmt).all()
            return [r.to_pydantic() for r in records]

    def get(self, id: str) -> Optional[Ticket]:
        with self._session_factory() as session:
            record = session.get(TicketModel, id)
            return record.to_pydantic() if record else None

    def all(self) -> list[Ticket]:
        with self._session_factory() as session:
            stmt = select(TicketModel).order_by(TicketModel.ts.asc())
            records = session.scalars(stmt).all()
            return [r.to_pydantic() for r in records]


class SqlIncidentRepo(IncidentRepo):
    """SQLAlchemy implementation of IncidentRepo."""

    def __init__(self, session_factory: Optional[Callable[[], Session]] = None):
        self._session_factory = session_factory or SessionLocal

    def upsert(self, i: Incident) -> None:
        with _session_scope(self._session_factory) as session:
            model = session.get(IncidentModel, i.id)
            if model is None:
                session.add(IncidentModel.from_pydantic(i))
            else:
                new_model = IncidentModel.from_pydantic(i)
                for col in IncidentModel.__table__.columns.keys():
                    setattr(model, col, getattr(new_model, col))

    def get(self, id: str) -> Optional[Incident]:
        with self._session_factory() as session:
            record = session.get(IncidentModel, id)
            return record.to_pydantic() if record else None

    def open(self) -> list[Incident]:
        with self._session_factory() as session:
            stmt = (
                select(IncidentModel)
                .where(IncidentModel.status.not_in(["closed", "resolving"]))
                .order_by(IncidentModel.opened_at.desc())
            )
            records = session.scalars(stmt).all()
            return [r.to_pydantic() for r in records]

    def all(self) -> list[Incident]:
        with self._session_factory() as session:
            stmt = select(IncidentModel).order_by(IncidentModel.opened_at.desc())
            records = session.scalars(stmt).all()
            return [r.to_pydantic() for r in records]


class SqlEvidenceRepo(EvidenceRepo):
    """SQLAlchemy implementation of EvidenceRepo."""

    def __init__(self, session_factory: Optional[Callable[[], Session]] = None):
        self._session_factory = session_factory or SessionLocal

    def add(self, e: Evidence) -> None:
        with _session_scope(self._session_factory) as session:
            model = session.get(EvidenceModel, e.id)
            if model is None:
                session.add(EvidenceModel.from_pydantic(e))
            else:
                new_model = EvidenceModel.from_pydantic(e)
                for col in EvidenceModel.__table__.columns.keys():
                    setattr(model, col, getattr(new_model, col))

    def link_incident(self, incident_id: str, evidence_id: str) -> None:
        with _session_scope(self._session_factory) as session:
            # Avoid duplicate links
            stmt = select(IncidentEvidenceModel).where(
                and_(
                    IncidentEvidenceModel.incident_id == incident_id,
                    IncidentEvidenceModel.evidence_id == evidence_id,
                )
            )
            existing = session.scalars(stmt).first()
            if not existing:
                session.add(IncidentEvidenceModel(incident_id=incident_id, evidence_id=evidence_id))

    def for_incident(self, incident_id: str) -> list[Evidence]:
        with self._session_factory() as session:
            stmt = (
                select(EvidenceModel)
                .join(
                    IncidentEvidenceModel,
                    EvidenceModel.id == IncidentEvidenceModel.evidence_id,
                )
                .where(IncidentEvidenceModel.incident_id == incident_id)
                .order_by(EvidenceModel.ts.asc())
            )
            records = session.scalars(stmt).all()
            return [r.to_pydantic() for r in records]

    def get(self, id: str) -> Optional[Evidence]:
        with self._session_factory() as session:
            record = session.get(EvidenceModel, id)
            return record.to_pydantic() if record else None

    def all(self) -> list[Evidence]:
        with self._session_factory() as session:
            stmt = select(EvidenceModel).order_by(EvidenceModel.ts.asc())
            records = session.scalars(stmt).all()
            return [r.to_pydantic() for r in records]
