"""Settings & System Diagnostics for IncuBrix Visibility Intelligence."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List
import streamlit as st

try:
    from ui_components import (
        API_BASE_URL,
        get_api_data,
        get_api_text,
        render_page_header,
        render_sidebar_global,
    )
except ImportError:
    from app.frontend.ui_components import (
        API_BASE_URL,
        get_api_data,
        get_api_text,
        render_page_header,
        render_sidebar_global,
    )

filters = render_sidebar_global()

render_page_header(
    title="Settings & System Diagnostics",
    subtitle="Configure default markets, inspect provider readiness without exposing secrets, and download executive data exports.",
    breadcrumb="System / Settings",
    badge_text="System Configuration",
)

tab_exports, tab_providers, tab_config = st.tabs([
    "📥 Data Export Center",
    "🔌 Provider Configuration",
    "⚙️ Environment & API Diagnostics",
])

# -----------------------------------------------------------------------------
# Tab 1: Data Export Center
# -----------------------------------------------------------------------------
with tab_exports:
    st.markdown("### Official Submission Data Exports")
    st.caption("Standard RFC 4180 CSV exports and weekly executive markdown intelligence brief.")
    
    col_e1, col_e2, col_e3 = st.columns(3)
    
    with col_e1:
        with st.container(border=True):
            st.markdown("#### :material/table_chart: visibility.csv")
            st.caption("All evaluated search rankings and AI observations with strict provenance.")
            vis_csv = get_api_text("/reports/export/visibility.csv")
            if vis_csv:
                st.download_button(
                    "Download visibility.csv",
                    data=vis_csv,
                    file_name="visibility.csv",
                    mime="text/csv",
                    key="btn_dl_vis_csv_settings",
                    type="primary",
                )
            else:
                st.button("Download visibility.csv", disabled=True, key="dis_vis_csv")

    with col_e2:
        with st.container(border=True):
            st.markdown("#### :material/verified_user: technical_fixes.csv")
            st.caption("20 prioritized technical crawlability fixes with code patches and validation evidence.")
            fixes_csv = get_api_text("/reports/export/technical_fixes.csv")
            if fixes_csv:
                st.download_button(
                    "Download technical_fixes.csv",
                    data=fixes_csv,
                    file_name="technical_fixes.csv",
                    mime="text/csv",
                    key="btn_dl_fixes_csv_settings",
                    type="primary",
                )
            else:
                st.button("Download technical_fixes.csv", disabled=True, key="dis_fixes_csv")

    with col_e3:
        with st.container(border=True):
            st.markdown("#### :material/share: citation_targets.csv")
            st.caption("30-target citation opportunity matrix with authority scores and outreach angles.")
            cite_csv = get_api_text("/reports/export/citation_targets.csv")
            if cite_csv:
                st.download_button(
                    "Download citation_targets.csv",
                    data=cite_csv,
                    file_name="citation_targets.csv",
                    mime="text/csv",
                    key="btn_dl_cite_csv_settings",
                    type="primary",
                )
            else:
                st.button("Download citation_targets.csv", disabled=True, key="dis_cite_csv")

    st.space("medium")
    st.markdown("### Weekly Executive Intelligence Brief")
    weekly_brief = get_api_data("/reports/weekly", params={"save_to_disk": False})
    if weekly_brief and weekly_brief.get("markdown_content"):
        st.download_button(
            "Download weekly_report.md",
            data=weekly_brief["markdown_content"],
            file_name=f"weekly_report_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            key="btn_dl_weekly_brief_settings",
        )
        with st.expander("Preview Executive Brief Content", icon=":material/visibility:"):
            st.markdown(weekly_brief["markdown_content"])
    else:
        st.info("Weekly intelligence report is currently generating or backend unreachable.")

# -----------------------------------------------------------------------------
# Tab 2: Provider Configuration
# -----------------------------------------------------------------------------
with tab_providers:
    st.markdown("### Provider Readiness & Live Search Capabilities")
    st.caption("Inspecting engine credentials safely without exposing sensitive tokens.")
    
    assistants = get_api_data("/geo/assistants") or []
    if assistants:
        for ast in assistants:
            is_cfg = ast.get("is_configured", False)
            status_badge = ":green-badge[ACTIVE & CONFIGURED]" if is_cfg else ":gray-badge[UNCONFIGURED (FALLBACK)]"
            
            with st.container(border=True):
                col_p1, col_p2 = st.columns([0.7, 0.3])
                with col_p1:
                    st.markdown(f"**{ast.get('provider_type', '').upper()}** — {status_badge}")
                    st.caption(f"Model: `{ast.get('model_name')}` | Live Web Access: `{'Supported' if ast.get('supports_live_search') else 'Static Training'}`")
                with col_p2:
                    if is_cfg:
                        st.write("Auth Token: `••••••••••••`")
                    else:
                        st.caption("Add key to `.env` to enable live provider harvest.")
    else:
        st.caption("Unable to load provider configuration status.")

# -----------------------------------------------------------------------------
# Tab 3: Environment & API Diagnostics
# -----------------------------------------------------------------------------
with tab_config:
    st.markdown("### System Architecture Diagnostics")
    st.caption("Diagnostic telemetry for development and deployment runtime.")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        with st.container(border=True):
            st.markdown("#### API Server Gateway")
            st.write(f"**Base URL**: `{API_BASE_URL}`")
            # Health test
            summary = get_api_data("/summary")
            if summary:
                st.write(":green-badge[STATUS: ONLINE & RESPONSIVE]")
                st.caption(f"Total Questions Stored: **{summary.get('total_questions', 0)}**")
                st.caption(f"Total Observations: **{summary.get('total_observations', 0)}**")
            else:
                st.write(":red-badge[STATUS: BACKEND UNREACHABLE]")
                st.caption("Ensure FastAPI backend is running on `127.0.0.1:8001`.")

    with col_d2:
        with st.container(border=True):
            st.markdown("#### Database Engine")
            st.write("**Engine**: SQLite (SQLAlchemy ORM)")
            st.write("**File**: `data/incubrix_visibility.db`")
            st.write(":green-badge[SCHEMA: SYNCHRONIZED & MIGRATED]")

    st.space("medium")
    st.markdown("### Unit Cost Rate Benchmarks")
    st.caption("Standard rates used for cost estimation across search and generative AI providers.")
    cost_rates = get_api_data("/pipeline/cost-rates") or {}
    if cost_rates:
        rate_cols = st.columns(len(cost_rates))
        for idx, (k, v) in enumerate(cost_rates.items()):
            with rate_cols[idx]:
                st.metric(label=k.replace("_", " ").title(), value=f"${v:.4f}")
