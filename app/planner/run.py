from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from app.contracts.models import Action, Evidence, Incident
from app.investigator.graph import build_graph
from app.investigator.run import get_default_tool_choices, load_canned_evidence
from app.llm import FakeLLM
from app.planner.planner import PlanDraft, Planner
from app.planner.priority import score, to_band, vulnerability
from app.stubs.fake_tool_registry import FakeToolRegistry
from app.stubs.in_memory_repos import InMemoryEvidenceRepo


def get_canned_plan(scenario: str, evidence: list[Evidence]) -> PlanDraft:
    ev_ids = [e.id for e in evidence]
    if "stp" in scenario.lower() or "power" in scenario.lower():
        return PlanDraft(
            actions=[
                Action(
                    dept="power_utility",
                    action="Restore 11kV substation feeder power to tech park STP",
                    priority="P1",
                    rationale="Power trip caused STP pumps to stall, resulting in localized sewage backflow",
                    evidence_ids=[ev_ids[0], ev_ids[1]] if len(ev_ids) >= 2 else ev_ids,
                    confidence=0.89,
                ),
                Action(
                    dept="sewerage",
                    action="Deploy suction jetting machines to clear overflow on ORR service road",
                    priority="P1",
                    rationale="High pedestrian and bus stop proximity with bio-hazard risk",
                    evidence_ids=[ev_ids[0]],
                    confidence=0.89,
                ),
            ]
        )
    else:
        return PlanDraft(
            actions=[
                Action(
                    dept="stormwater",
                    action="Deploy high-capacity mobile dewatering pumps at Ecospace culvert",
                    priority="P1",
                    rationale="Cloudburst volume exceeds drain gravity discharge threshold",
                    evidence_ids=[ev_ids[0]],
                    confidence=0.92,
                ),
                Action(
                    dept="traffic_police",
                    action="Divert Bellandur-Marathahalli service lane traffic to flyover",
                    priority="P2",
                    rationale="Waterlogging exceeds 2 feet along central bus stop",
                    evidence_ids=[ev_ids[0]],
                    confidence=0.92,
                ),
            ]
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="NammaTwin Dispatch Planner CLI")
    parser.add_argument(
        "--scenario",
        type=str,
        default="power_led_stp",
        help="Scenario name (e.g. power_led_stp, rain_overwhelm)",
    )
    args = parser.parse_args()

    # 1. Load evidence and run investigator graph to generate dossier
    fixtures_dir = Path("tests/fixtures")
    fixture_path = fixtures_dir / f"evidence_{args.scenario}.json"
    if not fixture_path.exists():
        fixture_path = fixtures_dir / f"{args.scenario}.json"

    canned_evidence = load_canned_evidence(fixture_path)
    registry = FakeToolRegistry(canned_evidence=canned_evidence)
    repo = InMemoryEvidenceRepo()
    choices = get_default_tool_choices(args.scenario)
    investigator_llm = FakeLLM(choices)

    incident = Incident(
        id=f"inc-{args.scenario}-01",
        opened_at=datetime.now(timezone.utc),
        status="open",
        centroid=(12.928, 77.682),
        cells=["886189255bfffff"],
        category_mix={"waterlogging": 5, "power": 4, "traffic": 3},
    )

    app = build_graph(registry=registry, llm=investigator_llm, repo=repo)
    result = app.invoke({"incident": incident, "tickets": []})
    dossier = result["dossier"]

    # 2. Plan actions with Planner
    osm_ctx = {
        "hospital_dist_m": 450.0,
        "school_dist_m": 800.0,
        "on_arterial": True,
    }

    plan_draft = get_canned_plan(args.scenario, dossier.evidence)
    planner_llm = FakeLLM([plan_draft])
    planner = Planner(llm=planner_llm)

    actions = planner.plan(dossier=dossier, incident=incident, osm_ctx=osm_ctx)

    # 3. Print operational dispatch plan
    vuln = vulnerability(osm_ctx)
    top_hyp, top_prob = dossier.ranked[0]
    p_score, breakdown = score(
        severity_norm=0.7,
        velocity=0.6,
        vulnerability=vuln,
        confidence=top_prob,
    )
    band = to_band(p_score)

    print("\n" + "=" * 70)
    print(f"DISPATCH PLAN: Scenario '{args.scenario}'")
    print(f"Incident: {incident.id} | Root Cause Lead: {top_hyp.value} ({top_prob:.1%})")
    print("=" * 70)
    print(f"Priority Band : {band} (Score: {p_score:.3f})")
    print(
        f"Breakdown     : Severity={breakdown['severity']:.2f}, "
        f"Velocity={breakdown['velocity']:.2f}, "
        f"Vuln={breakdown['vulnerability']:.2f}, "
        f"Conf={breakdown['confidence']:.2f}"
    )
    print("-" * 70)
    print(f"{'ID':<9} | {'Dept':<15} | {'Band':<5} | {'Action':<34}")
    print("-" * 70)
    for act in actions:
        print(f"{act.id or 'N/A':<9} | {act.dept:<15} | {act.priority:<5} | {act.action}")
        print(f"          Rationale: {act.rationale}")
        print(f"          Evidence IDs: {act.evidence_ids} | Verify First: {act.needs_field_verification}")
        print("-" * 70)
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
