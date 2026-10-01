from __future__ import annotations

from typing import Optional
import streamlit as st

from app.contracts.models import Ticket

CATEGORY_COLORS = {
    "waterlogging": "#0284c7",    # Sky blue
    "power": "#eab308",           # Yellow
    "sewage": "#854d0e",          # Amber/brown
    "water_supply": "#06b6d4",    # Cyan
    "traffic": "#ea580c",         # Orange
    "garbage_debris": "#64748b",  # Slate
    "road_damage": "#dc2626",     # Red
    "other": "#6b7280",           # Gray
}


def get_lang_badge(lang: str) -> str:
    """Return flag badge for ticket language."""
    if lang.lower() == "kn":
        return "🇮🇳 KN"
    elif lang.lower() == "en":
        return "🇬🇧 EN"
    return f"🌐 {lang.upper()}"


def render_ticket_feed(
    tickets: list[Ticket],
    max_items: int = 50,
) -> None:
    """Render interactive ticket sensor stream."""
    st.subheader(f"📡 Ticket Sensor Stream ({len(tickets)})")

    if not tickets:
        st.info("No tickets ingested yet. Submit a report or replay a scenario.")
        return

    # Filter controls
    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        categories = ["All"] + sorted(list({t.category for t in tickets}))
        selected_cat = st.selectbox("Category Filter", categories, index=0, key="feed_cat_filter")
    with col_f2:
        source_filter = st.selectbox(
            "Source Filter",
            ["All", "Citizen Only", "Synthetic Only"],
            index=0,
            key="feed_src_filter",
        )

    search_query = st.text_input("🔍 Search tickets...", "", key="feed_search")

    filtered = tickets
    if selected_cat != "All":
        filtered = [t for t in filtered if t.category == selected_cat]

    if source_filter == "Citizen Only":
        filtered = [t for t in filtered if not t.is_synthetic]
    elif source_filter == "Synthetic Only":
        filtered = [t for t in filtered if t.is_synthetic]

    if search_query.strip():
        q = search_query.lower()
        filtered = [
            t for t in filtered
            if q in t.text_original.lower() or q in t.text_en.lower() or q in t.category.lower()
        ]

    st.caption(f"Showing {min(len(filtered), max_items)} of {len(filtered)} matching tickets")

    feed_container = st.container(height=520)
    with feed_container:
        for t in filtered[:max_items]:
            cat_color = CATEGORY_COLORS.get(t.category, "#64748b")
            lang_badge = get_lang_badge(t.lang)
            synth_tag = (
                '<span style="background-color: #581c87; color: #e9d5ff; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600;">SYNTHETIC</span>'
                if t.is_synthetic
                else '<span style="background-color: #064e3b; color: #a7f3d0; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600;">CITIZEN</span>'
            )
            depth_tag = (
                f'<span style="background-color: #1e3a8a; color: #bfdbfe; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600;">DEPTH: {t.photo_depth.upper()}</span>'
                if t.photo_depth
                else ""
            )

            ts_str = t.ts.strftime("%H:%M:%S UTC") if hasattr(t.ts, "strftime") else str(t.ts)

            card_html = f"""
            <div style="border: 1px solid #334155; background-color: #1e293b; border-radius: 8px; padding: 10px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <div>
                        <span style="font-weight: 700; color: #f8fafc; font-size: 12px;">{t.id}</span>
                        <span style="margin-left: 6px; font-size: 11px; color: #94a3b8;">{lang_badge}</span>
                        <span style="margin-left: 6px; background-color: {cat_color}; color: white; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600;">{t.category.upper()}</span>
                        <span style="margin-left: 4px;">{synth_tag}</span>
                        {f'<span style="margin-left: 4px;">{depth_tag}</span>' if depth_tag else ''}
                    </div>
                    <span style="font-size: 11px; color: #cbd5e1;">Sev: <b>{t.severity}/5</b></span>
                </div>
                <div style="color: #f1f5f9; font-size: 13px; margin-top: 4px; line-height: 1.4;">
                    {t.text_original}
                </div>
                {f'<div style="color: #94a3b8; font-size: 12px; font-style: italic; margin-top: 2px;">🇬🇧 {t.text_en}</div>' if t.lang.lower() == 'kn' and t.text_en != t.text_original else ''}
                <div style="display: flex; justify-content: space-between; font-size: 10px; color: #64748b; margin-top: 6px;">
                    <span>📍 {round(t.lat, 4)}, {round(t.lon, 4)} (Cell: <code>{t.h3_r8[:8]}...</code>)</span>
                    <span>🕒 {ts_str}</span>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
