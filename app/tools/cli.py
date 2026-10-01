import argparse
import json
import sys
from datetime import datetime, timezone, timedelta

from app.contracts.models import ToolArgs
from app.tools._registry import discover, get_registry


def main():
    parser = argparse.ArgumentParser(description="Run any NammaTwin tool and print Evidence output.")
    parser.add_argument(
        "tool",
        nargs="?",
        default="all",
        help="Name of the tool to execute (rainfall, elevation, osm, history, hotspots, outage, traffic, or all)",
    )
    parser.add_argument("--lat", type=float, default=12.93, help="Latitude (default: 12.93)")
    parser.add_argument("--lon", type=float, default=77.68, help="Longitude (default: 77.68)")
    parser.add_argument(
        "--t0",
        type=str,
        default=None,
        help="Start timestamp ISO (default: 1 hour ago)",
    )
    parser.add_argument(
        "--t1",
        type=str,
        default=None,
        help="End timestamp ISO (default: now)",
    )
    parser.add_argument("--incident-id", type=str, default="inc-demo-001", help="Incident ID")
    parser.add_argument("--cells", nargs="*", default=["886189255bfffff"], help="List of H3 cells")

    args = parser.parse_args()

    # Discover all tools in app.tools
    reg = discover()

    now = datetime.now(timezone.utc)
    t1 = datetime.fromisoformat(args.t1) if args.t1 else now
    t0 = datetime.fromisoformat(args.t0) if args.t0 else (t1 - timedelta(hours=1))

    tool_args = ToolArgs(
        incident_id=args.incident_id,
        lat=args.lat,
        lon=args.lon,
        t0=t0,
        t1=t1,
        cells=args.cells,
    )

    tools_to_run = list(reg.keys()) if args.tool == "all" else [args.tool]

    for tool_name in tools_to_run:
        if tool_name not in reg:
            print(f"Error: Unknown tool '{tool_name}'. Available: {list(reg.keys())}", file=sys.stderr)
            continue

        spec, handler = reg[tool_name]
        print(f"\n=== Running tool: {tool_name} [{spec.provenance}] ===")
        evidence = handler(tool_args)
        print(json.dumps(evidence.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
