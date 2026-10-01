from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import pytest

from app.contracts.keys import HypothesisID
from app.contracts.models import Evidence, Incident, Ticket
from app.investigator.graph import build_graph
from app.investigator.state import ToolChoice
from app.llm import FakeLLM
from app.stubs.fake_tool_registry import FakeToolRegistry
from app.stubs.in_memory_repos import InMemoryEvidenceRepo


def load_fixture_evidence(filename: str) -> dict[str, list[Evidence]]:
    path = Path("tests/fixtures") / filename
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = [Evidence.model_validate(item) for item in data]
    by_tool: dict[str, list[Evidence]] = {}
    for it in items:
        by_tool.setdefault(it.tool, []).append(it)
    return by_tool


def sample_incident() -> Incident:
    return Incident(
        id="inc-bellandur-01",
        opened_at=datetime(2026, 9, 5, 8, 0, tzinfo=timezone.utc),
        status="open",
        centroid=(12.928, 77.682),
        cells=["886189255bfffff"],
        category_mix={"waterlogging": 5, "traffic": 3, "power": 2},
    )


def test_rain_overwhelm_scenario():
    canned = load_fixture_evidence("evidence_rain_overwhelm.json")
    registry = FakeToolRegistry(canned_evidence=canned)
    repo = InMemoryEvidenceRepo()

    fake_llm = FakeLLM([
        ToolChoice(tool_name="rainfall", why="Check cloudburst intensity"),
        ToolChoice(tool_name="elevation", why="Check low-lying topography"),
        ToolChoice(tool_name="hotspots", why="Check chronic flood history"),
    ])

    app = build_graph(registry=registry, llm=fake_llm, repo=repo)
    incident = sample_incident()

    result = app.invoke({"incident": incident, "tickets": []})
    dossier = result["dossier"]

    assert dossier is not None
    assert dossier.conclusive is True
    assert dossier.ranked[0][0] == HypothesisID.RAIN_OVERWHELM
    assert dossier.ranked[0][1] >= 0.75
    assert len(result["used_tools"]) <= 6
    assert len(result["used_tools"]) == len(set(result["used_tools"]))
    assert len(dossier.trace) == result["step"]


def test_power_led_stp_scenario():
    canned = load_fixture_evidence("evidence_power_led_stp.json")
    registry = FakeToolRegistry(canned_evidence=canned)
    repo = InMemoryEvidenceRepo()

    fake_llm = FakeLLM([
        ToolChoice(tool_name="history", why="Analyze ticket sequence and power lag"),
        ToolChoice(tool_name="outage", why="Verify grid feeder trip status"),
        ToolChoice(tool_name="osm", why="Check proximity to STP plants"),
    ])

    app = build_graph(registry=registry, llm=fake_llm, repo=repo)
    result = app.invoke({"incident": sample_incident(), "tickets": []})
    dossier = result["dossier"]

    assert dossier is not None
    assert dossier.conclusive is True
    assert dossier.ranked[0][0] == HypothesisID.POWER_LED_STP_OVERFLOW
    assert len(result["used_tools"]) <= 6


def test_inconclusive_scenario_terminates_at_cap():
    canned = load_fixture_evidence("evidence_inconclusive.json")
    registry = FakeToolRegistry(canned_evidence=canned)
    repo = InMemoryEvidenceRepo()

    # Provide 6 choices to let it reach step cap
    fake_llm = FakeLLM([
        ToolChoice(tool_name="rainfall", why="Check rain"),
        ToolChoice(tool_name="elevation", why="Check elevation"),
        ToolChoice(tool_name="history", why="Check history"),
        ToolChoice(tool_name="osm", why="Check OSM"),
        ToolChoice(tool_name="hotspots", why="Check hotspots"),
        ToolChoice(tool_name="outage", why="Check outage"),
    ])

    app = build_graph(registry=registry, llm=fake_llm, repo=repo)
    result = app.invoke({"incident": sample_incident(), "tickets": []})
    dossier = result["dossier"]

    assert dossier is not None
    assert dossier.conclusive is False
    assert result["step"] == 6
    assert "inconclusive" in dossier.stop_reason.lower()


def test_invalid_tool_choice_retries_and_falls_back():
    registry = FakeToolRegistry()
    repo = InMemoryEvidenceRepo()

    # Return invalid tool names twice
    fake_llm = FakeLLM([
        ToolChoice(tool_name="non_existent_tool_1", why="Testing invalid"),
        ToolChoice(tool_name="non_existent_tool_2", why="Testing invalid retry"),
        ToolChoice(tool_name="elevation", why="Follow-up"),
    ])

    app = build_graph(registry=registry, llm=fake_llm, repo=repo)
    result = app.invoke({"incident": sample_incident(), "tickets": []})

    # The first executed tool should be the first from FALLBACK_TOOL_ORDER: "rainfall"
    assert result["used_tools"][0] == "rainfall"


def test_trace_callback_emission():
    registry = FakeToolRegistry()
    repo = InMemoryEvidenceRepo()
    trace_events: list[dict[str, Any]] = []

    def on_step(evt: dict[str, Any]) -> None:
        trace_events.append(evt)

    fake_llm = FakeLLM([
        ToolChoice(tool_name="rainfall", why="Test callback 1"),
        ToolChoice(tool_name="elevation", why="Test callback 2"),
    ])

    app = build_graph(
        registry=registry,
        llm=fake_llm,
        repo=repo,
        on_step_callback=on_step,
    )
    result = app.invoke({"incident": sample_incident(), "tickets": [], "max_steps": 2})

    assert len(trace_events) == result["step"]
    for evt in trace_events:
        assert "step" in evt
        assert "tool" in evt
        assert "why" in evt
        assert "evidence_id" in evt
        assert "posterior_snapshot" in evt


def test_investigator_run_cli():
    import subprocess
    import sys

    res = subprocess.run(
        [sys.executable, "-m", "app.investigator.run", "--scenario", "rain_overwhelm"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "INVESTIGATOR RUN" in res.stdout
    assert "RAIN_OVERWHELM" in res.stdout
    assert "FINAL DOSSIER" in res.stdout

