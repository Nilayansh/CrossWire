from datetime import datetime, timezone
from pathlib import Path
import pytest

from app.contracts.keys import HypothesisID
from app.contracts.models import Action, Decision, Incident, OutboundMessage, Ticket
from app.llm import FakeLLM
from app.orchestrator.pipeline import OuterPipeline, SqliteSaver
from app.planner.planner import PlanDraft, Planner
from app.stubs.console_notifier import ConsoleNotifier
from app.stubs.fake_tool_registry import FakeToolRegistry
from app.stubs.in_memory_repos import InMemoryEvidenceRepo


class RecordingNotifier:
    def __init__(self):
        self.sent: list[tuple[str, OutboundMessage]] = []

    def send(self, dept: str, message: OutboundMessage):
        self.sent.append((dept, message))
        return ConsoleNotifier().send(dept, message)


def sample_incident() -> Incident:
    return Incident(
        id="inc-pipe-01",
        opened_at=datetime.now(timezone.utc),
        status="open",
        centroid=(12.928, 77.682),
        cells=["886189255bfffff"],
        ticket_ids=["t1", "t2"],
        category_mix={"power": 2, "sewage": 2},
    )


def test_outer_pipeline_interrupt_and_resume(tmp_path: Path):
    db_file = tmp_path / "checkpoints.db"
    saver = SqliteSaver(str(db_file))

    # Setup canned evidence for power_led_stp
    from app.investigator.run import load_canned_evidence
    canned = load_canned_evidence(Path("tests/fixtures/evidence_power_led_stp.json"))
    registry = FakeToolRegistry(canned_evidence=canned)
    notifier = RecordingNotifier()

    # Setup FakeLLMs
    from app.investigator.state import ToolChoice

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

    pipeline = OuterPipeline(
        registry=registry,
        investigator_llm=inv_llm,
        planner_llm=planner_llm,
        notifier=notifier,
        checkpointer=saver,
    )

    incident = sample_incident()
    thread_id = incident.id

    # 1. Run pipeline until interrupt at await_approval
    res1 = pipeline.start(incident=incident, tickets=[])
    assert "__interrupt__" in res1
    assert res1.get("status") == "awaiting_approval"
    assert len(res1.get("actions", [])) == 2
    # Notifier has not been called yet
    assert len(notifier.sent) == 0

    # 2. Simulate officer decision: approve act-001, reject act-002
    decision = Decision(
        incident_id=incident.id,
        approved_action_ids=["act-001"],
        rejected={"act-002": "Not required"},
        edits={},
        officer="Officer Kumar",
    )

    # 3. Simulate process restart by creating a new pipeline with same sqlite db
    saver_restarted = SqliteSaver(str(db_file))
    pipeline_restarted = OuterPipeline(
        registry=registry,
        investigator_llm=inv_llm,
        planner_llm=planner_llm,
        notifier=notifier,
        checkpointer=saver_restarted,
    )

    res2 = pipeline_restarted.resume_with_decision(thread_id=thread_id, decision=decision)

    # 4. Verify that only act-001 was dispatched, and status transitioned
    assert res2.get("status") in ("resolving", "closed", "escalated")
    assert len(notifier.sent) == 1
    dept, msg = notifier.sent[0]
    assert dept == "power_utility"
    assert "act-001" in msg.subject or "Reset" in msg.body
