from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.schemas import (
    HealthResponse,
    IncidentDetailResponse,
    TicketIngestResponse,
    VerifyResponse,
)
from app.contracts.keys import HypothesisID, EvidenceKey
from app.contracts.models import Action, Decision, Dossier, Evidence, Incident, Ticket


def load_fixture_tickets() -> list[Ticket]:
    path = Path("tests/fixtures/tickets_bellandur_flood.json")
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Ticket.model_validate(item) for item in data]


def load_fixture_evidence() -> list[Evidence]:
    path = Path("tests/fixtures/evidence_power_led_stp.json")
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Evidence.model_validate(item) for item in data]


class MockBackend:
    """In-memory mock backend provider returning validated contract models."""

    def __init__(self) -> None:
        self.tickets: list[Ticket] = load_fixture_tickets()
        self.evidence: list[Evidence] = load_fixture_evidence()
        self._init_data()

    def _init_data(self) -> None:
        now = datetime.now(timezone.utc)
        self.incidents: dict[str, Incident] = {
            "inc-bellandur-01": Incident(
                id="inc-bellandur-01",
                opened_at=now,
                status="awaiting_approval",
                centroid=(12.928, 77.683),
                cells=["886189255bfffff", "8861892559fffff"],
                ticket_ids=[t.id for t in self.tickets] or ["t-001", "t-002", "t-003", "t-004"],
                category_mix={
                    "waterlogging": 8,
                    "traffic": 3,
                    "power": 2,
                    "sewage": 1,
                },
                reinvestigate=False,
            ),
            "inc-kadubeesanahalli-02": Incident(
                id="inc-kadubeesanahalli-02",
                opened_at=now,
                status="investigating",
                centroid=(12.935, 77.692),
                cells=["886189255bfffff"],
                ticket_ids=["t-004", "t-005"],
                category_mix={"power": 3, "sewage": 2},
                reinvestigate=True,
            ),
        }

        self.dossiers: dict[str, Dossier] = {
            "inc-bellandur-01": Dossier(
                incident_id="inc-bellandur-01",
                ranked=[
                    (HypothesisID.POWER_LED_STP_OVERFLOW, 0.892),
                    (HypothesisID.RAIN_OVERWHELM, 0.065),
                    (HypothesisID.DRAIN_BLOCKAGE, 0.024),
                    (HypothesisID.PIPE_BURST, 0.011),
                    (HypothesisID.LAKE_OVERFLOW, 0.005),
                    (HypothesisID.TRAFFIC_ONLY, 0.003),
                ],
                evidence=self.evidence,
                conclusive=True,
                stop_reason="Posterior threshold >= 0.75 and margin >= 0.20 reached at step 3",
                trace=[
                    {
                        "step": 1,
                        "tool": "history",
                        "why": "Analyze ticket temporal lags and category progression",
                        "evidence_id": "ev-stp-01",
                        "top_hypothesis": "POWER_LED_STP_OVERFLOW",
                        "posterior": 0.54,
                    },
                    {
                        "step": 2,
                        "tool": "outage",
                        "why": "Check 11kV feeder tripping records around substation",
                        "evidence_id": "ev-stp-02",
                        "top_hypothesis": "POWER_LED_STP_OVERFLOW",
                        "posterior": 0.78,
                    },
                    {
                        "step": 3,
                        "tool": "osm",
                        "why": "Locate nearest large wastewater treatment facility",
                        "evidence_id": "ev-stp-03",
                        "top_hypothesis": "POWER_LED_STP_OVERFLOW",
                        "posterior": 0.892,
                    },
                ],
            )
        }

        self.actions: dict[str, list[Action]] = {
            "inc-bellandur-01": [
                Action(
                    id="act-001",
                    dept="power_utility",
                    action="BESCOM Emergency Response: Reset tripped Kadubeesanahalli 11kV substation breaker (Feeder F-KADU-04) and restore STP pump backup power.",
                    priority="P1",
                    rationale="BESCOM power outage complaints preceded sewage overflow by 45 minutes; feeder trip directly paralyzed STP suction pumps.",
                    evidence_ids=["ev-stp-01", "ev-stp-02"],
                    confidence=0.92,
                    target_latlon=(12.934, 77.692),
                    needs_field_verification=False,
                ),
                Action(
                    id="act-002",
                    dept="sewerage",
                    action="BWSSB Quick-Reaction: Dispatch 2x 100 HP diesel-driven suction pumps to ORR-Ecospace junction to relieve backpressure in primary wet well.",
                    priority="P1",
                    rationale="STP wet well overflow spilling raw effluent onto Outer Ring Road service corridor toward Bellandur lake inlet.",
                    evidence_ids=["ev-stp-01", "ev-stp-03"],
                    confidence=0.89,
                    target_latlon=(12.928, 77.684),
                    needs_field_verification=False,
                ),
                Action(
                    id="act-003",
                    dept="traffic_police",
                    action="BTP Traffic Alert: Close flooded ORR service lane near Central Mall; divert inbound traffic via Marathahalli flyover loop to Sarjapur Rd.",
                    priority="P2",
                    rationale="Traffic slowdown ratio 0.35 with queue length > 2.5 km. Hospital route along Sakra World Hospital impeded.",
                    evidence_ids=["ev-stp-01"],
                    confidence=0.85,
                    target_latlon=(12.926, 77.683),
                    needs_field_verification=False,
                ),
            ]
        }

        self.decisions: list[Decision] = []

    def get_incidents(self) -> list[Incident]:
        return list(self.incidents.values())

    def get_incident_detail(self, incident_id: str) -> IncidentDetailResponse:
        inc = self.incidents.get(incident_id)
        if not inc:
            raise KeyError(f"Incident {incident_id} not found")
        dossier = self.dossiers.get(incident_id)
        actions = self.actions.get(incident_id, [])
        return IncidentDetailResponse(
            incident=inc,
            status=inc.status,
            dossier=dossier,
            actions=actions,
        )

    def ingest_ticket(self, ticket: Ticket) -> TicketIngestResponse:
        self.tickets.append(ticket)
        # Attach to primary incident
        inc = self.incidents.get("inc-bellandur-01")
        if inc:
            inc.ticket_ids.append(ticket.id)
            inc.category_mix[ticket.category] = inc.category_mix.get(ticket.category, 0) + 1
            return TicketIngestResponse(ticket_id=ticket.id, incident_id=inc.id)
        return TicketIngestResponse(ticket_id=ticket.id)

    def submit_decision(self, incident_id: str, decision: Decision) -> dict[str, Any]:
        self.decisions.append(decision)
        inc = self.incidents.get(incident_id)
        if inc:
            inc.status = "dispatched"
        return {
            "status": "dispatched",
            "incident_id": incident_id,
            "approved": decision.approved_action_ids,
            "dispatched_at": datetime.now(timezone.utc).isoformat(),
        }

    def verify_incident(self, incident_id: str, fast_forward_min: int = 45) -> VerifyResponse:
        inc = self.incidents.get(incident_id)
        if not inc:
            raise KeyError(f"Incident {incident_id} not found")
        inc.status = "resolving"
        return VerifyResponse(
            incident_id=incident_id,
            status="resolving",
            verify_result="resolving",
            fast_forward_min=fast_forward_min,
        )

    def get_trace(self, incident_id: str) -> list[dict[str, Any]]:
        dossier = self.dossiers.get(incident_id)
        if dossier and dossier.trace:
            return dossier.trace
        return []


