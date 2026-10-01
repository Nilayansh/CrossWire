import csv
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.contracts.models import ToolSpec, ToolArgs, Evidence
from app.contracts.keys import HypothesisID, EvidenceKey
from app.tools._registry import register_tool
from app.tools.thresholds import HOTSPOT_MAX_RADIUS_M

spec = ToolSpec(
    name="hotspots",
    description="Cross-references incident coordinates against the BBMP Chronic Flood Hotspot Registry.",
    args_model=ToolArgs,
    provenance="derived",
    discriminates=[HypothesisID.RAIN_OVERWHELM],
)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def _get_hotspots_csv_path() -> Path:
    base_dir = Path(__file__).resolve().parent.parent.parent
    return base_dir / "data" / "hotspots.csv"


@register_tool(spec)
def run(args: ToolArgs) -> Evidence:
    csv_path = _get_hotspots_csv_path()
    matched_hotspot = None
    min_distance = float("inf")

    if csv_path.exists():
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    h_lat = float(row.get("lat", 0.0))
                    h_lon = float(row.get("lon", 0.0))
                    radius = float(row.get("radius_m", HOTSPOT_MAX_RADIUS_M))
                    dist = _haversine_m(args.lat, args.lon, h_lat, h_lon)
                    if dist <= radius and dist < min_distance:
                        min_distance = dist
                        matched_hotspot = row
                except Exception:
                    continue

    keys: list[EvidenceKey] = []
    if matched_hotspot:
        keys.append(EvidenceKey.KNOWN_HOTSPOT)
        name = matched_hotspot.get("name", "Unknown Area")
        hid = matched_hotspot.get("hotspot_id", "BLR-SWD-XXX")
        freq = matched_hotspot.get("historical_frequency", "high")
        summary = f"{name} is a recognized BBMP chronic flood hotspot ({hid}, frequency: {freq})"
        raw = {
            "hotspot_id": hid,
            "name": name,
            "distance_m": round(min_distance, 1),
            "historical_frequency": freq,
        }
    else:
        summary = "Incident location is not an officially cataloged BBMP chronic flood hotspot"
        raw = {"matched": False}

    return Evidence(
        id=f"ev-hot-{uuid.uuid4().hex[:6]}",
        tool="hotspots",
        ts=datetime.now(timezone.utc),
        summary=summary,
        keys=keys,
        source="BBMP Chronic Hotspot Registry 2024",
        provenance="derived",
        raw=raw,
    )
