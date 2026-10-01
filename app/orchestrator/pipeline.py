from __future__ import annotations

import pickle
import sqlite3
from typing import Any, Callable, Iterator, Optional, Sequence, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    get_checkpoint_metadata,
)
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt

from app.contracts.interfaces import EvidenceRepo, Notifier, ToolRegistry
from app.contracts.models import (
    Action,
    Decision,
    Delivery,
    Dossier,
    Incident,
    OutboundMessage,
    Ticket,
)
from app.investigator.graph import build_graph
from app.planner.planner import Planner
from app.verifier.verifier import assess


class SqliteSaver(BaseCheckpointSaver):
    """SQLite-backed checkpointer ensuring graph interrupts survive process restarts."""

    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT,
                    checkpoint_ns TEXT,
                    checkpoint_id TEXT,
                    parent_id TEXT,
                    checkpoint_blob BLOB,
                    metadata_blob BLOB,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS blobs (
                    thread_id TEXT,
                    checkpoint_ns TEXT,
                    channel TEXT,
                    version TEXT,
                    blob_type TEXT,
                    blob_data BLOB,
                    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS writes (
                    thread_id TEXT,
                    checkpoint_ns TEXT,
                    checkpoint_id TEXT,
                    task_id TEXT,
                    idx INTEGER,
                    channel TEXT,
                    val_type TEXT,
                    val_data BLOB,
                    task_path TEXT,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                )
                """
            )

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        with self._get_conn() as conn:
            cursor = conn.cursor()
            if checkpoint_id:
                cursor.execute(
                    """
                    SELECT checkpoint_id, parent_id, checkpoint_blob, metadata_blob 
                    FROM checkpoints 
                    WHERE thread_id=? AND checkpoint_ns=? AND checkpoint_id=?
                    """,
                    (thread_id, checkpoint_ns, checkpoint_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT checkpoint_id, parent_id, checkpoint_blob, metadata_blob 
                    FROM checkpoints 
                    WHERE thread_id=? AND checkpoint_ns=? 
                    ORDER BY checkpoint_id DESC LIMIT 1
                    """,
                    (thread_id, checkpoint_ns),
                )
            row = cursor.fetchone()
            if not row:
                return None

            cid, pid, c_blob, m_blob = row
            c_dict = self.serde.loads_typed(pickle.loads(c_blob))
            meta_dict = self.serde.loads_typed(pickle.loads(m_blob))

            # Retrieve channel value blobs
            values: dict[str, Any] = {}
            for channel, version in c_dict.get("channel_versions", {}).items():
                cursor.execute(
                    """
                    SELECT blob_type, blob_data FROM blobs 
                    WHERE thread_id=? AND checkpoint_ns=? AND channel=? AND version=?
                    """,
                    (thread_id, checkpoint_ns, channel, version),
                )
                brow = cursor.fetchone()
                if brow and brow[0] != "empty":
                    values[channel] = self.serde.loads_typed((brow[0], brow[1]))
            c_dict["channel_values"] = values

            # Retrieve pending writes
            cursor.execute(
                """
                SELECT task_id, channel, val_type, val_data FROM writes 
                WHERE thread_id=? AND checkpoint_ns=? AND checkpoint_id=?
                """,
                (thread_id, checkpoint_ns, cid),
            )
            pending_writes = [
                (r[0], r[1], self.serde.loads_typed((r[2], r[3]))) for r in cursor.fetchall()
            ]

            return CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": cid,
                    }
                },
                checkpoint=c_dict,
                metadata=meta_dict,
                parent_config=(
                    {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": pid,
                        }
                    }
                    if pid
                    else None
                ),
                pending_writes=pending_writes,
            )

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        return iter([])

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        c = checkpoint.copy()
        values = c.pop("channel_values")

        with self._get_conn() as conn:
            for k, v in new_versions.items():
                if k in values:
                    t, b = self.serde.dumps_typed(values[k])
                else:
                    t, b = "empty", b""
                conn.execute(
                    """
                    INSERT OR REPLACE INTO blobs VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (thread_id, checkpoint_ns, k, v, t, b),
                )
            c_type, c_bytes = self.serde.dumps_typed(c)
            m_type, m_bytes = self.serde.dumps_typed(get_checkpoint_metadata(config, metadata))
            conn.execute(
                """
                INSERT OR REPLACE INTO checkpoints VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    checkpoint_ns,
                    checkpoint["id"],
                    config["configurable"].get("checkpoint_id"),
                    pickle.dumps((c_type, c_bytes)),
                    pickle.dumps((m_type, m_bytes)),
                ),
            )

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]
        with self._get_conn() as conn:
            for idx, (ch, val) in enumerate(writes):
                t, b = self.serde.dumps_typed(val)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO writes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (thread_id, checkpoint_ns, checkpoint_id, task_id, idx, ch, t, b, task_path),
                )


