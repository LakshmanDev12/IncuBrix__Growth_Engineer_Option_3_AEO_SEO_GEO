"""Citation Explorer for IncuBrix 30-Target Authority Opportunity Matrix."""

from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd
import streamlit as st

try:
    from ui_components import (
        get_api_data,
        get_api_text,
        post_api_data,
        render_page_header,
        render_kpi_card,
        render_empty_state,
        render_sidebar_global,
    )
except ImportError:
    from app.frontend.ui_components import (
        get_api_data,
        get_api_text,
        post_api_data,
        render_page_header,
        render_kpi_card,
        render_empty_state,
        render_sidebar_global,
    )

filters = render_sidebar_global()

render_page_header(
    title="Citation Explorer",
    subtitle="High-impact third-party citation opportunities, competitor mention gaps, and legitimate outreach angles.",
    breadcrumb="Content & Audits / Citation Explorer",
    badge_text="Authority Matrix",
)

# Toolbar Row
col_t1, col_t2 = st.columns([0.7, 0.3], vertical_alignment="bottom")
with col_t1:
    st.caption("Inspect and target 30 verified third-party publications and creator hubs where Vk Analysis can acquire high-impact citations.")
with col_t2:
    if st.button("Seed 30 Citation Targets", key="btn_seed_citations", type="primary"):
        with st.spinner("Seeding authority target catalog..."):
            res = post_api_data("/citations/seed-catalog")
            if res:
                st.toast(f"Seeded {res.get('total_seeded')} citation opportunities!", icon=":material/check_circle:")
                st.rerun()
            else:
                st.error("Failed to seed citation catalog.")

st.space("small")

# Fetch Citation Targets
targets = get_api_data("/citations/targets", params={"limit": 100}) or []

if not targets:
    render_empty_state(
        title="No Citation Targets Stored",
        description="The citation opportunity matrix is currently empty. Click 'Seed 30 Citation Targets' to load real industry opportunities.",
        icon=":material/share:",
        action_label="Seed 30 Citation Targets",
        action_key="empty_seed_cites_btn",
    )
else:
    # Summary Metrics
    avg_da = sum(t.get("authority_score", 0) for t in targets) // len(targets) if targets else 0
    competitor_gaps = sum(1 for t in targets if t.get("competitor_domain"))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card(label="Citation Opportunities", value=len(targets))
    with col2:
        render_kpi_card(label="Average Domain Authority", value=f"DA {avg_da}")
    with col3:
        render_kpi_card(label="Competitor Gaps", value=competitor_gaps, help_text="Articles currently citing a competitor but missing Vk Analysis.")
    with col4:
        # Download button
        csv_text = get_api_text("/reports/export/citation_targets.csv")
        if csv_text:
            st.download_button(
                "Export Targets CSV",
                data=csv_text,
                file_name="citation_targets.csv",
                mime="text/csv",
                key="btn_dl_citations_csv",
            )
        else:
            st.button("Export Targets CSV", disabled=True)

    st.space("medium")

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        gap_types = ["All"] + sorted(list({t.get("gap_type") for t in targets if t.get("gap_type")}))
        gap_filter = st.selectbox("Filter Gap Type", gap_types, key="cite_gap_filter")
    with col_f2:
        domain_search = st.text_input("Search Domain or Keyword", key="cite_domain_search", placeholder="e.g. forbes, substack...")

    filtered_targets = targets
    if gap_filter != "All":
        filtered_targets = [t for t in filtered_targets if t.get("gap_type") == gap_filter]
    if domain_search.strip():
        filtered_targets = [
            t for t in filtered_targets
            if domain_search.lower() in t.get("target_domain", "").lower()
            or domain_search.lower() in t.get("pitch_angle", "").lower()
        ]

    st.markdown(f"### Opportunity Matrix ({len(filtered_targets)} Targets)")

    for t in filtered_targets:
        da = t.get("authority_score") or "N/A"
        domain = t.get("target_domain") or "Authority Site"
        gap = t.get("gap_type", "opportunity").upper()
        
        with st.expander(f":violet-badge[DA: {da}] **{domain}** | :blue-badge[{gap}]"):
            col_l, col_r = st.columns([0.65, 0.35])
            with col_l:
                target_url = t.get("target_url")
                st.markdown(f"**Target URL**: [{target_url}]({target_url})")
                st.write(f"**Relevance**: {t.get('relevance')}")
            with col_r:
                comp = t.get("competitor_domain")
                st.write(f"**Competitor Mentioned**: `{comp if comp else 'None (Unlinked / Organic)'}`")
                st.write(f"**Domain Authority**: `{da}`")
            
            with st.container(border=True):
                st.caption("Legitimate Outreach Pitch Angle")
                st.markdown(f"_{t.get('pitch_angle')}_")
