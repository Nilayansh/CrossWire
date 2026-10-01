from __future__ import annotations

from typing import Callable, Optional
import streamlit as st

from app.contracts.models import Action, Decision, Incident

PRIORITY_CONFIG = {
    "P1": {"color": "#ef4444", "bg": "#450a0a", "label": "P1 - CRITICAL (Immediate)", "desc": "<15 min dispatch"},
    "P2": {"color": "#f97316", "bg": "#431407", "label": "P2 - HIGH (Rapid)", "desc": "<60 min dispatch"},
    "P3": {"color": "#3b82f6", "bg": "#172554", "label": "P3 - MEDIUM (Standard)", "desc": "<4 hr dispatch"},
}

DEPT_CONFIG = {
    "stormwater": {"label": "BBMP Stormwater", "icon": "🌧️"},
    "power_utility": {"label": "BESCOM Power", "icon": "⚡"},
    "sewerage": {"label": "BWSSB Sewerage", "icon": "🚰"},
    "traffic_police": {"label": "BTP Traffic Police", "icon": "👮"},
    "solid_waste": {"label": "BBMP Solid Waste", "icon": "🚛"},
    "water_board": {"label": "BWSSB Water Supply", "icon": "💧"},
}


def render_officer_console(
    incident: Incident,
    actions: list[Action],
    on_submit_decision: Callable[[Decision], None],
    on_fast_forward: Callable[[int], None],
) -> None:
    """Render Officer Human-In-The-Loop review, dispatch controls, and verification button."""
    st.subheader("🛡️ Municipal Officer HITL Console")

    st.markdown(
        f"""
        <div style="background-color: #1e293b; border-left: 4px solid #3b82f6; padding: 10px 14px; border-radius: 4px; margin-bottom: 14px;">
            <b>Active Incident:</b> <code>{incident.id}</code> &nbsp;|&nbsp;
            <b>Status:</b> <code>{incident.status.upper()}</code> &nbsp;|&nbsp;
            <b>Centroid:</b> <code>{round(incident.centroid[0], 4)}, {round(incident.centroid[1], 4)}</code> &nbsp;|&nbsp;
            <b>Total Tickets:</b> <code>{len(incident.ticket_ids)}</code>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not actions:
        st.info("No departmental action drafts available yet.")
        return

    st.markdown("#### 📋 Proposed Departmental Orders")

    approved_action_ids: list[str] = []
    rejected_reasons: dict[str, str] = {}
    edited_actions: dict[str, str] = {}

    for i, act in enumerate(actions, start=1):
        act_id = act.id or f"act-{i}"
        p_info = PRIORITY_CONFIG.get(act.priority, {"color": "#64748b", "bg": "#1e293b", "label": act.priority, "desc": ""})
        dept_info = DEPT_CONFIG.get(act.dept, {"label": act.dept.upper(), "icon": "🏛️"})

        border_color = p_info["color"] if act.priority == "P1" else "#334155"

        with st.container():
            st.markdown(
                f"""
                <div style="border: 1px solid {border_color}; background-color: #0f172a; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div>
                            <span style="font-weight: 700; color: #f8fafc; font-size: 14px;">{dept_info['icon']} {dept_info['label']}</span>
                            <span style="margin-left: 8px; background-color: {p_info['bg']}; color: {p_info['color']}; border: 1px solid {p_info['color']}; font-size: 11px; padding: 2px 7px; border-radius: 4px; font-weight: 700;">
                                {p_info['label']}
                            </span>
                            <span style="margin-left: 8px; font-size: 11px; color: #64748b;">(Confidence: {round(act.confidence * 100, 1)}%)</span>
                        </div>
                        <span style="font-size: 11px; color: #94a3b8;">{act_id}</span>
                    </div>
                    <div style="color: #f1f5f9; font-size: 13.5px; font-weight: 500; margin: 6px 0;">
                        {act.action}
                    </div>
                    <div style="color: #94a3b8; font-size: 12px; margin-bottom: 4px;">
                        <b>Rationale:</b> {act.rationale}
                    </div>
                    <div style="font-size: 11px; color: #64748b;">
                        <b>Evidence Justification:</b> {', '.join(act.evidence_ids) if act.evidence_ids else 'None'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if act.needs_field_verification:
                st.warning("⚠️ Low confidence warning: Action requires mandatory field inspection before heavy machinery dispatch.")

            col_a1, col_a2 = st.columns([1, 2])
            with col_a1:
                is_approved = st.checkbox(
                    f"Approve {act_id}",
                    value=True,
                    key=f"chk_approve_{act_id}_{incident.id}",
                )
            with col_a2:
                if not is_approved:
                    reason = st.text_input(
                        f"Rejection Reason for {act_id}",
                        value="Redundant with existing ground crew",
                        key=f"txt_reject_{act_id}_{incident.id}",
                    )
                    rejected_reasons[act_id] = reason
                else:
                    approved_action_ids.append(act_id)

    st.markdown("---")

    # Decision Submission Form
    col_d1, col_d2 = st.columns([2, 1])
    with col_d1:
        officer_name = st.text_input(
            "Officer Digital Signature",
            value="Chief Disaster Officer, BBMP Control Cell",
            key=f"officer_name_{incident.id}",
        )
    with col_d2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 Sign & Dispatch Orders", type="primary", use_container_width=True):
            decision = Decision(
                incident_id=incident.id,
                approved_action_ids=approved_action_ids,
                rejected=rejected_reasons,
                edits=edited_actions,
                officer=officer_name,
            )
            on_submit_decision(decision)

    # Fast Forward / Verification section
    st.markdown("---")
    st.markdown("#### ⏩ Post-Dispatch Verification")
    col_v1, col_v2 = st.columns([2, 1])
    with col_v1:
        st.caption("Simulate 45-minute elapsed time to trigger automated resolution verifier (ticket decay, weather cessation, traffic recovery).")
    with col_v2:
        if st.button("⏩ Fast-Forward 45 Min", use_container_width=True):
            on_fast_forward(45)
