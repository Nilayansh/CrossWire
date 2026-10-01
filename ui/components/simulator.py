from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
import uuid
import streamlit as st

from app.contracts.models import Ticket
from app.geo.geocode import geocode
from app.geo.h3_utils import latlon_to_cell

PRESET_SCENARIOS = {
    "Bellandur Flood (Kannada)": {
        "text": "ಬೆಳ್ಳಂದೂರು ಇಕೋಸ್ಪೇಸ್ ಮುಂದೆ ಭಾರಿ ನೀರು ನಿಂತಿದೆ",
        "text_en": "Heavy water accumulation in front of Bellandur Ecospace",
        "lang": "kn",
        "category": "waterlogging",
        "severity": 4,
        "landmark": "Bellandur Ecospace",
        "photo_depth": "knee",
    },
    "Central Mall Road Inundation (English)": {
        "text": "Outer ring road service lane completely flooded near Central Mall",
        "text_en": "Outer ring road service lane completely flooded near Central Mall",
        "lang": "en",
        "category": "waterlogging",
        "severity": 4,
        "landmark": "Central Mall Bellandur",
        "photo_depth": "waist",
    },
    "Kadubeesanahalli Substation Sparking (Kannada)": {
        "text": "ವಿದ್ಯುತ್ ಕಂಬದಿಂದ ಕಿಡಿ ಬರುತ್ತಿದೆ ಮತ್ತು ಕರೆಂಟ್ ಹೋಗಿದೆ",
        "text_en": "Sparks from electric pole and power has gone off",
        "lang": "kn",
        "category": "power",
        "severity": 5,
        "landmark": "Kadubeesanahalli Substation",
        "photo_depth": None,
    },
    "BWSSB Pipeline Burst (English)": {
        "text": "Huge water pressure blasting from broken water main near HSR layout",
        "text_en": "Huge water pressure blasting from broken water main near HSR layout",
        "lang": "en",
        "category": "water_supply",
        "severity": 4,
        "landmark": "HSR Layout Sector 1",
        "photo_depth": "knee",
    },
}

LANDMARK_COORDS = {
    "Bellandur Ecospace": (12.926, 77.683),
    "Central Mall Bellandur": (12.928, 77.681),
    "Kadubeesanahalli Substation": (12.936, 77.693),
    "Marathahalli Bridge": (12.956, 77.701),
    "HSR Layout Sector 1": (12.912, 77.638),
    "Koramangala 4th Block": (12.934, 77.628),
}


