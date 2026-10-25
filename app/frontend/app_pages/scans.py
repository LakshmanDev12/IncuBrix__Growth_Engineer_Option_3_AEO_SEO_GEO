"""Scan History & Pipeline Orchestration for IncuBrix Visibility Intelligence."""

from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd
import streamlit as st

try:
    from ui_components import (
        get_api_data,
        post_api_data,
        render_page_header,
        render_kpi_card,
        render_empty_state,
        render_sidebar_global,
    )
except ImportError:
    from app.frontend.ui_components import (
        get_api_data,
        post_api_data,
        render_page_header,
        render_kpi_card,
        render_empty_state,
        render_sidebar_global,
    )

filters = render_sidebar_global()

render_page_header(
    title="Scan History & Pipeline Runs",
    subtitle="Orchestrate end-to-end visibility pipelines, inspect job durations, bounded retries, and API cost telemetry.",
    breadcrumb="System / Scan History",
    badge_text="Pipeline Telemetry",
)

# Pipeline Action Triggers
with st.container(border=True):
    col_act1, col_act2, col_act3 = st.columns([0.45, 0.27, 0.28], vertical_alignment="bottom")
    with col_act1:
        st.markdown("**Manual Pipeline Orchestration**")
        st.caption("Trigger comprehensive end-to-end collection or refresh measurements for active queries.")
    with col_act2:
        if st.button("Refresh Measurements", key="btn_run_refresh_scans", type="primary"):
            with st.spinner("Refreshing measurements across providers..."):
                r_res = post_api_data("/pipeline/refresh")
                if r_res and r_res.get("status") == "completed":
                    st.toast("Measurements refreshed!", icon=":material/check_circle:")
                    st.rerun()
                elif r_res:
                    st.warning(f"Refresh completed with status: {r_res.get('status')}")
                else:
                    st.error("Failed to connect to pipeline runner.")
    with col_act3:
        if st.button("Run Full Pipeline", key="btn_run_full_scans"):
            with st.spinner("Executing end-to-end pipeline (ingest, harvest, audit, content, report)..."):
                f_res = post_api_data("/pipeline/run", {"mode": "e2e", "max_retries": 2})
                if f_res and f_res.get("status") == "completed":
                    st.toast("Full pipeline completed!", icon=":material/check_circle:")
                    st.rerun()
                elif f_res:
                    st.warning(f"Run completed with status: {f_res.get('status')}")
                else:
                    st.error("Failed to trigger full pipeline.")

st.space("medium")

# Fetch Runs and Cost Rates
runs = get_api_data("/pipeline/runs", params={"limit": 50}) or []
cost_rates = get_api_data("/pipeline/cost-rates") or {}

if not runs:
    render_empty_state(
        title="No Pipeline Runs Logged",
        description="No automated or manual pipeline runs have been recorded yet. Use the action triggers above to execute your first visibility scan.",
        icon=":material/history_toggle_off:",
        action_label="Run Measurement Refresh",
        action_key="empty_run_scan_btn",
    )
else:
    # Summary Metrics
    total_runs = len(runs)
    successful_runs = sum(1 for r in runs if r.get("status") == "completed")
    avg_duration = sum(r.get("duration_seconds", 0.0) for r in runs) / total_runs if total_runs else 0.0
    total_processed_q = sum(r.get("processed_questions_count", 0) for r in runs)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card(label="Total Executions", value=total_runs)
    with col2:
        render_kpi_card(
            label="Success Rate",
            value=f"{(successful_runs / total_runs * 100):.1f}%",
            delta=f"{successful_runs} completed",
        )
    with col3:
        render_kpi_card(label="Average Runtime", value=f"{avg_duration:.1f}s")
    with col4:
        render_kpi_card(label="Processed Queries", value=total_processed_q)

    st.space("medium")

    # Historical Runs Table & Detailed Cards
    st.markdown(f"### Historical Execution Log ({total_runs} Runs)")

    for r in runs:
        r_id = r.get("id")
        raw_status = r.get("status", "unknown").lower()
        if raw_status == "completed":
            s_badge = ":green-badge[COMPLETED]"
        elif raw_status == "running":
            s_badge = ":blue-badge[RUNNING]"
        elif raw_status == "failed":
            s_badge = ":red-badge[FAILED]"
        else:
            s_badge = ":orange-badge[PARTIAL]"

        dur = f"{r.get('duration_seconds', 0.0):.1f}s"
        q_count = r.get("processed_questions_count", 0)
        mode_disp = r.get("mode", "default").upper()
        
        with st.expander(f"{s_badge} Run #{r_id[:8]} | Mode: {mode_disp} | Duration: {dur} | Queries: {q_count}"):
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.write(f"**Run ID**: `{r_id}`")
                st.write(f"**Started At**: `{r.get('started_at')}`")
                st.write(f"**Completed At**: `{r.get('completed_at') or 'Active'}`")
            with col_d2:
                st.write(f"**Processed Questions**: `{q_count}`")
                st.write(f"**Failed Providers / Errors**: `{r.get('failures_count', 0)}`")
                if r.get("error_message"):
                    st.error(f"Error Detail: {r.get('error_message')}")
            
            # Cost Telemetry
            if cost_rates:
                with st.container(border=True):
                    st.caption("Standard Unit API Cost Benchmarks Applied")
                    st.write(
                        f"Perplexity: `${cost_rates.get('perplexity', 0.005)}/req` | "
                        f"Search: `${cost_rates.get('google_search', 0.002)}/req` | "
                        f"OpenAI: `${cost_rates.get('chatgpt', 0.003)}/req`"
                    )
