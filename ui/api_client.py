from __future__ import annotations

import json
import logging
from typing import Any, Iterable, Optional

import httpx

from app.api.schemas import (
    HealthResponse,
    IncidentDetailResponse,
    TicketIngestResponse,
    VerifyResponse,
)
from app.contracts.models import Decision, Incident, Ticket
from ui.mock_api import MockBackend

logger = logging.getLogger(__name__)


def parse_sse_stream(lines: Iterable[str]) -> list[dict[str, Any]]:
    """Parse raw SSE stream lines into a list of JSON event dictionaries."""
    events: list[dict[str, Any]] = []
    current_data: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_data:
                payload = "\n".join(current_data)
                try:
                    parsed = json.loads(payload)
                    if parsed:
                        events.append(parsed)
                except json.JSONDecodeError:
                    pass
                current_data = []
            continue

        if stripped.startswith("data:"):
            data_content = stripped[len("data:") :].strip()
            current_data.append(data_content)

    if current_data:
        payload = "\n".join(current_data)
        try:
            parsed = json.loads(payload)
            if parsed:
                events.append(parsed)
        except json.JSONDecodeError:
            pass

    return events


class ApiClient:
    """HTTP client communicating with NammaTwin FastAPI endpoints."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        use_mock: bool = False,
        timeout: float = 1.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.use_mock = use_mock
        self.timeout = timeout
        self.mock_backend = MockBackend()
        self.is_mock_fallback = use_mock

    def is_healthy(self) -> bool:
        if self.use_mock:
            return True
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(f"{self.base_url}/health")
                return res.status_code == 200
        except Exception:
            return False

    def get_incidents(self) -> list[Incident]:
        if self.use_mock:
            return self.mock_backend.get_incidents()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(f"{self.base_url}/incidents")
                res.raise_for_status()
                data = res.json()
                self.is_mock_fallback = False
                return [Incident.model_validate(item) for item in data]
        except Exception as e:
            logger.warning("Falling back to mock backend for get_incidents: %s", e)
            self.is_mock_fallback = True
            return self.mock_backend.get_incidents()

    def get_incident(self, incident_id: str) -> IncidentDetailResponse:
        if self.use_mock:
            return self.mock_backend.get_incident_detail(incident_id)
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(f"{self.base_url}/incidents/{incident_id}")
                res.raise_for_status()
                self.is_mock_fallback = False
                return IncidentDetailResponse.model_validate(res.json())
        except Exception as e:
            logger.warning("Falling back to mock backend for get_incident: %s", e)
            self.is_mock_fallback = True
            return self.mock_backend.get_incident_detail(incident_id)

    def submit_decision(self, incident_id: str, decision: Decision) -> dict[str, Any]:
        if self.use_mock:
            return self.mock_backend.submit_decision(incident_id, decision)
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(
                    f"{self.base_url}/incidents/{incident_id}/decision",
                    json=decision.model_dump(mode="json"),
                )
                res.raise_for_status()
                self.is_mock_fallback = False
                return res.json()
        except Exception as e:
            logger.warning("Falling back to mock backend for submit_decision: %s", e)
            self.is_mock_fallback = True
            return self.mock_backend.submit_decision(incident_id, decision)

    def verify_incident(self, incident_id: str, fast_forward_min: int = 45) -> VerifyResponse:
        if self.use_mock:
            return self.mock_backend.verify_incident(incident_id, fast_forward_min)
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(
                    f"{self.base_url}/incidents/{incident_id}/verify?fast_forward_min={fast_forward_min}"
                )
                res.raise_for_status()
                self.is_mock_fallback = False
                return VerifyResponse.model_validate(res.json())
        except Exception as e:
            logger.warning("Falling back to mock backend for verify_incident: %s", e)
            self.is_mock_fallback = True
            return self.mock_backend.verify_incident(incident_id, fast_forward_min)

    def ingest_ticket(self, ticket: Ticket) -> TicketIngestResponse:
        if self.use_mock:
            return self.mock_backend.ingest_ticket(ticket)
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(
                    f"{self.base_url}/tickets",
                    json=ticket.model_dump(mode="json"),
                )
                res.raise_for_status()
                self.is_mock_fallback = False
                return TicketIngestResponse.model_validate(res.json())
        except Exception as e:
            logger.warning("Falling back to mock backend for ingest_ticket: %s", e)
            self.is_mock_fallback = True
            return self.mock_backend.ingest_ticket(ticket)

    def get_trace_events(self, incident_id: str) -> list[dict[str, Any]]:
        if self.use_mock:
            return self.mock_backend.get_trace(incident_id)
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(f"{self.base_url}/incidents/{incident_id}/stream")
                res.raise_for_status()
                lines = res.text.splitlines()
                return parse_sse_stream(lines)
        except Exception as e:
            logger.warning("Falling back to mock backend for get_trace_events: %s", e)
            return self.mock_backend.get_trace(incident_id)
