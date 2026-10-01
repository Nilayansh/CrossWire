from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from backtest.generate_tickets import generate_cluster_tickets

scenarios_dir = Path("backtest/scenarios")
scenarios_dir.mkdir(parents=True, exist_ok=True)

start_t = datetime(2026, 9, 5, 8, 0, tzinfo=timezone.utc)

configs = [
    {
        "id": "scen_rain_bellandur_01",
        "loc": "Bellandur Ecospace",
        "cat": "waterlogging",
        "gt_hyp": "RAIN_OVERWHELM",
        "gt_depts": ["stormwater", "traffic_police"],
        "keys": ["RAIN_GT_40", "RAIN_GT_25", "LOW_LYING", "KNOWN_HOTSPOT"],
    },
    {
        "id": "scen_rain_silkboard_02",
        "loc": "Silk Board Junction",
        "cat": "waterlogging",
        "gt_hyp": "RAIN_OVERWHELM",
        "gt_depts": ["stormwater", "traffic_police"],
        "keys": ["RAIN_GT_25", "LOW_LYING", "KNOWN_HOTSPOT", "SUSTAINED_RAIN_24H"],
    },
    {
        "id": "scen_rain_hebbal_03",
        "loc": "Bellandur Ecospace",
        "cat": "waterlogging",
        "gt_hyp": "RAIN_OVERWHELM",
        "gt_depts": ["stormwater", "traffic_police"],
        "keys": ["RAIN_GT_40", "KNOWN_HOTSPOT", "SUSTAINED_RAIN_24H"],
    },
    {
        "id": "scen_drain_koramangala_04",
        "loc": "Koramangala 4th Block",
        "cat": "waterlogging",
        "gt_hyp": "DRAIN_BLOCKAGE",
        "gt_depts": ["stormwater", "solid_waste"],
        "keys": ["DEBRIS_TICKETS_NEARBY", "LOCALIZED_SPREAD", "RAIN_LT_15"],
    },
    {
        "id": "scen_drain_indiranagar_05",
        "loc": "Koramangala 4th Block",
        "cat": "garbage_debris",
        "gt_hyp": "DRAIN_BLOCKAGE",
        "gt_depts": ["stormwater", "solid_waste"],
        "keys": ["DEBRIS_TICKETS_NEARBY", "LOCALIZED_SPREAD", "RAIN_LT_5"],
    },
    {
        "id": "scen_drain_whitefield_06",
        "loc": "Bellandur Ecospace",
        "cat": "garbage_debris",
        "gt_hyp": "DRAIN_BLOCKAGE",
        "gt_depts": ["stormwater", "solid_waste"],
        "keys": ["DEBRIS_TICKETS_NEARBY", "KNOWN_HOTSPOT", "DRY_WEATHER"],
    },
    {
        "id": "scen_stp_kadubeesanahalli_07",
        "loc": "Kadubeesanahalli ORR",
        "cat": "power",
        "gt_hyp": "POWER_LED_STP_OVERFLOW",
        "gt_depts": ["power_utility", "sewerage"],
        "keys": ["POWER_TICKETS_PRECEDE_SEWAGE", "OUTAGE_REPORTED", "LARGE_STP_SITE_NEARBY"],
    },
    {
        "id": "scen_stp_marathahalli_08",
        "loc": "Kadubeesanahalli ORR",
        "cat": "sewage",
        "gt_hyp": "POWER_LED_STP_OVERFLOW",
        "gt_depts": ["power_utility", "sewerage"],
        "keys": ["POWER_TICKETS_PRECEDE_SEWAGE", "LARGE_STP_SITE_NEARBY"],
    },
    {
        "id": "scen_stp_mahadevapura_09",
        "loc": "Kadubeesanahalli ORR",
        "cat": "power",
        "gt_hyp": "POWER_LED_STP_OVERFLOW",
        "gt_depts": ["power_utility", "sewerage"],
        "keys": ["POWER_TICKETS_PRECEDE_SEWAGE", "OUTAGE_REPORTED"],
    },
    {
        "id": "scen_pipe_ejipura_10",
        "loc": "Koramangala 4th Block",
        "cat": "waterlogging",
        "gt_hyp": "PIPE_BURST",
        "gt_depts": ["water_board"],
        "keys": ["LINEAR_SPREAD", "DRY_WEATHER", "RAIN_LT_5"],
    },
    {
        "id": "scen_pipe_hsr_11",
        "loc": "Silk Board Junction",
        "cat": "waterlogging",
        "gt_hyp": "PIPE_BURST",
        "gt_depts": ["water_board"],
        "keys": ["LINEAR_SPREAD", "LOCALIZED_SPREAD", "DRY_WEATHER"],
    },
    {
        "id": "scen_lake_bellandur_12",
        "loc": "Bellandur Ecospace",
        "cat": "waterlogging",
        "gt_hyp": "LAKE_OVERFLOW",
        "gt_depts": ["stormwater"],
        "keys": ["NEAR_LAKE", "SUSTAINED_RAIN_24H", "RAIN_GT_25"],
    },
    {
        "id": "scen_lake_varthur_13",
        "loc": "Varthur Kodi",
        "cat": "waterlogging",
        "gt_hyp": "LAKE_OVERFLOW",
        "gt_depts": ["stormwater"],
        "keys": ["NEAR_LAKE", "SUSTAINED_RAIN_24H", "LOW_LYING"],
    },
    {
        "id": "scen_traffic_tin_factory_14",
        "loc": "Tin Factory KR Puram",
        "cat": "traffic",
        "gt_hyp": "TRAFFIC_ONLY",
        "gt_depts": ["traffic_police"],
        "keys": ["TRAFFIC_SLOWDOWN", "NO_WATER_POWER_SIGNAL", "DRY_WEATHER"],
    },
    {
        "id": "scen_traffic_goraguntepalya_15",
        "loc": "Tin Factory KR Puram",
        "cat": "traffic",
        "gt_hyp": "TRAFFIC_ONLY",
        "gt_depts": ["traffic_police"],
        "keys": ["TRAFFIC_SLOWDOWN", "NO_WATER_POWER_SIGNAL"],
    },
    {
        "id": "scen_ambiguous_low_signals_16",
        "loc": "Koramangala 4th Block",
        "cat": "waterlogging",
        "gt_hyp": "DRAIN_BLOCKAGE",
        "gt_depts": ["stormwater", "solid_waste"],
        "keys": ["RAIN_LT_5", "DRY_WEATHER"],
    },
    {
        "id": "scen_ambiguous_mixed_signals_17",
        "loc": "Bellandur Ecospace",
        "cat": "waterlogging",
        "gt_hyp": "RAIN_OVERWHELM",
        "gt_depts": ["stormwater"],
        "keys": ["RAIN_LT_15", "LOW_LYING"],
    },
]

for cfg in configs:
    prefix_str = f"t-{cfg['id'][:6]}"
    tickets = generate_cluster_tickets(
        prefix=prefix_str,
        locality_name=cfg["loc"],
        start_time=start_t,
        count=8,
        dominant_category=cfg["cat"],
    )

    ev_overrides = []
    for idx, k in enumerate(cfg["keys"]):
        ev_overrides.append({
            "id": f"ev-{cfg['id']}-{idx+1}",
            "tool": "evidence_tool",
            "ts": start_t.isoformat(),
            "summary": f"Observed evidence signal: {k}",
            "keys": [k],
            "source": "backtest_synthetic",
            "provenance": "derived",
            "raw": {"key": k},
        })

    scenario_data = {
        "id": cfg["id"],
        "tickets": [t.model_dump(mode="json") for t in tickets],
        "evidence_overrides": ev_overrides,
        "ground_truth_hypothesis": cfg["gt_hyp"],
        "ground_truth_depts": cfg["gt_depts"],
    }

    file_path = scenarios_dir / f"{cfg['id']}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(scenario_data, f, indent=2)

print(f"Successfully generated {len(configs)} scenario JSON files in {scenarios_dir}")