def create_mock_app() -> FastAPI:
    """FastAPI application serving mock fixture responses matching openapi.json."""
    mock_app = FastAPI(title="NammaTwin Mock API", version="0.1.0")
    backend = MockBackend()

    @mock_app.get("/health", response_model=HealthResponse)
    def health():
        return HealthResponse()

    @mock_app.get("/incidents", response_model=list[Incident])
    def list_incidents():
        return backend.get_incidents()

    @mock_app.get("/incidents/{incident_id}", response_model=IncidentDetailResponse)
    def get_incident(incident_id: str):
        try:
            return backend.get_incident_detail(incident_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Incident not found")

    @mock_app.post("/tickets", response_model=TicketIngestResponse)
    def ingest_ticket(ticket: Ticket):
        return backend.ingest_ticket(ticket)

    @mock_app.post("/incidents/{incident_id}/decision")
    def submit_decision(incident_id: str, decision: Decision):
        return backend.submit_decision(incident_id, decision)

    @mock_app.post("/incidents/{incident_id}/verify", response_model=VerifyResponse)
    def verify(incident_id: str, fast_forward_min: int = Query(45)):
        try:
            return backend.verify_incident(incident_id, fast_forward_min)
        except KeyError:
            raise HTTPException(status_code=404, detail="Incident not found")

    @mock_app.get("/incidents/{incident_id}/stream")
    def stream_trace(incident_id: str):
        trace = backend.get_trace(incident_id)

        def gen():
            for t in trace:
                yield f"data: {json.dumps(t)}\n\n"
            yield "event: end\ndata: {}\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    return mock_app


app = create_mock_app()
