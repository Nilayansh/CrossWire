import uuid
from datetime import datetime, timezone

from app.contracts.models import ToolSpec, ToolArgs, Evidence
from app.contracts.keys import HypothesisID, EvidenceKey
from app.tools._registry import register_tool
from app.tools._http import get_json

spec = ToolSpec(
    name="outage",
    description="Queries utility grid outage and substation trip records in the feeder area.",
    args_model=ToolArgs,
    provenance="simulated",
    discriminates=[HypothesisID.POWER_LED_STP_OVERFLOW],
)


@register_tool(spec)
def run(args: ToolArgs) -> Evidence:
    cache_key = f"outage_{round(args.lat, 2)}_{round(args.lon, 2)}"
    cached_data = get_json("https://bescom.simulated.internal/feeders", cache_key=cache_key)

    is_tripped = cached_data.get("status") == "tripped" or cached_data.get("outage_reported", True)
    feeder = cached_data.get("feeder", "F-KADU-04")
    outage_start = cached_data.get("outage_start", "2026-09-05T07:10:00Z")

    keys: list[EvidenceKey] = []
    if is_tripped:
        keys.append(EvidenceKey.OUTAGE_REPORTED)
        summary = f"11kV feeder trip confirmed at {feeder} substation"
    else:
        summary = "No active feeder outages or substation trips detected in feeder sector"

    return Evidence(
        id=f"ev-outage-{uuid.uuid4().hex[:6]}",
        tool="outage",
        ts=datetime.now(timezone.utc),
        summary=summary,
        keys=keys,
        source="BESCOM feeder status adapter",
        provenance="simulated",
        raw={
            "feeder": feeder,
            "status": "tripped" if is_tripped else "nominal",
            "outage_start": outage_start,
        },
    )
