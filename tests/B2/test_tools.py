import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from app.contracts.models import ToolArgs, Evidence, Ticket
from app.contracts.keys import EvidenceKey, HypothesisID
from app.tools._registry import discover, get_registry
from app.stubs.in_memory_repos import InMemoryTicketRepo
import app.tools.rainfall as rainfall_tool
import app.tools.elevation as elevation_tool
import app.tools.traffic as traffic_tool
import app.tools.hotspots as hotspots_tool
import app.tools.history as history_tool
import app.tools.osm as osm_tool
import app.tools.outage_sim as outage_tool


@pytest.fixture(autouse=True)
def setup_tools():
    discover()


def test_discover_finds_all_tools():
    reg = discover()
    expected_tools = {"rainfall", "elevation", "osm", "history", "hotspots", "outage", "traffic"}
    assert expected_tools.issubset(set(reg.keys()))

    for tool_name, (spec, handler) in reg.items():
        assert len(spec.description) > 0, f"Tool {tool_name} must have a non-empty description"
        assert spec.args_model == ToolArgs
        assert spec.provenance in ("real", "simulated", "derived")
        assert len(spec.discriminates) > 0
        assert callable(handler)


def test_every_tool_runs_in_demo_mode_returns_valid_evidence():
    reg = discover()
    sample_args = ToolArgs(
        incident_id="inc-test-01",
        lat=12.93,
        lon=77.68,
        t0=datetime(2026, 9, 5, 7, 0, 0, tzinfo=timezone.utc),
        t1=datetime(2026, 9, 5, 8, 0, 0, tzinfo=timezone.utc),
        cells=["886189255bfffff"],
    )

    for tool_name, (spec, handler) in reg.items():
        evidence = handler(sample_args)
        assert isinstance(evidence, Evidence), f"Tool {tool_name} did not return an Evidence object"
        assert evidence.tool == tool_name
        assert evidence.provenance == spec.provenance
        assert len(evidence.summary) > 0
        assert evidence.ts.tzinfo is not None

        # Assert every key emitted is a member of EvidenceKey enum
        for key in evidence.keys:
            assert isinstance(key, EvidenceKey), f"Tool {tool_name} emitted invalid key {key}"
            assert key in EvidenceKey


def test_rainfall_threshold_26mm_yields_gt25_and_not_gt40():
    args = ToolArgs(
        incident_id="inc-test",
        lat=12.93,
        lon=77.68,
        t0=datetime.now(timezone.utc),
        t1=datetime.now(timezone.utc),
    )

    fake_data = {
        "hourly": {"precipitation": [26.0] + [0.0] * 23},
        "precipitation_mm": 26.0,
        "sustained_24h": 30.0,
    }

    with patch("app.tools.rainfall.get_json", return_value=fake_data):
        ev = rainfall_tool.run(args)
        assert EvidenceKey.RAIN_GT_25 in ev.keys
        assert EvidenceKey.RAIN_GT_40 not in ev.keys
        assert EvidenceKey.SUSTAINED_RAIN_24H not in ev.keys


def test_rainfall_heavy_and_sustained():
    args = ToolArgs(
        incident_id="inc-test",
        lat=12.93,
        lon=77.68,
        t0=datetime.now(timezone.utc),
        t1=datetime.now(timezone.utc),
    )

    fake_data = {
        "hourly": {"precipitation": [48.0] + [2.0] * 23},
        "precipitation_mm": 48.0,
        "sustained_24h": 94.0,
    }

    with patch("app.tools.rainfall.get_json", return_value=fake_data):
        ev = rainfall_tool.run(args)
        assert EvidenceKey.RAIN_GT_40 in ev.keys
        assert EvidenceKey.RAIN_GT_25 in ev.keys
        assert EvidenceKey.SUSTAINED_RAIN_24H in ev.keys


def test_rainfall_dry_weather():
    args = ToolArgs(
        incident_id="inc-test",
        lat=12.93,
        lon=77.68,
        t0=datetime.now(timezone.utc),
        t1=datetime.now(timezone.utc),
    )

    fake_data = {
        "hourly": {"precipitation": [0.2] + [0.0] * 23},
        "precipitation_mm": 0.2,
        "sustained_24h": 0.2,
    }

    with patch("app.tools.rainfall.get_json", return_value=fake_data):
        ev = rainfall_tool.run(args)
        assert EvidenceKey.RAIN_LT_15 in ev.keys
        assert EvidenceKey.RAIN_LT_5 in ev.keys
        assert EvidenceKey.DRY_WEATHER in ev.keys
        assert EvidenceKey.RAIN_GT_25 not in ev.keys


