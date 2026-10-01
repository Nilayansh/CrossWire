from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from app.contracts.models import Evidence, Incident, Ticket
from app.investigator.graph import build_graph
from app.investigator.state import ToolChoice
from app.llm import FakeLLM
from app.stubs.fake_tool_registry import FakeToolRegistry
from app.stubs.in_memory_repos import InMemoryEvidenceRepo


def _resolve_evidence_fixture(scenario: str) -> Path:
    fixtures_dir = Path("tests/fixtures")
    candidates = [
        fixtures_dir / f"evidence_{scenario}.json",
        fixtures_dir / f"{scenario}.json",
        Path(scenario),
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"Fixture for scenario '{scenario}' not found under tests/fixtures/")


def load_canned_evidence(fixture_path: Path) -> dict[str, list[Evidence]]:
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)
    items = [Evidence.model_validate(it) for it in data]
    by_tool: dict[str, list[Evidence]] = {}
    for it in items:
        by_tool.setdefault(it.tool, []).append(it)
    return by_tool


def get_default_tool_choices(scenario: str) -> list[ToolChoice]:
    if "rain" in scenario.lower():
        return [
            ToolChoice(tool_name="rainfall", why="Check cloudburst precipitation intensity"),
            ToolChoice(tool_name="elevation", why="Analyze natural terrain depression"),
            ToolChoice(tool_name="hotspots", why="Check BBMP chronic flood database"),
        ]
    elif "stp" in scenario.lower() or "power" in scenario.lower():
        return [
            ToolChoice(tool_name="history", why="Analyze ticket sequence and power-sewage lag"),
            ToolChoice(tool_name="outage", why="Verify 11kV substation grid trip"),
            ToolChoice(tool_name="osm", why="Locate nearby large STP facility"),
        ]
    else:
        return [
            ToolChoice(tool_name="rainfall", why="Measure precipitation rate"),
            ToolChoice(tool_name="elevation", why="Check terrain slope"),
            ToolChoice(tool_name="history", why="Review past ticket temporal history"),
            ToolChoice(tool_name="osm", why="Inspect surrounding infrastructure on OSM"),
            ToolChoice(tool_name="hotspots", why="Check historical hotspot records"),
            ToolChoice(tool_name="outage", why="Check power grid status"),
        ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NammaTwin Investigator LangGraph Loop")
    parser.add_argument(
        "--scenario",
        type=str,
        default="rain_overwhelm",
        help="Scenario name (e.g. rain_overwhelm, power_led_stp, inconclusive)",
    )
    args = parser.parse_args()

    fixture_path = _resolve_evidence_fixture(args.scenario)
    canned_evidence = load_canned_evidence(fixture_path)

    registry = FakeToolRegistry(canned_evidence=canned_evidence)
    repo = InMemoryEvidenceRepo()
    choices = get_default_tool_choices(args.scenario)
    fake_llm = FakeLLM(choices)

    incident = Incident(
        id=f"inc-{args.scenario}-01",
        opened_at=datetime.now(timezone.utc),
        status="open",
        centroid=(12.928, 77.682),
        cells=["886189255bfffff"],
        category_mix={"waterlogging": 6, "traffic": 4, "power": 2},
    )

    tickets_file = Path("tests/fixtures/tickets_bellandur_flood.json")
    tickets: list[Ticket] = []
    if tickets_file.exists():
        with open(tickets_file, encoding="utf-8") as f:
            t_data = json.load(f)
        tickets = [Ticket.model_validate(it) for it in t_data]

    print("\n" + "=" * 60)
    print(f"INVESTIGATOR RUN: Scenario '{args.scenario}'")
    print(f"Incident: {incident.id} | Centroid: {incident.centroid}")
    print("=" * 60 + "\n")

    def on_step(evt: dict[str, Any]) -> None:
        top_post = max(evt["posterior_snapshot"].items(), key=lambda kv: kv[1])
        print(f"[Step {evt['step']}] Tool: {evt['tool']:<12} | Why: {evt['why']}")
        print(f"         Evidence: {evt['evidence_id']}")
        print(f"         Top Lead: {top_post[0]} ({top_post[1]:.1%})\n")

    app = build_graph(
        registry=registry,
        llm=fake_llm,
        repo=repo,
        on_step_callback=on_step,
    )

    result = app.invoke({"incident": incident, "tickets": tickets})
    dossier = result.get("dossier")

    if not dossier:
        print("ERROR: No dossier produced!")
        return

    print("=" * 60)
    print("FINAL DOSSIER")
    print("=" * 60)
    print(f"Incident ID   : {dossier.incident_id}")
    print(f"Conclusive    : {dossier.conclusive}")
    print(f"Stop Reason   : {dossier.stop_reason}")
    print(f"Steps Taken   : {result.get('step', len(dossier.trace))}")
    print(f"Tools Used    : {', '.join(result.get('used_tools', []))}")
    print("\nRanked Hypotheses:")
    for hyp, prob in dossier.ranked:
        print(f"  - {hyp.value:<25}: {prob:>6.2%}")
    print("\nEvidence Collected:")
    for ev in dossier.evidence:
        print(f"  - [{ev.tool}] {ev.summary} (keys: {[k.value for k in ev.keys]})")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