def render_citizen_simulator(
    on_submit_ticket: Callable[[Ticket], None],
    on_replay_batch: Callable[[], None],
) -> None:
    """Render interactive citizen ticket submission form and batch stream replayer."""
    st.subheader("📱 Citizen Intake & Scenario Replay Simulator")

    tab_single, tab_replay = st.tabs(["📝 Submit Single Citizen Report", "⏩ Replay Flood Scenario Stream"])

    with tab_single:
        st.markdown("##### Quick-Fill Preset Scenarios")
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        selected_preset = None

        if col_p1.button("🌧️ Bellandur Flood (KN)", use_container_width=True):
            selected_preset = PRESET_SCENARIOS["Bellandur Flood (Kannada)"]
        if col_p2.button("🌊 Central Mall (EN)", use_container_width=True):
            selected_preset = PRESET_SCENARIOS["Central Mall Road Inundation (English)"]
        if col_p3.button("⚡ Substation Spark (KN)", use_container_width=True):
            selected_preset = PRESET_SCENARIOS["Kadubeesanahalli Substation Sparking (Kannada)"]
        if col_p4.button("🚰 Pipe Burst (EN)", use_container_width=True):
            selected_preset = PRESET_SCENARIOS["BWSSB Pipeline Burst (English)"]

        default_text = selected_preset["text"] if selected_preset else "ಬೆಳ್ಳಂದೂರು ಇಕೋಸ್ಪೇಸ್ ಮುಂದೆ ಭಾರಿ ನೀರು ನಿಂತಿದೆ"
        default_lang = selected_preset["lang"] if selected_preset else "kn"
        default_cat = selected_preset["category"] if selected_preset else "waterlogging"
        default_sev = selected_preset["severity"] if selected_preset else 4
        default_landmark = selected_preset["landmark"] if selected_preset else "Bellandur Ecospace"
        default_depth = selected_preset["photo_depth"] if selected_preset else "knee"

        col_in1, col_in2 = st.columns([2, 1])
        with col_in1:
            report_text = st.text_area(
                "Citizen Report Text (Kannada or English)",
                value=default_text,
                height=100,
                key="sim_report_text",
            )
        with col_in2:
            lang = st.selectbox(
                "Language",
                ["kn", "en"],
                index=0 if default_lang == "kn" else 1,
                key="sim_lang",
            )
            category = st.selectbox(
                "Category",
                [
                    "waterlogging",
                    "power",
                    "sewage",
                    "water_supply",
                    "traffic",
                    "garbage_debris",
                    "road_damage",
                    "other",
                ],
                index=0,
                key="sim_category",
            )

        col_geo1, col_geo2, col_geo3 = st.columns([1.5, 1, 1])
        with col_geo1:
            landmark_choice = st.selectbox(
                "Location / Landmark",
                list(LANDMARK_COORDS.keys()),
                index=0,
                key="sim_landmark",
            )
            lat, lon = LANDMARK_COORDS[landmark_choice]
        with col_geo2:
            severity = st.slider("Severity (1-5)", min_value=1, max_value=5, value=default_sev, key="sim_sev")
        with col_geo3:
            photo_depth_choice = st.selectbox(
                "Photo Water Depth",
                ["None", "ankle", "knee", "waist", "vehicle"],
                index=2 if default_depth == "knee" else 0,
                key="sim_depth",
            )
            depth_val = None if photo_depth_choice == "None" else photo_depth_choice

        h3_cell = latlon_to_cell(lat, lon, res=8)

        st.caption(f"📍 Resolved Coordinates: `{round(lat, 4)}, {round(lon, 4)}` | H3 Cell: `{h3_cell}`")

        if st.button("📤 Ingest Citizen Report via Intake Pipeline", type="primary", use_container_width=True):
            ticket_id = f"t-sim-{str(uuid.uuid4())[:6]}"
            new_ticket = Ticket(
                id=ticket_id,
                ts=datetime.now(timezone.utc),
                channel="telegram",
                lang=lang,
                text_original=report_text,
                text_en=report_text,  # Normalized/translated in real intake
                category=category,
                severity=severity,
                lat=lat,
                lon=lon,
                geo_confidence=0.95,
                h3_r8=h3_cell,
                photo_depth=depth_val,
                reporter_chat_id="tg-sim-user",
                is_synthetic=False,
            )
            on_submit_ticket(new_ticket)
            st.success(f"Ticket `{ticket_id}` ingested! Check ticket feed & cluster detector.")

    with tab_replay:
        st.markdown("##### 🚀 Fast-Replay Benchmark Flood Stream")
        st.markdown(
            """
            Replays 14 synthetic sensor tickets from **Bellandur 2026 Monsoon Cloudburst**:
            - Combines multi-lingual reports (Kannada + English)
            - Spans 4 distinct civic categories (Waterlogging, Power Outage, Sewage Overflow, Arterial Congestion)
            - Triggers the **Bayesian Cluster Detector** ($N \\ge 4$ tickets / $\\ge 2$ categories in 2-ring disk)
            - Kicks off the autonomous LangGraph investigator loop!
            """
        )
        if st.button("▶️ Launch Scenario Replay", type="primary", use_container_width=True):
            on_replay_batch()
            st.success("Replay batch dispatched! Incident opened and investigator activated.")
