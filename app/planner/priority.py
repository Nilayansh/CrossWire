from __future__ import annotations

from typing import Any, Literal
from app.config import settings


def vulnerability(osm_context: dict[str, Any]) -> float:
    """Computes a vulnerability index in [0.0, 1.0] from OSM context.
    
    Factors:
    - Arterial road / primary transit route
    - Proximity to nearest hospital
    - Proximity to nearest school
    """
    v = 0.0
    if osm_context.get("on_arterial", False):
        v += 0.40

    h_dist = osm_context.get("hospital_dist_m")
    if h_dist is not None:
        if h_dist <= 500:
            v += 0.35
        elif h_dist <= 1000:
            v += 0.20
        elif h_dist <= 2000:
            v += 0.10

    s_dist = osm_context.get("school_dist_m")
    if s_dist is not None:
        if s_dist <= 500:
            v += 0.25
        elif s_dist <= 1000:
            v += 0.15
        elif s_dist <= 2000:
            v += 0.05

    return min(max(v, 0.0), 1.0)


def score(
    severity_norm: float,
    velocity: float,
    vulnerability: float,
    confidence: float,
) -> tuple[float, dict[str, float]]:
    """Calculates weighted priority score and breakdown.
    
    Formula:
        priority_score = 0.35 * severity + 0.25 * velocity + 0.25 * vulnerability + 0.15 * confidence
    """
    breakdown = {
        "severity": settings.WEIGHT_SEVERITY * max(0.0, min(1.0, severity_norm)),
        "velocity": settings.WEIGHT_VELOCITY * max(0.0, min(1.0, velocity)),
        "vulnerability": settings.WEIGHT_VULNERABILITY * max(0.0, min(1.0, vulnerability)),
        "confidence": settings.WEIGHT_CONFIDENCE * max(0.0, min(1.0, confidence)),
    }
    total = sum(breakdown.values())
    return min(max(total, 0.0), 1.0), breakdown


def to_band(score_val: float) -> Literal["P1", "P2", "P3"]:
    """Maps priority score in [0.0, 1.0] to operational bands P1, P2, P3."""
    if score_val >= 0.70:
        return "P1"
    elif score_val >= 0.40:
        return "P2"
    else:
        return "P3"
