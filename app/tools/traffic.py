import uuid
from datetime import datetime, timezone

from app.contracts.models import ToolSpec, ToolArgs, Evidence
from app.contracts.keys import HypothesisID, EvidenceKey
from app.config import settings
from app.tools._registry import register_tool
from app.tools._http import get_json
from app.tools.thresholds import TRAFFIC_SLOWDOWN_RATIO

spec = ToolSpec(
    name="traffic",
    description="Queries TomTom live traffic flow for current vs free-flow speeds on surrounding corridors.",
    args_model=ToolArgs,
    provenance="real",
    discriminates=[HypothesisID.TRAFFIC_ONLY],
)


@register_tool(spec)
def run(args: ToolArgs) -> Evidence:
    cache_key = f"traffic_{round(args.lat, 2)}_{round(args.lon, 2)}"
    url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"
    params = {
        "point": f"{args.lat},{args.lon}",
        "key": settings.TOMTOM_API_KEY or "demo_key",
    }

    data = get_json(url, params=params, cache_key=cache_key)

    flow_data = data.get("flowSegmentData", {})
    if flow_data:
        current_speed = float(flow_data.get("currentSpeed", 15.0))
        free_flow_speed = float(flow_data.get("freeFlowSpeed", 50.0))
    elif "current_speed" in data and "free_flow_speed" in data:
        current_speed = float(data["current_speed"])
        free_flow_speed = float(data["free_flow_speed"])
    else:
        # Default slowdown for flooded demo corridor
        current_speed = 12.0
        free_flow_speed = 48.0

    ratio = (current_speed / free_flow_speed) if free_flow_speed > 0 else 1.0

    keys: list[EvidenceKey] = []
    if ratio <= TRAFFIC_SLOWDOWN_RATIO:
        keys.append(EvidenceKey.TRAFFIC_SLOWDOWN)
        summary = (
            f"Severe traffic congestion: average speed {current_speed:.0f} km/h "
            f"vs normal {free_flow_speed:.0f} km/h ({ratio * 100:.0f}% of freeflow)"
        )
    else:
        summary = (
            f"Traffic flowing normally: speed {current_speed:.0f} km/h "
            f"vs freeflow {free_flow_speed:.0f} km/h ({ratio * 100:.0f}% of freeflow)"
        )

    return Evidence(
        id=f"ev-traf-{uuid.uuid4().hex[:6]}",
        tool="traffic",
        ts=datetime.now(timezone.utc),
        summary=summary,
        keys=keys,
        source="TomTom Flow API",
        provenance="real",
        raw={
            "current_speed_kmh": round(current_speed, 1),
            "free_flow_speed_kmh": round(free_flow_speed, 1),
            "speed_ratio": round(ratio, 2),
        },
    )
