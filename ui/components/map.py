from __future__ import annotations

from typing import Any, Optional
import pydeck as pdk
import streamlit as st

from app.contracts.models import Incident, Ticket

# Pre-defined critical infrastructure nodes in Bangalore SE tech corridor
CRITICAL_INFRASTRUCTURE = [
    {
        "name": "Sakra World Hospital",
        "type": "hospital",
        "lat": 12.9261,
        "lon": 77.6838,
        "color": [239, 68, 68, 220],  # Red
        "radius": 45,
    },
    {
        "name": "Manipal Hospital Sarjapur",
        "type": "hospital",
        "lat": 12.9185,
        "lon": 77.6715,
        "color": [239, 68, 68, 220],
        "radius": 45,
    },
    {
        "name": "Kadubeesanahalli 11kV Substation",
        "type": "substation",
        "lat": 12.9362,
        "lon": 77.6934,
        "color": [168, 85, 247, 230],  # Purple
        "radius": 40,
    },
    {
        "name": "Bellandur STP Facility",
        "type": "sewage_treatment",
        "lat": 12.9340,
        "lon": 77.6720,
        "color": [14, 165, 233, 230],  # Cyan
        "radius": 50,
    },
    {
        "name": "Greenwood High Preschool",
        "type": "school",
        "lat": 12.9230,
        "lon": 77.6775,
        "color": [234, 179, 8, 220],  # Amber
        "radius": 35,
    },
    {
        "name": "Central Mall ORR Junction",
        "type": "chokepoint",
        "lat": 12.9282,
        "lon": 77.6814,
        "color": [249, 115, 22, 220],  # Orange
        "radius": 40,
    },
]


def build_h3_layer_data(incident: Optional[Incident], tickets: list[Ticket]) -> list[dict[str, Any]]:
    """Aggregate tickets by H3 cell to calculate density and elevation."""
    cell_counts: dict[str, int] = {}
    cell_severities: dict[str, list[int]] = {}

    for t in tickets:
        hex_id = t.h3_r8
        cell_counts[hex_id] = cell_counts.get(hex_id, 0) + 1
        cell_severities.setdefault(hex_id, []).append(t.severity)

    if incident:
        for c in incident.cells:
            cell_counts.setdefault(c, 1)
            cell_severities.setdefault(c, [3])

    records: list[dict[str, Any]] = []
    max_count = max(cell_counts.values()) if cell_counts else 1

    for hex_id, count in cell_counts.items():
        ratio = count / max(max_count, 1)
        # Gradient: low count = yellow/orange, high count = intense crimson
        r = int(220 + 35 * ratio)
        g = int(max(40, 200 * (1 - ratio)))
        b = int(40 * (1 - ratio))
        records.append({
            "hex": hex_id,
            "count": count,
            "avg_severity": round(sum(cell_severities[hex_id]) / len(cell_severities[hex_id]), 1),
            "color": [r, g, b, 170],
            "elevation": count * 60,
        })
    return records


def render_map(
    incident: Optional[Incident],
    tickets: list[Ticket],
    height: int = 420,
) -> None:
    """Render Pydeck H3HexagonLayer, ticket points, and critical infrastructure markers."""
    if incident:
        center_lat, center_lon = incident.centroid
    elif tickets:
        center_lat = sum(t.lat for t in tickets) / len(tickets)
        center_lon = sum(t.lon for t in tickets) / len(tickets)
    else:
        center_lat, center_lon = 12.928, 77.683

    h3_data = build_h3_layer_data(incident, tickets)

    ticket_points = [
        {
            "id": t.id,
            "category": t.category,
            "severity": t.severity,
            "lang": t.lang,
            "lat": t.lat,
            "lon": t.lon,
            "color": [59, 130, 246, 200] if not t.is_synthetic else [147, 51, 234, 180],
            "radius": 15 + t.severity * 5,
        }
        for t in tickets
    ]

    centroid_point = []
    if incident:
        centroid_point.append({
            "name": f"Incident {incident.id} (Centroid)",
            "lat": incident.centroid[0],
            "lon": incident.centroid[1],
            "color": [255, 0, 50, 255],
            "radius": 60,
        })

    layers: list[pdk.Layer] = [
        pdk.Layer(
            "H3HexagonLayer",
            data=h3_data,
            pickable=True,
            stroked=True,
            filled=True,
            extruded=True,
            get_hexagon="hex",
            get_fill_color="color",
            get_line_color=[255, 255, 255, 120],
            line_width_min_pixels=1.5,
            get_elevation="elevation",
            elevation_scale=1.5,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data=ticket_points,
            pickable=True,
            opacity=0.8,
            stroked=True,
            filled=True,
            radius_scale=1,
            radius_min_pixels=4,
            radius_max_pixels=14,
            line_width_min_pixels=1,
            get_position=["lon", "lat"],
            get_fill_color="color",
            get_line_color=[255, 255, 255, 200],
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data=CRITICAL_INFRASTRUCTURE,
            pickable=True,
            opacity=0.9,
            stroked=True,
            filled=True,
            radius_min_pixels=6,
            radius_max_pixels=16,
            line_width_min_pixels=2,
            get_position=["lon", "lat"],
            get_fill_color="color",
            get_line_color=[255, 255, 255, 230],
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data=centroid_point,
            pickable=True,
            opacity=0.95,
            stroked=True,
            filled=True,
            radius_min_pixels=9,
            radius_max_pixels=22,
            line_width_min_pixels=2.5,
            get_position=["lon", "lat"],
            get_fill_color="color",
            get_line_color=[255, 255, 255, 255],
        ),
    ]

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=13.8,
        pitch=45,
        bearing=15,
    )

    tooltip = {
        "html": (
            "<b>{name}</b><br/>"
            "<b>Cell:</b> {hex}<br/>"
            "<b>Tickets:</b> {count}<br/>"
            "<b>Avg Severity:</b> {avg_severity}<br/>"
            "<b>Category:</b> {category}<br/>"
            "<b>Type:</b> {type}"
        ),
        "style": {
            "backgroundColor": "#1e293b",
            "color": "white",
            "fontSize": "12px",
            "padding": "8px",
            "borderRadius": "6px",
            "border": "1px solid #475569",
        },
    }

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v11",
        tooltip=tooltip,
    )

    st.pydeck_chart(deck, use_container_width=True, height=height)

    # Legend
    st.markdown(
        """
        <div style="display: flex; gap: 14px; font-size: 11px; color: #94a3b8; margin-top: -8px; padding-bottom: 8px; flex-wrap: wrap;">
            <span><span style="color: #ef4444;">●</span> Hospital</span>
            <span><span style="color: #a855f7;">●</span> Substation</span>
            <span><span style="color: #0ea5e9;">●</span> STP / Lake Inlet</span>
            <span><span style="color: #eab308;">●</span> School</span>
            <span><span style="color: #3b82f6;">●</span> Citizen Ticket</span>
            <span><span style="color: #9333ea;">●</span> Synthetic Sensor</span>
            <span><span style="color: #ef4444; font-weight: bold;">⬢</span> H3 Cell Density</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
