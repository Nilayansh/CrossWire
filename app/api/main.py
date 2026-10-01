from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
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
from app.contracts.interfaces import (
    ClusterDetector,
    EvidenceRepo,
    IncidentRepo,
    Notifier,
    TicketRepo,
)
from app.contracts.models import Decision, Incident, Ticket
from app.investigator.run import get_default_tool_choices, load_canned_evidence
from app.llm import FakeLLM
from app.orchestrator.pipeline import OuterPipeline, SqliteSaver
from app.planner.planner import PlanDraft
from app.stubs.console_notifier import ConsoleNotifier
from app.stubs.fake_tool_registry import FakeToolRegistry
from app.stubs.in_memory_repos import (
    InMemoryEvidenceRepo,
    InMemoryIncidentRepo,
    InMemoryTicketRepo,
)
from app.verifier.verifier import assess


class DefaultClusterDetector:
    def __init__(self, ticket_repo: TicketRepo, incident_repo: IncidentRepo):
        self.ticket_repo = ticket_repo
        self.incident_repo = incident_repo

    def ingest(self, t: Ticket) -> Incident:
        self.ticket_repo.add(t)
        open_incs = self.incident_repo.open()
        if open_incs:
            inc = open_incs[0]
            inc.ticket_ids.append(t.id)
            self.incident_repo.upsert(inc)
            return inc

        inc = Incident(
            id=f"inc-{t.id}",
            opened_at=datetime.now(timezone.utc),
            status="open",
            centroid=(t.lat, t.lon),
            cells=[t.h3_r8],
            ticket_ids=[t.id],
            category_mix={t.category: 1},
        )
        self.incident_repo.upsert(inc)
        return inc


