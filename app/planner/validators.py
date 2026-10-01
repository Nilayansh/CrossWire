from __future__ import annotations

import re
from typing import Optional

from app.contracts.keys import HypothesisID
from app.contracts.models import Action, Dossier
from app.investigator.hypotheses import HYPOTHESIS_DEPARTMENTS

DEPT_CANONICAL_MAP: dict[str, str] = {
    "stormwater": "stormwater",
    "stormwater/swd": "stormwater",
    "lake authority": "stormwater",
    "power utility": "power_utility",
    "power_utility": "power_utility",
    "sewerage board": "sewerage",
    "sewerage": "sewerage",
    "traffic": "traffic_police",
    "traffic police": "traffic_police",
    "traffic_police": "traffic_police",
    "solid waste": "solid_waste",
    "solid_waste": "solid_waste",
    "water board": "water_board",
    "water_board": "water_board",
}

REMEDY_VERB_PREFIXES = (
    "deploy ",
    "dispatch ",
    "clear ",
    "repair ",
    "replace ",
    "excavate ",
    "pump ",
    "unclog ",
    "fix ",
    "install ",
)


def get_allowed_departments(dossier: Dossier) -> set[str]:
    """Returns canonical department literals allowed by the top-2 hypotheses."""
    top_2_hypotheses = [h for h, _ in dossier.ranked[:2]]
    allowed: set[str] = set()
    for h in top_2_hypotheses:
        for raw_dept in HYPOTHESIS_DEPARTMENTS.get(h, []):
            norm = DEPT_CANONICAL_MAP.get(raw_dept.lower().strip())
            if norm:
                allowed.add(norm)
    return allowed


def rewrite_to_inspect_first(action_text: str) -> str:
    """Rewrites remedy verbs to 'inspect and verify' when confidence is low."""
    clean = action_text.strip()
    if clean.lower().startswith("inspect and verify"):
        return clean

    # If starts with a remedy verb, rewrite smoothly
    for prefix in REMEDY_VERB_PREFIXES:
        if clean.lower().startswith(prefix):
            remainder = clean[len(prefix):]
            return f"Inspect and verify condition of {remainder}"

    return f"Inspect and verify: {clean}"


def validate_actions(actions: list[Action], dossier: Dossier) -> list[Action]:
    """Validates and enforces guardrails on LLM-generated Actions.
    
    Rules:
    1. Reject any action with empty evidence_ids or ids not in dossier.evidence.
    2. Reject any action for a department not supported by the top-2 hypotheses.
    3. If confidence < 0.6, force needs_field_verification=True and rewrite remedy verbs to 'inspect and verify'.
    """
    valid_evidence_ids = {ev.id for ev in dossier.evidence}
    allowed_departments = get_allowed_departments(dossier)

    validated: list[Action] = []
    for act in actions:
        # Rule 1: Evidence ID validation
        if not act.evidence_ids:
            continue
        if any(eid not in valid_evidence_ids for eid in act.evidence_ids):
            continue

        # Rule 2: Department alignment with top-2 hypotheses
        canonical_dept = DEPT_CANONICAL_MAP.get(act.dept.lower().strip(), act.dept)
        if canonical_dept not in allowed_departments:
            continue

        act_data = act.model_dump()
        act_data["dept"] = canonical_dept

        # Rule 3: Low-confidence demotion
        if act.confidence < 0.6:
            act_data["needs_field_verification"] = True
            act_data["action"] = rewrite_to_inspect_first(act.action)

        validated.append(Action(**act_data))

    return validated
