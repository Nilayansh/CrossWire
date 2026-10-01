import h3
from typing import Optional


def latlon_to_cell(lat: float, lon: float, res: int = 8) -> str:
    """Convert latitude/longitude to an H3 cell index at the specified resolution."""
    if hasattr(h3, "latlng_to_cell"):
        return h3.latlng_to_cell(lat, lon, res)
    return h3.geo_to_h3(lat, lon, res)  # pragma: no cover


def cell_to_latlon(cell: str) -> tuple[float, float]:
    """Convert an H3 cell index back to (latitude, longitude) center coordinates."""
    if hasattr(h3, "cell_to_latlng"):
        return h3.cell_to_latlng(cell)
    return h3.h3_to_geo(cell)  # pragma: no cover


def neighbors(cell: str, k: int = 2) -> list[str]:
    """Return all H3 cells within a k-ring disk around the cell (including the center cell)."""
    if hasattr(h3, "grid_disk"):
        return list(h3.grid_disk(cell, k))
    return list(h3.k_ring(cell, k))  # pragma: no cover


def cell_distance(origin: str, destination: str) -> int:
    """Return the grid distance (number of hops) between two cells."""
    if hasattr(h3, "grid_distance"):
        return h3.grid_distance(origin, destination)
    return h3.h3_distance(origin, destination)  # pragma: no cover