class PipelineState(TypedDict, total=False):
    incident: Incident
    tickets: list[Ticket]
    dossier: Optional[Dossier]
    actions: list[Action]
    decision: Optional[Decision]
    status: str
    verify_result: Optional[str]
    dispatched: list[Delivery]


class OuterPipeline:
    """Outer LangGraph pipeline orchestrating investigation, planning, approval, and dispatch."""

    def __init__(
        self,
        registry: ToolRegistry,
        investigator_llm: Any,
        planner_llm: Any,
        notifier: Notifier,
        checkpointer: Optional[BaseCheckpointSaver] = None,
        repo: Optional[EvidenceRepo] = None,
        on_trace_callback: Optional[Callable[[dict[str, Any]], None]] = None,
    ):
        self.registry = registry
        self.investigator_llm = investigator_llm
        self.planner_llm = planner_llm
        self.notifier = notifier
        self.checkpointer = checkpointer
        self.repo = repo
        self.on_trace_callback = on_trace_callback
        self.graph = self._build_graph()

    def _build_graph(self):
        def incident_opened_node(state: PipelineState) -> dict[str, Any]:
            inc = state["incident"]
            inc_dict = inc.model_dump()
            inc_dict["status"] = "investigating"
            return {"incident": Incident(**inc_dict), "status": "investigating"}

        def investigate_node(state: PipelineState) -> dict[str, Any]:
            inv_graph = build_graph(
                registry=self.registry,
                llm=self.investigator_llm,
                repo=self.repo,
                on_step_callback=self.on_trace_callback,
            )
            inv_result = inv_graph.invoke({
                "incident": state["incident"],
                "tickets": state.get("tickets", []),
            })
            return {"dossier": inv_result.get("dossier")}

        def plan_node(state: PipelineState) -> dict[str, Any]:
            planner = Planner(llm=self.planner_llm)
            osm_ctx = {"hospital_dist_m": 500.0, "school_dist_m": 800.0, "on_arterial": True}
            actions = planner.plan(
                dossier=state["dossier"],
                incident=state["incident"],
                osm_ctx=osm_ctx,
            )
            return {"actions": actions, "status": "awaiting_approval"}

        def await_approval_node(state: PipelineState) -> dict[str, Any]:
            decision = state.get("decision")
            if not decision:
                # Pause at approval interrupt until officer decision is provided
                decision = interrupt({
                    "incident_id": state["incident"].id,
                    "actions": [a.model_dump() for a in state.get("actions", [])],
                })
            return {"decision": decision, "status": "dispatched"}

        def dispatch_node(state: PipelineState) -> dict[str, Any]:
            decision: Optional[Decision] = state.get("decision")
            if not decision:
                return {}

            approved_ids = set(decision.approved_action_ids)
            deliveries: list[Delivery] = []
            for act in state.get("actions", []):
                if act.id in approved_ids:
                    msg = OutboundMessage(
                        recipient=act.dept,
                        subject=f"NammaTwin Action {act.id}",
                        body=act.action,
                        metadata={
                            "incident_id": state["incident"].id,
                            "priority": act.priority,
                            "rationale": act.rationale,
                        },
                    )
                    delivery = self.notifier.send(act.dept, msg)
                    deliveries.append(delivery)

            return {"dispatched": deliveries, "status": "dispatched"}

        def schedule_verify_node(state: PipelineState) -> dict[str, Any]:
            return {"status": "resolving"}

        def verify_node(state: PipelineState) -> dict[str, Any]:
            v_status = assess(
                incident=state["incident"],
                new_tickets=[],
                rainfall_now=1.0,
                traffic_ratio=0.85,
            )
            return {"status": v_status, "verify_result": v_status}

        builder = StateGraph(PipelineState)
        builder.add_node("incident_opened", incident_opened_node)
        builder.add_node("investigate", investigate_node)
        builder.add_node("plan", plan_node)
        builder.add_node("await_approval", await_approval_node)
        builder.add_node("dispatch", dispatch_node)
        builder.add_node("schedule_verify", schedule_verify_node)
        builder.add_node("verify", verify_node)

        builder.set_entry_point("incident_opened")
        builder.add_edge("incident_opened", "investigate")
        builder.add_edge("investigate", "plan")
        builder.add_edge("plan", "await_approval")
        builder.add_edge("await_approval", "dispatch")
        builder.add_edge("dispatch", "schedule_verify")
        builder.add_edge("schedule_verify", "verify")
        builder.add_edge("verify", END)

        return builder.compile(checkpointer=self.checkpointer)

    def start(self, incident: Incident, tickets: list[Ticket]) -> dict[str, Any]:
        config = {"configurable": {"thread_id": incident.id}}
        return self.graph.invoke({"incident": incident, "tickets": tickets}, config=config)

    def resume_with_decision(self, thread_id: str, decision: Decision) -> dict[str, Any]:
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.invoke(Command(resume=decision), config=config)