def test_elevation_bowl_and_flat_thresholds():
    args = ToolArgs(
        incident_id="inc-test",
        lat=12.93,
        lon=77.68,
        t0=datetime.now(timezone.utc),
        t1=datetime.now(timezone.utc),
    )

    # 1. Bowl depression (4.2m below median)
    bowl_data = {
        "results": [
            {"elevation": 872.0},
            {"elevation": 876.2},
            {"elevation": 876.5},
            {"elevation": 876.0},
        ]
    }
    with patch("app.tools.elevation.get_json", return_value=bowl_data):
        ev = elevation_tool.run(args)
        assert EvidenceKey.LOW_LYING in ev.keys

    # 2. Flat terrain (0.3m difference)
    flat_data = {
        "results": [
            {"elevation": 876.0},
            {"elevation": 876.3},
            {"elevation": 876.1},
            {"elevation": 876.4},
        ]
    }
    with patch("app.tools.elevation.get_json", return_value=flat_data):
        ev = elevation_tool.run(args)
        assert EvidenceKey.LOW_LYING not in ev.keys


def test_traffic_slowdown_threshold():
    args = ToolArgs(
        incident_id="inc-test",
        lat=12.93,
        lon=77.68,
        t0=datetime.now(timezone.utc),
        t1=datetime.now(timezone.utc),
    )

    # 1. Slowdown (15 km/h vs 50 km/h = 0.30 <= 0.50)
    slow_data = {
        "flowSegmentData": {"currentSpeed": 15.0, "freeFlowSpeed": 50.0}
    }
    with patch("app.tools.traffic.get_json", return_value=slow_data):
        ev = traffic_tool.run(args)
        assert EvidenceKey.TRAFFIC_SLOWDOWN in ev.keys

    # 2. Normal flow (42 km/h vs 50 km/h = 0.84 > 0.50)
    normal_data = {
        "flowSegmentData": {"currentSpeed": 42.0, "freeFlowSpeed": 50.0}
    }
    with patch("app.tools.traffic.get_json", return_value=normal_data):
        ev = traffic_tool.run(args)
        assert EvidenceKey.TRAFFIC_SLOWDOWN not in ev.keys


def test_hotspots_catalog_match():
    # Ecospace coordinates (should match BLR-SWD-042)
    args_match = ToolArgs(
        incident_id="inc-test",
        lat=12.926,
        lon=77.683,
        t0=datetime.now(timezone.utc),
        t1=datetime.now(timezone.utc),
    )
    ev_match = hotspots_tool.run(args_match)
    assert EvidenceKey.KNOWN_HOTSPOT in ev_match.keys
    assert "Bellandur Ecospace" in ev_match.summary

    # Far coordinates (should not match)
    args_nomatch = ToolArgs(
        incident_id="inc-test",
        lat=13.15,
        lon=77.85,
        t0=datetime.now(timezone.utc),
        t1=datetime.now(timezone.utc),
    )
    ev_nomatch = hotspots_tool.run(args_nomatch)
    assert EvidenceKey.KNOWN_HOTSPOT not in ev_nomatch.keys


def test_history_tool_analysis():
    repo = InMemoryTicketRepo()
    history_tool.set_ticket_repo(repo)

    t0 = datetime(2026, 9, 5, 7, 0, 0, tzinfo=timezone.utc)
    # Add debris ticket
    repo.add(
        Ticket(
            id="t-deb-1",
            ts=t0 + timedelta(minutes=5),
            channel="web",
            lang="en",
            text_original="debris",
            text_en="debris",
            category="garbage_debris",
            severity=3,
            lat=12.926,
            lon=77.683,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        )
    )
    # Add power ticket at 07:10
    repo.add(
        Ticket(
            id="t-pwr-1",
            ts=t0 + timedelta(minutes=10),
            channel="web",
            lang="en",
            text_original="power",
            text_en="power",
            category="power",
            severity=4,
            lat=12.926,
            lon=77.683,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        )
    )
    # Add sewage ticket at 07:45 (preceded by power by 35 min)
    repo.add(
        Ticket(
            id="t-swg-1",
            ts=t0 + timedelta(minutes=45),
            channel="web",
            lang="en",
            text_original="sewage",
            text_en="sewage",
            category="sewage",
            severity=4,
            lat=12.926,
            lon=77.683,
            geo_confidence=0.9,
            h3_r8="886189255bfffff",
        )
    )

    args = ToolArgs(
        incident_id="inc-test",
        lat=12.926,
        lon=77.683,
        t0=t0,
        t1=t0 + timedelta(hours=1),
        cells=["886189255bfffff"],
    )

    ev = history_tool.run(args)
    assert EvidenceKey.DEBRIS_TICKETS_NEARBY in ev.keys
    assert EvidenceKey.POWER_TICKETS_PRECEDE_SEWAGE in ev.keys
    assert EvidenceKey.LOCALIZED_SPREAD in ev.keys


@pytest.mark.live
def test_live_smoke():
    """Opt-in live smoke test querying real open API."""
    import httpx
    resp = httpx.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": 12.93, "longitude": 77.68, "hourly": "precipitation"},
        timeout=10.0,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "hourly" in data
