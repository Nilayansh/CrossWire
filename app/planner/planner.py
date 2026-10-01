from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field

from app.contracts.models import Action, Dossier, Incident
from app.llm import LLM
from app.planner.priority import score, to_band, vulnerability
from app.planner.validators import get_allowed_departments, validate_actions

PLANNER_SYSTEM_PROMPT = """You are the Senior Municipal Dispatch Planner for NammaTwin in Bengaluru.
Your objective is to review the completed investigative dossier for an infrastructure incident and generate high-impact, coordinated departmental actions.

Rules:
1. Every action must target one of the permitted departments.
2. Every action MUST cite at least one valid evidence ID from the dossier that justifies it.
3. Provide a clear, actionable operational remedy and rationale.
"""

PLAN_PROMPT_TEMPLATE = """Incident: {incident_id}
Centroid: {centroid}
Affected Cells: {cells}
Category Distribution: {category_mix}

Top Hypotheses (Root Causes):
{hypotheses_ranking}

Evidence Dossier:
{evidence_summary}

Permitted Departments for this Incident:
{allowed_departments}

Generate departmental operational actions citing supporting evidence IDs.
"""


class PlanDraft(BaseModel):
    actions: list[Action] = Field(default_factory=list)


class Planner:
    def __init__(self, llm: Optional[Any] = None) -> None:
        self.llm = llm if llm is not None else LLM

    def plan(
        self,
        dossier: Dossier,
        incident: Incident,
        osm_ctx: dict[str, Any],
    ) -> list[Action]:
        """Generates validated, prioritized actions for an incident dossier."""
        vuln = vulnerability(osm_ctx)
        top_confidence = dossier.ranked[0][1] if dossier.ranked else 0.5
        severity_norm = 0.7
        velocity = 0.6

        p_score, _ = score(
            severity_norm=severity_norm,
            velocity=velocity,
            vulnerability=vuln,
            confidence=top_confidence,
        )
        calculated_band = to_band(p_score)

        allowed_depts = get_allowed_departments(dossier)
        hyp_str = "\n".join(f"- {h.value}: {prob:.1%}" for h, prob in dossier.ranked[:3])
        ev_str = "\n".join(f"- ID [{ev.id}] ({ev.tool}): {ev.summary}" for ev in dossier.evidence)

        prompt = PLAN_PROMPT_TEMPLATE.format(
            incident_id=incident.id,
            centroid=incident.centroid,
            cells=incident.cells,
            category_mix=incident.category_mix,
            hypotheses_ranking=hyp_str,
            evidence_summary=ev_str,
            allowed_departments=", ".join(sorted(allowed_depts)),
        )

        draft: PlanDraft = self.llm.structured(
            schema=PlanDraft,
            prompt=prompt,
            tier="fast",
            system_prompt=PLANNER_SYSTEM_PROMPT,
        )

        processed_actions: list[Action] = []
        for i, act in enumerate(draft.actions, start=1):
            act_data = act.model_dump()
            if not act_data.get("id"):
                act_data["id"] = f"act-{i:03d}"
            if not act_data.get("target_latlon"):
                act_data["target_latlon"] = incident.centroid
            # Apply calculated band if not set
            if not act_data.get("priority"):
                act_data["priority"] = calculated_band
            # Default confidence to top hypothesis confidence if omitted or 0.0
            if not act_data.get("confidence"):
                act_data["confidence"] = top_confidence
            processed_actions.append(Action(**act_data))

        # Enforce all guardrail validators (evidence presence, allowed depts, confidence demotion)
        return validate_actions(processed_actions, dossier)
