import json
from pathlib import Path

DEMO_AREAS = [
    {
        "name": "Bellandur Ecospace",
        "lat": 12.93,
        "lon": 77.68,
        "rainfall": {
            "latitude": 12.93,
            "longitude": 77.68,
            "hourly": {
                "time": [f"2026-09-05T{h:02d}:00" for h in range(24)],
                "precipitation": [0.0, 0.0, 1.2, 5.4, 18.2, 47.2, 38.5, 12.0, 4.2, 1.0] + [0.0] * 14,
            },
            "precipitation_mm": 47.2,
            "sustained_24h": 127.7,
        },
        "elevation": {
            "results": [
                {"latitude": 12.93, "longitude": 77.68, "elevation": 872.1},
                {"latitude": 12.934, "longitude": 77.683, "elevation": 876.5},
                {"latitude": 12.928, "longitude": 77.686, "elevation": 875.8},
                {"latitude": 12.924, "longitude": 77.678, "elevation": 877.2},
                {"latitude": 12.932, "longitude": 77.674, "elevation": 876.1},
                {"latitude": 12.936, "longitude": 77.680, "elevation": 876.3},
            ],
            "centroid_elevation_m": 872.1,
            "surrounding_median_m": 876.3,
        },
        "osm": {
            "lake_dist_m": 420.0,
            "stp_dist_m": 310.0,
            "hospital_dist_m": 1200.0,
            "school_dist_m": 800.0,
            "on_arterial": True,
        },
        "traffic": {
            "flowSegmentData": {
                "frc": "FRC2",
                "currentSpeed": 11.0,
                "freeFlowSpeed": 48.0,
                "currentTravelTime": 320,
                "freeFlowTravelTime": 75,
                "confidence": 0.95,
            },
            "current_speed": 11.0,
            "free_flow_speed": 48.0,
        },
        "outage": {
            "feeder": "F-KADU-04",
            "substation": "Kadubeesanahalli 66/11kV",
            "status": "tripped",
            "outage_reported": True,
            "outage_start": "2026-09-05T07:10:00Z",
        },
    },
    {
        "name": "Central Mall Bellandur",
        "lat": 12.93,
        "lon": 77.68,
        # Re-uses the rounded 12.93/77.68 coordinates
    },
]


def prefetch():
    cache_dir = Path(__file__).resolve().parent.parent / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"Pre-warming caches in {cache_dir}...")
    for area in DEMO_AREAS:
        lat = area["lat"]
        lon = area["lon"]
        for tool_name in ["rainfall", "elevation", "osm", "traffic", "outage"]:
            if tool_name in area:
                cache_file = cache_dir / f"{tool_name}_{lat}_{lon}.json"
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(area[tool_name], f, indent=2)
                print(f"  + Cached {cache_file.name}")

    print("Pre-warming complete!")


if __name__ == "__main__":
    prefetch()
