from __future__ import annotations

import os
import sys
from pathlib import Path
import streamlit as st

# Add project root to sys.path so app modules are resolvable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.contracts.models import Decision, Ticket
from ui.api_client import ApiClient
from ui.components.console import render_officer_console
from ui.components.feed import render_ticket_feed
from ui.components.impact import render_impact_tab
from ui.components.investigator import render_investigator_panel
from ui.components.map import render_map
from ui.components.simulator import render_citizen_simulator

# Page configuration
st.set_page_config(
    page_title="NammaTwin v2 — Civic Infrastructure Control Room",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_client() -> ApiClient:
    """Retrieve or initialize the API client in session state."""
    if "api_client" not in st.session_state:
        # Check if mock mode was forced via env var or query params
        force_mock = os.getenv("USE_MOCK_API", "0") in ("1", "true", "True")
        st.session_state.api_client = ApiClient(use_mock=force_mock)
    return st.session_state.api_client


def main() -> None:
    client = get_client()

    # --- SIDEBAR ---
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
            <span style="font-size: 28px;">🏙️</span>
            <div>
                <div style="font-weight: 800; font-size: 18px; color: #f8fafc; letter-spacing: -0.5px;">NammaTwin v2</div>
                <div style="font-size: 11px; color: #94a3b8;">Tickets Are The Sensors</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # API Connection Mode toggle
    is_healthy = client.is_healthy()
    if is_healthy and not client.use_mock and not client.is_mock_fallback:
        st.sidebar.success("🟢 API Connected (`localhost:8000`)")
    else:
        st.sidebar.warning("🟡 Standalone Mode (Mock Fixtures)")

    use_mock_toggle = st.sidebar.checkbox(
        "Force Standalone Mock Mode",
        value=client.use_mock,
        help="Run entirely from offline fixture JSONs without requiring the FastAPI backend server.",
        key="mock_mode_toggle",
    )
    if use_mock_toggle != client.use_mock:
        client.use_mock = use_mock_toggle
        st.rerun()

    st.sidebar.markdown("---")

    # Fetch Incidents
    incidents = client.get_incidents()
    incident_map = {inc.id: inc for inc in incidents}

    st.sidebar.markdown(f"**Active Incidents ({len(incidents)})**")
    if incidents:
        selected_id = st.sidebar.selectbox(
            "Select Incident",
            options=list(incident_map.keys()),
            format_func=lambda i_id: f"{i_id} ({incident_map[i_id].status.upper()})",
            key="selected_incident_id",
        )
    else:
        selected_id = None
        st.sidebar.info("No active incidents found.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**System Telemetry**")
    st.sidebar.caption("🌐 **LLM Engine:** Universal Adapter (Dual-Mode)")
    st.sidebar.caption("🗺️ **Spatial Partition:** Uber H3 Resolution 8")
    st.sidebar.caption("🚦 **Traffic Sensor:** TomTom Free Tier Flow API")
    st.sidebar.caption("🗣️ **STT/Translation:** Sarvam AI / Kannada NLP")
    st.sidebar.caption("⏱️ **Debounce:** 5-min Window Debounce")

    if st.sidebar.button("🔄 Refresh State", use_container_width=True):
        st.rerun()

    # --- MAIN CONTENT ---
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h2 style="margin: 0; color: #f8fafc; font-weight: 800; font-size: 26px;">
                🏙️ NammaTwin v2 — Urban Infrastructure Incident Control Room
            </h2>
            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 14px;">
                Autonomous Multi-Agency Root Cause Diagnostics & Dispatch &bull; Bengaluru South-East Disaster Cell
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_control, tab_sim, tab_impact, tab_arch = st.tabs([
        "🚨 Incident Control Room",
        "📱 Citizen Intake Simulator",
        "📈 Backtest Benchmark & Impact",
        "🏛️ Multi-Agency Architecture",
    ])

    # 1. CONTROL ROOM TAB
    with tab_control:
        if not selected_id:
            st.info("No active incident. Use the Citizen Intake Simulator tab to trigger a flood scenario!")
        else:
            detail = client.get_incident(selected_id)
            incident = detail.incident
            dossier = detail.dossier
            actions = detail.actions
            status = detail.status
            trace_events = client.get_trace_events(selected_id)

            # Retrieve tickets for this incident (from mock or client)
            all_tickets = client.mock_backend.tickets
            incident_tickets = [t for t in all_tickets if t.id in incident.ticket_ids]
            display_tickets = incident_tickets if incident_tickets else all_tickets

            # Layout: 3 Columns (Ticket Feed | Pydeck Map | Investigator)
            col_feed, col_map, col_inv = st.columns([3.2, 4.8, 4.0])

            with col_feed:
                render_ticket_feed(display_tickets)

            with col_map:
                st.subheader(f"🗺️ Spatial Intelligence ({len(display_tickets)} tickets)")
                render_map(incident=incident, tickets=display_tickets, height=520)

            with col_inv:
                render_investigator_panel(
                    dossier=dossier,
                    incident_status=status,
                    trace_events=trace_events,
                )

            st.markdown("---")

            # Officer HITL Console
            def handle_decision(decision: Decision) -> None:
                res = client.submit_decision(selected_id, decision)
                st.success(f"Dispatched {len(decision.approved_action_ids)} orders! Incident marked as `{res.get('status', 'dispatched')}`.")
                st.rerun()

            def handle_fast_forward(minutes: int) -> None:
                res = client.verify_incident(selected_id, fast_forward_min=minutes)
                st.info(f"Verified incident status after {minutes} minutes: `{res.status}` (Resolution confirmed).")
                st.rerun()

            render_officer_console(
                incident=incident,
                actions=actions,
                on_submit_decision=handle_decision,
                on_fast_forward=handle_fast_forward,
            )

    # 2. CITIZEN SIMULATOR TAB
    with tab_sim:
        def handle_submit_ticket(t: Ticket) -> None:
            resp = client.ingest_ticket(t)
            if resp.incident_id:
                st.success(f"Report ingested! Assigned to Incident `{resp.incident_id}`.")
            else:
                st.info("Report ingested. Awaiting clustering threshold (>= 4 tickets / >= 2 categories).")

        def handle_replay_batch() -> None:
            tickets = client.mock_backend.tickets
            for t in tickets:
                client.ingest_ticket(t)
            st.success("Replayed 14 flood tickets into the cluster detector!")
            st.rerun()

        render_citizen_simulator(
            on_submit_ticket=handle_submit_ticket,
            on_replay_batch=handle_replay_batch,
        )

    # 3. IMPACT & EVALUATION TAB
    with tab_impact:
        render_impact_tab()

    # 4. SYSTEM ARCHITECTURE TAB
    with tab_arch:
        st.subheader("🏛️ Multi-Agency Urban Infrastructure Agent Architecture")
        st.markdown(
            """
            ```mermaid
            flowchart TD
                A["Citizen Tickets (Kannada & English Telegram/Web)"] --> B["Intake Normalization (Sarvam STT + Multimodal Vision)"]
                B --> C["H3 Spatial Clustering (Res-8, 2-Ring Disk, 60-min Window)"]
                C --> D{"Threshold Met?<br/>>= 4 tickets / >= 2 categories"}
                D -- No --> E["Hold in Spatial Ticket Buffer"]
                D -- Yes --> F["Open Incident (Awaiting Investigation)"]
                F --> G["Bayesian Investigator Loop (LangGraph)"]
                G <--> H["Multi-Source Tool Registry<br/>(Rainfall, Elevation, OSM, History, Outage, TomTom Traffic)"]
                G --> I["Diagnostic Dossier (Top Hypothesis & Posterior)"]
                I --> J["Action Planner (Multi-Department Priority P1/P2/P3)"]
                J --> K["Officer HITL Console (Approve / Edit / Reject)"]
                K --> L["Multi-Channel Notifier (Telegram Bot + Outbox)"]
                L --> M["Resolution Verifier (45-min Fast-Forward)"]
            ```
            """,
            unsafe_allow_html=True,
        )

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.markdown("#### 🛠️ Tool Registry & Evidence Provenance")
            st.markdown(
                """
                - **Rainfall Tool** (`rainfall.py`): Real Open-Meteo precipitation & archive telemetry (`RAIN_GT_25`, `SUSTAINED_RAIN_24H`).
                - **Elevation Tool** (`elevation.py`): Real SRTM raster topographic analysis (`LOW_LYING`).
                - **OSM Query Tool** (`osm.py`): Real Overpass API query for critical infrastructure (`LARGE_STP_SITE_NEARBY`, `NEAR_LAKE`).
                - **History Tool** (`history.py`): Real internal DB spatio-temporal lag analyzer (`POWER_TICKETS_PRECEDE_SEWAGE`).
                - **Hotspots Tool** (`hotspots.py`): Derived gazetteer lookup (`KNOWN_HOTSPOT`).
                - **Outage Sim Tool** (`outage_sim.py`): Simulated BESCOM substation feeder status (`OUTAGE_REPORTED`).
                - **TomTom Traffic Tool** (`traffic.py`): Live/Real TomTom free tier flow segment telemetry (`TRAFFIC_SLOWDOWN`).
                """
            )
        with col_a2:
            st.markdown("#### 🎯 Strict Epistemic Guardrails")
            st.markdown(
                r"""
                - **Immutable Evidence:** Tools emit strictly typed `EvidenceKey` members; LLMs never calculate mathematical probabilities directly.
                - **Bayesian Normalization:** Posterior updates are closed-form softmax log-odds equations.
                - **Provenance Badging:** Every piece of evidence carries an explicit provenance tag (`[REAL]`, `[SIMULATED]`, `[DERIVED]`).
                - **Field Verification Guardrail:** If hypothesis confidence is $< 60\%$, remedial actions automatically enforce mandatory field verification before heavy machinery is deployed.
                """
            )


if __name__ == "__main__":
    main()