def create_app(
    ticket_repo: Optional[TicketRepo] = None,
    incident_repo: Optional[IncidentRepo] = None,
    evidence_repo: Optional[EvidenceRepo] = None,
    cluster_detector: Optional[ClusterDetector] = None,
    pipeline: Optional[OuterPipeline] = None,
    notifier: Optional[Notifier] = None,
) -> FastAPI:
    """Factory function for FastAPI application with injected dependencies."""
    app = FastAPI(
        title="NammaTwin API",
        version="0.1.0",
        description="NammaTwin Urban Incident & Infrastructure Diagnostic API",
    )

    t_repo = ticket_repo or InMemoryTicketRepo()
    i_repo = incident_repo or InMemoryIncidentRepo()
    e_repo = evidence_repo or InMemoryEvidenceRepo()
    notif = notifier or ConsoleNotifier()
    detector = cluster_detector or DefaultClusterDetector(t_repo, i_repo)

    trace_store: dict[str, list[dict[str, Any]]] = {}
    pipeline_cache: dict[str, dict[str, Any]] = {}

    def on_trace(evt: dict[str, Any]) -> None:
        inc_id = evt.get("incident_id", "default")
        trace_store.setdefault(inc_id, []).append(evt)

    pipe = pipeline
    if pipe is None:
        canned_path = Path("tests/fixtures/evidence_power_led_stp.json")
        canned = load_canned_evidence(canned_path) if canned_path.exists() else {}
        reg = FakeToolRegistry(canned_evidence=canned)
        inv_llm = FakeLLM(get_default_tool_choices("power_led_stp"))
        plan_llm = FakeLLM([PlanDraft()])
        saver = SqliteSaver("data/api_pipeline.db")
        pipe = OuterPipeline(
            registry=reg,
            investigator_llm=inv_llm,
            planner_llm=plan_llm,
            notifier=notif,
            checkpointer=saver,
            repo=e_repo,
            on_trace_callback=on_trace,
        )

    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health():
        return HealthResponse()

    @app.post("/tickets", response_model=TicketIngestResponse, tags=["Tickets"])
    async def ingest_ticket(ticket: Ticket):
        t_repo.add(ticket)
        inc = detector.ingest(ticket)
        if inc:
            # Store in repo first
            i_repo.upsert(inc)
            # Run pipeline
            res = pipe.start(inc, [ticket])
            pipeline_cache[inc.id] = res

            # Capture trace
            dossier = res.get("dossier")
            if dossier and dossier.trace:
                trace_store[inc.id] = list(dossier.trace)

            inc_dict = inc.model_dump()
            inc_dict["status"] = res.get("status", "awaiting_approval")
            updated_inc = Incident(**inc_dict)
            i_repo.upsert(updated_inc)
            return TicketIngestResponse(ticket_id=ticket.id, incident_id=inc.id)

        return TicketIngestResponse(ticket_id=ticket.id)

    @app.get("/incidents", response_model=list[Incident], tags=["Incidents"])
    async def list_incidents():
        return i_repo.open()

    @app.get("/incidents/{incident_id}", response_model=IncidentDetailResponse, tags=["Incidents"])
    async def get_incident(incident_id: str):
        inc = i_repo.get(incident_id)
        if not inc:
            raise HTTPException(status_code=404, detail="Incident not found")

        cached = pipeline_cache.get(incident_id, {})
        dossier = cached.get("dossier")
        actions = cached.get("actions", [])
        status = cached.get("status", inc.status)
        all_t = t_repo.all()
        inc_tickets = [t for t in all_t if t.id in inc.ticket_ids]

        return IncidentDetailResponse(
            incident=inc,
            status=status,
            dossier=dossier,
            actions=actions,
            tickets=inc_tickets,
        )

    @app.post("/scenarios/load", tags=["Scenarios"])
    async def load_scenario(name: str = Query("bellandur_flood")):
        fixture_path = Path("tests/fixtures/tickets_bellandur_flood.json")
        if not fixture_path.exists():
            raise HTTPException(status_code=404, detail="Scenario fixture not found")
        with open(fixture_path, encoding="utf-8") as f:
            tickets_data = json.load(f)

        last_inc_id = None
        for td in tickets_data:
            t = Ticket(**td)
            t_repo.add(t)
            inc = detector.ingest(t)
            if inc:
                i_repo.upsert(inc)
                res = pipe.start(inc, [t])
                pipeline_cache[inc.id] = res
                dossier = res.get("dossier")
                if dossier and dossier.trace:
                    trace_store[inc.id] = list(dossier.trace)
                inc_dict = inc.model_dump()
                inc_dict["status"] = res.get("status", "awaiting_approval")
                i_repo.upsert(Incident(**inc_dict))
                last_inc_id = inc.id

        return {"status": "ok", "scenario": name, "incident_id": last_inc_id, "tickets_loaded": len(tickets_data)}

    @app.get("/incidents/{incident_id}/stream", tags=["Incidents"])
    async def stream_incident_trace(incident_id: str):
        async def event_generator():
            events = trace_store.get(incident_id, [])
            for evt in events:
                yield f"data: {json.dumps(evt)}\n\n"
                await asyncio.sleep(0.01)
            yield "event: end\ndata: {}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.post("/incidents/{incident_id}/decision", tags=["Incidents"])
    async def submit_decision(incident_id: str, decision: Decision):
        res = pipe.resume_with_decision(incident_id, decision)
        pipeline_cache[incident_id] = res

        inc = i_repo.get(incident_id)
        if inc:
            inc_dict = inc.model_dump()
            inc_dict["status"] = res.get("status", "dispatched")
            i_repo.upsert(Incident(**inc_dict))

        return res

    @app.post("/incidents/{incident_id}/verify", response_model=VerifyResponse, tags=["Incidents"])
    async def verify_incident(incident_id: str, fast_forward_min: int = Query(45)):
        inc = i_repo.get(incident_id)
        if not inc:
            raise HTTPException(status_code=404, detail="Incident not found")

        new_status = assess(
            incident=inc,
            new_tickets=[],
            rainfall_now=0.0,
            traffic_ratio=0.85,
        )
        inc_dict = inc.model_dump()
        inc_dict["status"] = new_status
        i_repo.upsert(Incident(**inc_dict))

        if incident_id in pipeline_cache:
            pipeline_cache[incident_id]["status"] = new_status

        return VerifyResponse(
            incident_id=incident_id,
            status=new_status,
            verify_result=new_status,
            fast_forward_min=fast_forward_min,
        )

    return app


# Default app instance for ASGI servers
app = create_app()
