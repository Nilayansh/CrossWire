from datetime import datetime, timezone
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.main import create_app
from app.contracts.models import Action, Decision, Incident, Ticket
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


class StubClusterDetector:
    def __init__(self, ticket_repo: InMemoryTicketRepo, incident_repo: InMemoryIncidentRepo):
        self.ticket_repo = ticket_repo
        self.incident_repo = incident_repo

    def ingest(self, t: Ticket) -> Incident:
        self.ticket_repo.add(t)
        # Ingest open incident
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


class RecordingNotifier:
    def __init__(self):
        self.sent: list[tuple[str, Any]] = []

    def send(self, dept: str, message: Any):
        self.sent.append((dept, message))
        return ConsoleNotifier().send(dept, message)


@pytest.fixture
def app_and_deps(tmp_path: Path):
    from app.investigator.run import load_canned_evidence
    from app.investigator.state import ToolChoice

    ticket_repo = InMemoryTicketRepo()
    incident_repo = InMemoryIncidentRepo()
    evidence_repo = InMemoryEvidenceRepo()
    detector = StubClusterDetector(ticket_repo, incident_repo)

    canned = load_canned_evidence(Path("tests/fixtures/evidence_power_led_stp.json"))
    registry = FakeToolRegistry(canned_evidence=canned)
    notifier = RecordingNotifier()

    inv_llm = FakeLLM([
        ToolChoice(tool_name="history", why="Analyze ticket lag"),
        ToolChoice(tool_name="outage", why="Check substation"),
    ])

    plan_draft = PlanDraft(
        actions=[
            Action(
                id="act-001",
                dept="power_utility",
                action="Reset substation breaker",
                priority="P1",
                rationale="Power trip",
                evidence_ids=["ev-stp-01"],
                confidence=0.89,
            ),
            Action(
                id="act-002",
                dept="sewerage",
                action="Clear blockage",
                priority="P2",
                rationale="Debris",
                evidence_ids=["ev-stp-01"],
                confidence=0.89,
            ),
        ]
    )
    planner_llm = FakeLLM([plan_draft])
    db_file = tmp_path / "api_checkpoints.db"
    checkpointer = SqliteSaver(str(db_file))

    pipeline = OuterPipeline(
        registry=registry,
        investigator_llm=inv_llm,
        planner_llm=planner_llm,
        notifier=notifier,
        checkpointer=checkpointer,
        repo=evidence_repo,
    )

    app = create_app(
        ticket_repo=ticket_repo,
        incident_repo=incident_repo,
        evidence_repo=evidence_repo,
        cluster_detector=detector,
        pipeline=pipeline,
        notifier=notifier,
    )

    return app, notifier


@pytest.mark.anyio
async def test_full_api_lifecycle(app_and_deps):
    app, notifier = app_and_deps
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

        # 2. Ingest ticket
        ticket_payload = {
            "id": "t-001",
            "ts": datetime.now(timezone.utc).isoformat(),
            "channel": "telegram",
            "lang": "en",
            "text_original": "Power cut and sewage overflow near tech park",
            "text_en": "Power cut and sewage overflow near tech park",
            "category": "power",
            "severity": 4,
            "lat": 12.928,
            "lon": 77.682,
            "geo_confidence": 0.9,
            "h3_r8": "886189255bfffff",
        }
        res_t = await client.post("/tickets", json=ticket_payload)
        assert res_t.status_code == 200
        data_t = res_t.json()
        assert "incident_id" in data_t
        incident_id = data_t["incident_id"]

        # 3. GET /incidents and GET /incidents/{id}
        res_list = await client.get("/incidents")
        assert res_list.status_code == 200
        assert len(res_list.json()) >= 1

        res_inc = await client.get(f"/incidents/{incident_id}")
        assert res_inc.status_code == 200
        inc_data = res_inc.json()
        assert inc_data["status"] == "awaiting_approval"
        assert len(inc_data["actions"]) == 2
        assert inc_data["dossier"] is not None

        # 4. SSE Stream endpoint
        res_stream = await client.get(f"/incidents/{incident_id}/stream")
        assert res_stream.status_code == 200
        assert "text/event-stream" in res_stream.headers["content-type"]

        # 5. POST /incidents/{id}/decision
        decision_payload = {
            "incident_id": incident_id,
            "approved_action_ids": ["act-001"],
            "rejected": {"act-002": "Unnecessary action"},
            "edits": {},
            "officer": "Chief Engineer",
        }
        res_dec = await client.post(f"/incidents/{incident_id}/decision", json=decision_payload)
        assert res_dec.status_code == 200
        dec_data = res_dec.json()
        assert dec_data["status"] in ("dispatched", "resolving")
        # Only approved act-001 was dispatched
        assert len(notifier.sent) == 1
        assert notifier.sent[0][0] == "power_utility"

        # 6. Fast-forward verify: POST /incidents/{id}/verify?fast_forward_min=45
        res_ver = await client.post(f"/incidents/{incident_id}/verify?fast_forward_min=45")
        assert res_ver.status_code == 200
        ver_data = res_ver.json()
        assert ver_data["status"] in ("resolving", "closed")
