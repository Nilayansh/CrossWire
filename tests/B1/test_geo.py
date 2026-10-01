import pytest
from app.geo.h3_utils import latlon_to_cell, cell_to_latlon, neighbors, cell_distance
from app.geo.geocode import geocode


def test_latlon_to_cell_and_reverse():
    lat, lon = 12.926, 77.683
    cell = latlon_to_cell(lat, lon, res=8)
    assert isinstance(cell, str)
    assert len(cell) == 15

    rev_lat, rev_lon = cell_to_latlon(cell)
    assert pytest.approx(rev_lat, abs=0.02) == lat
    assert pytest.approx(rev_lon, abs=0.02) == lon


def test_neighbors():
    lat, lon = 12.926, 77.683
    cell = latlon_to_cell(lat, lon, res=8)

    k1 = neighbors(cell, k=1)
    assert len(k1) == 7
    assert cell in k1

    k2 = neighbors(cell, k=2)
    assert len(k2) == 19
    assert cell in k2


def test_cell_distance():
    lat, lon = 12.926, 77.683
    cell = latlon_to_cell(lat, lon, res=8)
    assert cell_distance(cell, cell) == 0

    k1 = [c for c in neighbors(cell, k=1) if c != cell]
    assert cell_distance(cell, k1[0]) == 1


def test_geocode_with_pin():
    lat, lon, conf = geocode("Flooding reported near office", pin="560103")
    assert pytest.approx(lat, abs=0.01) == 12.926
    assert pytest.approx(lon, abs=0.01) == 77.683
    assert conf >= 0.90


def test_geocode_embedded_pin():
    lat, lon, conf = geocode("Major waterlogging in area 560037 near main road")
    assert pytest.approx(lat, abs=0.02) == 12.956
    assert pytest.approx(lon, abs=0.02) == 77.701
    assert conf >= 0.85


def test_geocode_landmark_fuzzy_english():
    lat, lon, conf = geocode("Heavy water accumulation in front of Bellandur Ecospace")
    assert pytest.approx(lat, abs=0.01) == 12.926
    assert pytest.approx(lon, abs=0.01) == 77.683
    assert conf >= 0.80

    lat_m, lon_m, conf_m = geocode("Traffic jam near Central Mall outer ring road")
    assert pytest.approx(lat_m, abs=0.02) == 12.928
    assert pytest.approx(lon_m, abs=0.02) == 77.681
    assert conf_m >= 0.70


def test_geocode_kannada_landmark():
    lat, lon, conf = geocode("ಬೆಳ್ಳಂದೂರು ಇಕೋಸ್ಪೇಸ್ ಮುಂದೆ ಭಾರಿ ನೀರು ನಿಂತಿದೆ")
    assert pytest.approx(lat, abs=0.01) == 12.926
    assert pytest.approx(lon, abs=0.01) == 77.683
    assert conf >= 0.80


def test_geocode_fallback():
    lat, lon, conf = geocode("Random unknown place without any landmark or pin")
    assert pytest.approx(lat, abs=0.01) == 12.9716
    assert pytest.approx(lon, abs=0.01) == 77.5946
    assert conf <= 0.30
