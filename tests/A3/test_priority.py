import pytest

from app.planner.priority import score, to_band, vulnerability


def test_vulnerability_bounds_and_structure():
    ctx = {
        "hospital_dist_m": 450.0,
        "school_dist_m": 800.0,
        "on_arterial": True,
    }
    v = vulnerability(ctx)
    assert isinstance(v, float)
    assert 0.0 <= v <= 1.0


def test_vulnerability_monotonicity():
    base_ctx = {
        "hospital_dist_m": 3000.0,
        "school_dist_m": 3000.0,
        "on_arterial": False,
    }
    base_v = vulnerability(base_ctx)

    arterial_ctx = dict(base_ctx, on_arterial=True)
    assert vulnerability(arterial_ctx) > base_v

    close_hospital_ctx = dict(base_ctx, hospital_dist_m=300.0)
    assert vulnerability(close_hospital_ctx) > base_v

    close_school_ctx = dict(base_ctx, school_dist_m=300.0)
    assert vulnerability(close_school_ctx) > base_v


def test_score_and_breakdown():
    total, breakdown = score(
        severity_norm=0.8,
        velocity=0.6,
        vulnerability=0.7,
        confidence=0.9,
    )
    assert isinstance(total, float)
    assert 0.0 <= total <= 1.0
    assert set(breakdown.keys()) == {"severity", "velocity", "vulnerability", "confidence"}
    
    # Check weighted sum matches weights (0.35, 0.25, 0.25, 0.15)
    expected = 0.35 * 0.8 + 0.25 * 0.6 + 0.25 * 0.7 + 0.15 * 0.9
    assert abs(total - expected) < 1e-4
    assert abs(sum(breakdown.values()) - total) < 1e-4


def test_to_band_values():
    assert to_band(0.95) == "P1"
    assert to_band(0.75) == "P1"
    assert to_band(0.55) == "P2"
    assert to_band(0.20) == "P3"


def test_priority_monotonicity_with_vulnerability():
    """Higher vulnerability never lowers the band."""
    band_order = {"P3": 1, "P2": 2, "P1": 3}
    for vuln in [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
        s, _ = score(severity_norm=0.6, velocity=0.5, vulnerability=vuln, confidence=0.8)
        band = to_band(s)
        # Higher vulnerability test
        s_higher, _ = score(severity_norm=0.6, velocity=0.5, vulnerability=min(vuln + 0.2, 1.0), confidence=0.8)
        band_higher = to_band(s_higher)
        assert band_order[band_higher] >= band_order[band]
