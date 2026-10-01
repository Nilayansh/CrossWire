from __future__ import annotations

from datetime import timedelta
from typing import Any, Callable, Optional

from langgraph.graph import END, StateGraph

from app.contracts.interfaces import EvidenceRepo, ToolRegistry
from app.contracts.keys import HypothesisID
from app.contracts.models import Dossier, Evidence, ToolArgs
from app.investigator.prompts import (
    INVESTIGATOR_SYSTEM_PROMPT,
    TOOL_RETRY_PROMPT,
    TOOL_SELECTION_PROMPT,
)
from app.investigator.scoring import (
    apply,
    discriminating_keys,
    init_state,
    posterior,
    should_stop,
)
from app.investigator.state import InvestigatorState, ToolChoice

FALLBACK_TOOL_ORDER: list[str] = [
    "rainfall",
    "elevation",
    "history",
    "osm",
    "hotspots",
    "outage",
]


def build_graph(
    registry: ToolRegistry,
    llm: Any,
    repo: Optional[EvidenceRepo] = None,
    on_step_callback: Optional[Callable[[dict[str, Any]], None]] = None,
):
    """Builds and compiles the Investigator LangGraph with pure dependency injection."""

    def propose_node(state: InvestigatorState) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        if "hypotheses" not in state or not state["hypotheses"]:
            init_hyp = init_state()
            updates["hypotheses"] = init_hyp
            updates["posteriors"] = posterior(init_hyp)
        if "evidence" not in state:
            updates["evidence"] = []
        if "used_tools" not in state:
            updates["used_tools"] = []
        if "trace" not in state:
            updates["trace"] = []
        if "step" not in state:
            updates["step"] = 0
        if "max_steps" not in state:
            updates["max_steps"] = 6
        if "should_stop" not in state:
            updates["should_stop"] = False
        return updates

    def select_tool_node(state: InvestigatorState) -> dict[str, Any]:
        used = set(state.get("used_tools", []))
        available_specs = [s for s in registry.specs() if s.name not in used]
        available_tool_names = [s.name for s in available_specs]

        if not available_specs:
            return {
                "tool_choice": None,
                "should_stop": True,
                "stop_reason": "inconclusive: no tools left",
            }

        incident = state["incident"]
        post = state["posteriors"]
        ranked = sorted(post.items(), key=lambda kv: kv[1], reverse=True)
        ranking_str = "\n".join(f"- {h.value}: {prob:.1%}" for h, prob in ranked)
        disc_keys = discriminating_keys(post)
        disc_keys_str = ", ".join(k.value for k in disc_keys[:5])
        tools_desc_str = "\n".join(
            f"- {s.name}: {s.description} (discriminates: {[h.value for h in s.discriminates]})"
            for s in available_specs
        )

        prompt = TOOL_SELECTION_PROMPT.format(
            incident_id=incident.id,
            centroid=incident.centroid,
            cells=incident.cells,
            category_mix=incident.category_mix,
            ticket_count=len(state.get("tickets", [])),
            hypotheses_ranking=ranking_str,
            discriminating_keys=disc_keys_str,
            used_tools=list(used),
            available_tools=tools_desc_str,
        )

        chosen: Optional[ToolChoice] = None
        try:
            choice = llm.structured(
                schema=ToolChoice,
                prompt=prompt,
                tier="fast",
                system_prompt=INVESTIGATOR_SYSTEM_PROMPT,
            )
            if choice.tool_name in available_tool_names:
                chosen = choice
            else:
                retry_prompt = TOOL_RETRY_PROMPT.format(
                    attempted_tool=choice.tool_name,
                    available_tools=", ".join(available_tool_names),
                )
                retry_choice = llm.structured(
                    schema=ToolChoice,
                    prompt=retry_prompt,
                    tier="fast",
                    system_prompt=INVESTIGATOR_SYSTEM_PROMPT,
                )
                if retry_choice.tool_name in available_tool_names:
                    chosen = retry_choice
        except Exception:
            pass

        # Fallback to deterministic tool order if LLM choice is invalid
        if not chosen:
            for fallback_name in FALLBACK_TOOL_ORDER:
                if fallback_name in available_tool_names:
                    chosen = ToolChoice(
                        tool_name=fallback_name,
                        why="Deterministic fallback tool selection",
                    )
                    break
            if not chosen and available_tool_names:
                chosen = ToolChoice(
                    tool_name=available_tool_names[0],
                    why="First available fallback tool",
                )

        return {"tool_choice": chosen}

    def run_tool_node(state: InvestigatorState) -> dict[str, Any]:
        choice = state.get("tool_choice")
        if not choice or state.get("should_stop", False):
            return {}

        incident = state["incident"]
        t1 = incident.opened_at
        t0 = t1 - timedelta(hours=2)

        raw_args = dict(choice.args)
        raw_args.setdefault("incident_id", incident.id)
        raw_args.setdefault("lat", incident.centroid[0])
        raw_args.setdefault("lon", incident.centroid[1])
        raw_args.setdefault("t0", t0)
        raw_args.setdefault("t1", t1)
        raw_args.setdefault("cells", list(incident.cells))

        tool_args = ToolArgs(**raw_args)
        ev: Evidence = registry.run(choice.tool_name, tool_args)

        if repo is not None:
            repo.add(ev)

        updated_evidence = list(state.get("evidence", [])) + [ev]
        updated_used = list(state.get("used_tools", [])) + [choice.tool_name]

        return {
            "evidence": updated_evidence,
            "used_tools": updated_used,
            "active_evidence": ev,
        }

    def update_node(state: InvestigatorState) -> dict[str, Any]:
        if state.get("should_stop", False):
            return {}

        ev: Optional[Evidence] = state.get("active_evidence")
        if ev is None and state.get("evidence"):
            ev = state["evidence"][-1]

        if ev is None:
            return {}

        choice = state.get("tool_choice")
        new_hypotheses = apply(state["hypotheses"], ev.keys)
        new_post = posterior(new_hypotheses)
        new_step = state.get("step", 0) + 1

        trace_entry: dict[str, Any] = {
            "step": new_step,
            "tool": choice.tool_name if choice else ev.tool,
            "why": choice.why if choice else "",
            "evidence_id": ev.id,
            "posterior_snapshot": {h.value: p for h, p in new_post.items()},
        }

        if on_step_callback is not None:
            on_step_callback(trace_entry)

        new_trace = list(state.get("trace", [])) + [trace_entry]

        return {
            "hypotheses": new_hypotheses,
            "posteriors": new_post,
            "step": new_step,
            "trace": new_trace,
            "active_evidence": None,
        }

    def decide_node(state: InvestigatorState) -> dict[str, Any]:
        if state.get("should_stop", False):
            return {}

        used = set(state.get("used_tools", []))
        available_count = len([s for s in registry.specs() if s.name not in used])
        stop, reason = should_stop(
            post=state["posteriors"],
            steps=state.get("step", 0),
            tools_left=available_count,
            budget=state.get("max_steps", 6),
        )
        return {"should_stop": stop, "stop_reason": reason}

    def finalize_node(state: InvestigatorState) -> dict[str, Any]:
        post = state.get("posteriors", {})
        ranked = sorted(post.items(), key=lambda kv: kv[1], reverse=True)
        top_prob = ranked[0][1] if ranked else 0.0
        second_prob = ranked[1][1] if len(ranked) > 1 else 0.0
        margin = top_prob - second_prob
        conclusive = top_prob >= 0.75 and margin >= 0.20

        dossier = Dossier(
            incident_id=state["incident"].id,
            ranked=ranked,
            evidence=state.get("evidence", []),
            conclusive=conclusive,
            stop_reason=state.get("stop_reason", "Completed investigation"),
            trace=state.get("trace", []),
        )
        return {"dossier": dossier}

    def route_decide(state: InvestigatorState) -> str:
        if state.get("should_stop", False):
            return "finalize"
        return "propose"

    builder = StateGraph(InvestigatorState)
    builder.add_node("propose", propose_node)
    builder.add_node("select_tool", select_tool_node)
    builder.add_node("run_tool", run_tool_node)
    builder.add_node("update", update_node)
    builder.add_node("decide", decide_node)
    builder.add_node("finalize", finalize_node)

    builder.set_entry_point("propose")
    builder.add_edge("propose", "select_tool")
    builder.add_edge("select_tool", "run_tool")
    builder.add_edge("run_tool", "update")
    builder.add_edge("update", "decide")
    builder.add_conditional_edges(
        "decide",
        route_decide,
        {
            "propose": "propose",
            "finalize": "finalize",
        },
    )
    builder.add_edge("finalize", END)

    return builder.compile()
