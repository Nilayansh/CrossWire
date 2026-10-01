from __future__ import annotations

from typing import Any, Optional
import streamlit as st

from app.contracts.keys import HypothesisID
from app.contracts.models import Dossier, Evidence

PROVENANCE_BADGES = {
    "real": {
        "bg": "#064e3b",
        "text": "#a7f3d0",
        "border": "#059669",
        "label": "REAL",
    },
    "simulated": {
        "bg": "#581c87",
        "text": "#e9d5ff",
        "border": "#9333ea",
        "label": "SIMULATED",
    },
    "derived": {
        "bg": "#1e3a8a",
        "text": "#bfdbfe",
        "border": "#3b82f6",
        "label": "DERIVED",
    },
}

HYPOTHESIS_LABELS = {
    HypothesisID.RAIN_OVERWHELM: "🌧️ Rain Overwhelm (Cloudburst / Intensity)",
    HypothesisID.DRAIN_BLOCKAGE: "🧱 Stormwater Drain Blockage / Debris",
    HypothesisID.POWER_LED_STP_OVERFLOW: "⚡ Power-Led STP Tripping & Overflow",
    HypothesisID.PIPE_BURST: "🚰 BWSSB Water Supply Main Burst",
    HypothesisID.LAKE_OVERFLOW: "🌊 Bellandur/Varthur Lake Spillover",
    HypothesisID.TRAFFIC_ONLY: "🚗 Congestion / Bottleneck Only",
}


def sort_hypotheses_by_posterior(ranked: list[tuple[HypothesisID, float]]) -> list[tuple[HypothesisID, float]]:
    """Sort hypotheses by posterior probability descending."""
    return sorted(ranked, key=lambda x: x[1], reverse=True)


def get_provenance_badge_html(provenance: str) -> str:
    """Generate HTML badge for evidence provenance."""
    meta = PROVENANCE_BADGES.get(
        provenance.lower(),
        {"bg": "#334155", "text": "#cbd5e1", "border": "#64748b", "label": provenance.upper()},
    )
    return (
        f'<span style="background-color: {meta["bg"]}; color: {meta["text"]}; '
        f'border: 1px solid {meta["border"]}; font-size: 11px; padding: 2px 7px; '
        f'border-radius: 4px; font-weight: 700; letter-spacing: 0.5px;">[{meta["label"]}]</span>'
    )


def render_investigator_panel(
    dossier: Optional[Dossier],
    incident_status: str = "open",
    trace_events: Optional[list[dict[str, Any]]] = None,
) -> None:
    """Render hypothesis distribution, evidence ledger with provenance badges, and execution trace."""
    st.subheader("🔬 Autonomous Bayesian Investigator")

    if not dossier:
        st.info("Investigator has not produced a dossier yet. Ingesting tickets...")
        return

    # Header status & stop reason
    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        if dossier.conclusive:
            st.success(f"🎯 **Investigation Conclusive** (Status: `{incident_status}`)")
        else:
            st.warning(f"⚠️ **Inconclusive** — Low hypothesis margin (Status: `{incident_status}`)")
    with col_c2:
        st.caption(f"**Stopping Rule:** {dossier.stop_reason}")

    # 1. Hypothesis Posterior Distribution
    st.markdown("#### 📊 Posterior Probability Distribution")
    sorted_ranked = sort_hypotheses_by_posterior(dossier.ranked)

    for i, (hyp_id, prob) in enumerate(sorted_ranked):
        pct = round(prob * 100, 1)
        hyp_label = HYPOTHESIS_LABELS.get(hyp_id, str(hyp_id))
        is_top = i == 0 and prob >= 0.5

        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            if is_top:
                st.markdown(f"**🏆 {hyp_label}**")
            else:
                st.markdown(f"{hyp_label}")
            st.progress(float(prob))
        with col_h2:
            st.markdown(
                f"<div style='text-align: right; padding-top: 18px; font-weight: bold; font-size: 16px; color: {'#10b981' if is_top else '#94a3b8'};'>{pct}%</div>",
                unsafe_allow_html=True,
            )

    # 2. Evidence Ledger with Provenance
    st.markdown("#### 📂 Multi-Source Evidence Ledger")
    if not dossier.evidence:
        st.info("No tool evidence collected yet.")
    else:
        for ev in dossier.evidence:
            badge_html = get_provenance_badge_html(ev.provenance)
            keys_chips = " ".join([
                f'<span style="background-color: #334155; color: #f1f5f9; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-family: monospace;">{k}</span>'
                for k in ev.keys
            ])
            ts_str = ev.ts.strftime("%H:%M:%S UTC") if hasattr(ev.ts, "strftime") else str(ev.ts)

            card_html = f"""
            <div style="border: 1px solid #334155; background-color: #0f172a; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div>
                        <span style="font-weight: 700; color: #38bdf8; font-size: 13px;">🛠️ {ev.tool.upper()} TOOL</span>
                        <span style="margin-left: 8px;">{badge_html}</span>
                        <span style="margin-left: 8px; font-size: 11px; color: #64748b;">({ev.id})</span>
                    </div>
                    <span style="font-size: 11px; color: #94a3b8;">🕒 {ts_str}</span>
                </div>
                <div style="color: #e2e8f0; font-size: 13px; line-height: 1.4; margin-bottom: 6px;">
                    {ev.summary}
                </div>
                <div style="margin-top: 4px;">
                    <span style="font-size: 11px; color: #94a3b8; margin-right: 6px;">Emitted Keys:</span>
                    {keys_chips}
                </div>
                <div style="font-size: 11px; color: #64748b; margin-top: 4px;">
                    Source: <i>{ev.source}</i>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            if ev.raw:
                with st.expander(f"Inspect raw telemetry ({ev.id})", expanded=False):
                    st.json(ev.raw)

    # 3. Investigation Execution Trace
    trace_data = trace_events or dossier.trace
    if trace_data:
        with st.expander(f"🔍 Agent Reasoning Trace ({len(trace_data)} steps)", expanded=False):
            for step in trace_data:
                step_num = step.get("step", "?")
                tool = step.get("tool", "unknown")
                why = step.get("why", "")
                top_h = step.get("top_hypothesis", "")
                post = step.get("posterior", 0.0)
                st.markdown(
                    f"- **Step {step_num}**: Called `{tool}` tool.<br/>"
                    f"  *Reasoning:* {why}<br/>"
                    f"  *Posterior Snapshot:* `{top_h}` @ {round(float(post)*100, 1)}%",
                    unsafe_allow_html=True,
                )
