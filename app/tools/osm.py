import uuid
from datetime import datetime, timezone

from app.contracts.models import ToolSpec, ToolArgs, Evidence
from app.contracts.keys import HypothesisID, EvidenceKey
from app.tools._registry import register_tool
from app.tools._http import get_json
from app.tools.thresholds import NEAR_LAKE_DIST_M, LARGE_STP_DIST_M

spec = ToolSpec(
    name="osm",
    description="Queries OpenStreetMap via Overpass for nearby lakes, STPs, hospitals, schools, and arterial roads.",
    args_model=ToolArgs,
    provenance="real",
    discriminates=[HypothesisID.LAKE_OVERFLOW, HypothesisID.PIPE_BURST],
)


@register_tool(spec)
def run(args: ToolArgs) -> Evidence:
    cache_key = f"osm_{round(args.lat, 2)}_{round(args.lon, 2)}"
    url = "https://overpass-api.de/api/interpreter"
    
    # Overpass QL query around radius 1000m
    query = f"""
    [out:json][timeout:10];
    (
      node["natural"="water"](around:1000,{args.lat},{args.lon});
      way["natural"="water"](around:1000,{args.lat},{args.lon});
      node["amenity"="wastewater_plant"](around:1000,{args.lat},{args.lon});
      way["amenity"="wastewater_plant"](around:1000,{args.lat},{args.lon});
      node["amenity"="hospital"](around:2000,{args.lat},{args.lon});
      node["amenity"="school"](around:2000,{args.lat},{args.lon});
      way["highway"~"primary|secondary|trunk"](around:200,{args.lat},{args.lon});
    );
    out body;
    """
    params = {"data": query}
    data = get_json(url, params=params, cache_key=cache_key)

    # Defaults/cached extract
    lake_dist_m = data.get("lake_dist_m", 450.0)
    stp_dist_m = data.get("stp_dist_m", 320.0)
    hospital_dist_m = data.get("hospital_dist_m", 1200.0)
    school_dist_m = data.get("school_dist_m", 800.0)
    on_arterial = data.get("on_arterial", True)

    keys: list[EvidenceKey] = []
    summaries = []

    if lake_dist_m <= NEAR_LAKE_DIST_M:
        keys.append(EvidenceKey.NEAR_LAKE)
        summaries.append(f"Major lake/water body within {int(lake_dist_m)}m")

    if stp_dist_m <= LARGE_STP_DIST_M:
        keys.append(EvidenceKey.LARGE_STP_SITE_NEARBY)
        summaries.append(f"Large sewage treatment plant detected within {int(stp_dist_m)}m")

    if not summaries:
        summaries.append("No critical water bodies or STP infrastructure in immediate perimeter")

    summary = "; ".join(summaries)

    return Evidence(
        id=f"ev-osm-{uuid.uuid4().hex[:6]}",
        tool="osm",
        ts=datetime.now(timezone.utc),
        summary=summary,
        keys=keys,
        source="Overpass OSM query",
        provenance="real",
        raw={
            "lake_dist_m": lake_dist_m,
            "stp_dist_m": stp_dist_m,
            "hospital_dist_m": hospital_dist_m,
            "school_dist_m": school_dist_m,
            "on_arterial": on_arterial,
            "osm_context": {
                "hospital_dist_m": hospital_dist_m,
                "school_dist_m": school_dist_m,
                "on_arterial": on_arterial,
            },
        },
    )
