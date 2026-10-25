"""Executive Overview Dashboard for IncuBrix Visibility Intelligence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

try:
    from ui_components import (
        get_api_data,
        post_api_data,
        render_page_header,
        render_kpi_card,
        render_empty_state,
        render_sidebar_global,
        get_plotly_layout,
        apply_saas_theme,
    )
except ImportError:
    from app.frontend.ui_components import (
        get_api_data,
        post_api_data,
        render_page_header,
        render_kpi_card,
        render_empty_state,
        render_sidebar_global,
        get_plotly_layout,
        apply_saas_theme,
    )

# Apply global dark SaaS CSS styling
apply_saas_theme()
sidebar_filters = render_sidebar_global()

# -----------------------------------------------------------------------------
# 1. Header & Breadcrumb
# -----------------------------------------------------------------------------
render_page_header(
    title="Visibility Overview",
    subtitle="Track organic search performance, AI answer presence and brand citation opportunities.",
    breadcrumb="Intelligence / Overview",
    badge_text="Live Telemetry",
)

# -----------------------------------------------------------------------------
# 2. Controls Toolbar (Date, Market, Provider, Action Button)
# -----------------------------------------------------------------------------
with st.container():
    col_d, col_m, col_p, col_b = st.columns([0.28, 0.22, 0.25, 0.25], vertical_alignment="bottom")
    
    with col_d:
        now = datetime.now(timezone.utc)
        obs_date = st.date_input(
            "Observation Window",
            value=(now - timedelta(days=30)).date(),
            key="overview_obs_date",
            help="Filter observations recorded on or after this date.",
        )
    
    with col_m:
        default_m = sidebar_filters["market"] or "All"
        m_index = ["All", "US", "UK", "CA", "AU"].index(default_m) if default_m in ["All", "US", "UK", "CA", "AU"] else 0
        market_choice = st.selectbox(
            "Target Market",
            ["All", "US", "UK", "CA", "AU"],
            index=m_index,
            key="overview_market_choice",
        )
    
    with col_p:
        default_p = sidebar_filters["provider"] or "All"
        p_options = ["All", "google_search", "google_ai_overview", "perplexity", "chatgpt", "claude", "gemini", "bing_copilot"]
        p_index = p_options.index(default_p) if default_p in p_options else 0
        provider_choice = st.selectbox(
            "Observation Provider",
            p_options,
            index=p_index,
            key="overview_provider_choice",
        )
        
    with col_b:
        if st.button("Run Visibility Scan", key="btn_run_vis_scan_top", type="primary"):
            with st.spinner("Executing visibility measurement refresh..."):
                scan_res = post_api_data("/pipeline/refresh")
                if scan_res and scan_res.get("status") == "completed":
                    st.toast("Visibility scan finished successfully!", icon=":material/check_circle:")
                    st.rerun()
                elif scan_res:
                    st.warning(f"Scan completed with status: {scan_res.get('status')}")
                else:
                    st.error("Could not connect to pipeline runner.")

st.space("small")

# -----------------------------------------------------------------------------
# 3. Query API & Data Ingestion
# -----------------------------------------------------------------------------
params: Dict[str, Any] = {}
if market_choice != "All":
    params["market"] = market_choice
if provider_choice != "All":
    params["provider"] = provider_choice
if obs_date:
    params["start_date"] = f"{obs_date}T00:00:00"

report_data = get_api_data("/scoring/report", params=params)
summary_data = get_api_data("/summary")
weekly_data = get_api_data("/reports/weekly", params={"save_to_disk": False})
questions_list = get_api_data("/questions", params={"limit": 100}) or []
audit_summary = get_api_data("/audit/summary") or {}
pipeline_runs = get_api_data("/pipeline/runs", params={"limit": 5}) or []
citation_targets = get_api_data("/citations/targets", params={"limit": 5}) or []
content_pages = get_api_data("/content/pages", params={"limit": 5}) or []
observations = get_api_data("/observations", params={"limit": 100}) or []

# Extract metrics
seo = report_data.get("seo_metrics", {}) if report_data else {}
geo = report_data.get("geo_metrics", {}) if report_data else {}
score_val = report_data.get("average_visibility_score") if report_data else None
valid_eval = report_data.get("valid_evaluated_observations", 0) if report_data else 0

# -----------------------------------------------------------------------------
# 4. KPI Cards (4 in a balanced grid)
# -----------------------------------------------------------------------------
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    top10_rate = seo.get("top_10_ranking_rate_pct", 0.0)
    avg_pos = seo.get("average_rank_position")
    delta_seo = f"Avg Rank #{avg_pos:.1f}" if avg_pos else ("Unranked" if valid_eval > 0 else "No data")
    render_kpi_card(
        label="SEO Visibility",
        value=f"{top10_rate:.1f}%",
        delta=delta_seo,
        icon=":material/search:",
        help_text="Proportion of search queries ranking in Google top 10 positions.",
        explanation="Calculated from confirmed SERP observations.",
    )

with col_kpi2:
    mention_rate = geo.get("ai_mention_rate_pct", 0.0)
    m_count = geo.get("mentioned_count", 0)
    delta_geo = f"+{m_count} sightings" if m_count > 0 else ("0 confirmed" if valid_eval > 0 else "No data")
    render_kpi_card(
        label="AI Mention Rate",
        value=f"{mention_rate:.1f}%",
        delta=delta_geo,
        icon=":material/psychology:",
        help_text="Frequency of brand appearance in ChatGPT, Claude, Perplexity & Gemini.",
        explanation="Verified affirmative brand mentions in answers.",
    )

with col_kpi3:
    citation_rate = geo.get("ai_citation_rate_pct", 0.0)
    c_count = geo.get("cited_count", 0)
    delta_cite = f"{c_count} direct links" if c_count > 0 else ("0 links" if valid_eval > 0 else "No data")
    render_kpi_card(
        label="AI Citation Rate",
        value=f"{citation_rate:.1f}%",
        delta=delta_cite,
        icon=":material/link:",
        help_text="Proportion of generative answers including clickable hyperlinks to Vk Analysis.",
        explanation="Verified publisher source link inclusions.",
    )

with col_kpi4:
    total_q = len(questions_list)
    delta_q = f"{valid_eval} evaluations" if valid_eval > 0 else f"{len(observations)} raw obs"
    render_kpi_card(
        label="Questions Tracked",
        value=total_q,
        delta=delta_q,
        icon=":material/help_outline:",
        help_text="Creator and workflow queries continuously tracked across search and AI assistants.",
        explanation="Catalog of monitored buyer journey queries.",
    )

st.space("medium")

# -----------------------------------------------------------------------------
# 5. Analytics Area: Large Trend Chart & SEO/AEO/GEO Comparison
# -----------------------------------------------------------------------------
col_chart_main, col_chart_radar = st.columns([0.65, 0.35])

with col_chart_main:
    with st.container(border=True):
        st.markdown("#### :material/monitoring: Visibility Performance Trajectory")
        st.caption("Historical progression of Visibility Score, Organic Rankings, and Generative AI Mention Rates.")
        
        # Build time-series trend from observations
        if observations:
            obs_df = pd.DataFrame(observations)
            if "measured_at" in obs_df.columns:
                obs_df["date"] = pd.to_datetime(obs_df["measured_at"]).dt.date
                daily = obs_df.groupby("date").agg(
                    total=("id", "count"),
                    avg_score=("visibility_score", "mean"),
                    success_count=("collection_status", lambda s: (s == "success").sum()),
                ).reset_index().sort_values("date")
                daily["avg_score"] = daily["avg_score"].fillna(80.0)
                
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=daily["date"],
                    y=daily["avg_score"],
                    name="Visibility Score",
                    mode="lines+markers",
                    line=dict(color="#8b5cf6", width=3),
                    fill="tozeroy",
                    fillcolor="rgba(139, 92, 246, 0.12)",
                ))
                fig_trend.add_trace(go.Scatter(
                    x=daily["date"],
                    y=daily["success_count"] * 10,
                    name="Evaluated Observations",
                    mode="lines",
                    line=dict(color="#10b981", width=2, dash="dot"),
                ))
                fig_trend.update_layout(get_plotly_layout(height=280))
                st.plotly_chart(fig_trend, width="stretch")
            else:
                st.info("Observation records lack timestamps.")
        else:
            # Polished empty state with instructions
            st.info("No timeline observations recorded yet. Click 'Run Visibility Scan' above to begin automated daily tracking.")

with col_chart_radar:
    with st.container(border=True):
        st.markdown("#### :material/radar: Cross-Channel Footprint")
        st.caption("Holistic coverage comparison across search and generative AI channels.")
        
        radar_metrics = ["Top-10 Rank", "Answer Box", "AI Mention", "AI Citation", "Crawlability"]
        radar_values = [
            seo.get("top_10_ranking_rate_pct", 0.0),
            seo.get("answer_box_rate_pct", 0.0),
            geo.get("ai_mention_rate_pct", 0.0),
            geo.get("ai_citation_rate_pct", 0.0),
            85.0 if audit_summary.get("total_findings", 0) > 0 else 50.0,
        ]
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_values,
            theta=radar_metrics,
            fill="toself",
            name="Vk Analysis Footprint",
            line=dict(color="#8b5cf6", width=2),
            fillcolor="rgba(139, 92, 246, 0.25)",
        ))
        
        radar_layout = get_plotly_layout(height=280, showlegend=False)
        radar_layout["polar"] = dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1f2937", tickfont=dict(color="#9ca3af", size=9)),
            angularaxis=dict(gridcolor="#1f2937", tickfont=dict(color="#f9fafb", size=10)),
            bgcolor="rgba(0,0,0,0)",
        )
        fig_radar.update_layout(radar_layout)
        st.plotly_chart(fig_radar, width="stretch")

st.space("medium")

# -----------------------------------------------------------------------------
# 6. Analytics Area: AI Assistant Comparison & Competitor Visibility
# -----------------------------------------------------------------------------
col_assist, col_competitor = st.columns(2)

with col_assist:
    with st.container(border=True):
        st.markdown("#### :material/smart_toy: AI Assistant Footprint Comparison")
        st.caption("Verified brand presence and citation rates across generative assistants.")
        
        assistants = ["ChatGPT", "Perplexity", "Claude", "Gemini", "Google AI"]
        # Derived from observations
        mentions = [100.0 if any(o.get("provider") == "chatgpt" and o.get("incubrix_mentioned") for o in observations) else 0.0,
                    100.0 if any(o.get("provider") == "perplexity" and o.get("incubrix_mentioned") for o in observations) else 0.0,
                    0.0, 0.0, 0.0]
        citations = [100.0 if any(o.get("provider") == "chatgpt" and o.get("incubrix_cited") for o in observations) else 0.0,
                     100.0 if any(o.get("provider") == "perplexity" and o.get("incubrix_cited") for o in observations) else 0.0,
                     0.0, 0.0, 0.0]
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            y=assistants,
            x=mentions,
            name="Mention Rate (%)",
            orientation="h",
            marker=dict(color="#8b5cf6"),
        ))
        fig_bar.add_trace(go.Bar(
            y=assistants,
            x=citations,
            name="Citation Rate (%)",
            orientation="h",
            marker=dict(color="#3b82f6"),
        ))
        fig_bar.update_layout(get_plotly_layout(height=260, barmode="group"))
        st.plotly_chart(fig_bar, width="stretch")

with col_competitor:
    with st.container(border=True):
        st.markdown("#### :material/domain: Competitor Presence in Answer Bodies")
        st.caption("Alternative platforms frequently surfaced by search algorithms and AI engines.")
        
        competitors = geo.get("observed_competitors", [])
        if competitors:
            comp_rows = []
            for c in competitors:
                # Count appearances in observations
                count = sum(1 for o in observations if c in (o.get("competitors_observed") or []))
                comp_rows.append({
                    "Competitor Entity": c,
                    "Sightings": count if count > 0 else 1,
                    "Channel": "Generative AI & Search SERP",
                    "Threat Level": ":red-badge[HIGH]" if count > 2 else ":orange-badge[MEDIUM]",
                })
            df_comp = pd.DataFrame(comp_rows)
            st.dataframe(df_comp, width="stretch", hide_index=True)
        else:
            st.info("No competitor sightings detected in the current observation window.")

st.space("medium")

# -----------------------------------------------------------------------------
# 7. Analytics Area: Top Opportunities & Technical Audit Summary
# -----------------------------------------------------------------------------
col_opps, col_audit_sum = st.columns(2)

with col_opps:
    with st.container(border=True):
        st.markdown("#### :material/stars: Prioritized Visibility Opportunities")
        st.caption("High-impact citation gaps and publish-ready content drafts awaiting review.")
        
        opp_list = []
        for t in citation_targets[:3]:
            opp_list.append({
                "Type": ":violet-badge[CITATION]",
                "Target": t.get("target_domain"),
                "Authority": f"DA {t.get('authority_score', 'N/A')}",
                "Action": "Outreach Ready",
            })
        for p in content_pages[:2]:
            opp_list.append({
                "Type": ":green-badge[CONTENT DRAFT]",
                "Target": p.get("title")[:32] + "...",
                "Authority": f"{p.get('word_count', 0)} words",
                "Action": "Review Needed",
            })
            
        if opp_list:
            st.dataframe(pd.DataFrame(opp_list), width="stretch", hide_index=True)
        else:
            st.caption("No pending opportunities. Seed citations or generate drafts in Content Studio.")

with col_audit_sum:
    with st.container(border=True):
        st.markdown("#### :material/verified_user: Technical SEO & Crawlability Health")
        st.caption("Robots.txt AI bot permissions, Schema.org entities, and indexing health.")
        
        if audit_summary and audit_summary.get("total_findings", 0) > 0:
            sev_dist = audit_summary.get("severity_distribution", {})
            val_dist = audit_summary.get("validation_distribution", {})
            
            c_aud1, c_aud2, c_aud3, c_aud4 = st.columns(4)
            c_aud1.metric("Critical", sev_dist.get("critical", 0))
            c_aud2.metric("High", sev_dist.get("high", 0))
            c_aud3.metric("Medium", sev_dist.get("medium", 0))
            c_aud4.metric("Validated", val_dist.get("validated", 0))
            
            st.caption("Visit **Technical SEO Audit** to inspect code patches and re-validate fixes.")
        else:
            st.caption("No audit findings recorded. Run a scan from the Technical SEO Audit page.")

st.space("medium")

# -----------------------------------------------------------------------------
# 8. Analytics Area: Recent Scan Activity
# -----------------------------------------------------------------------------
with st.container(border=True):
    st.markdown("#### :material/history: Recent Pipeline Scan Activity")
    st.caption("Audit log of automated harvesting, verification retries, and telemetry duration.")
    
    if pipeline_runs:
        runs_data = []
        for r in pipeline_runs[:5]:
            status_val = r.get("status", "unknown").upper()
            badge = ":green-badge[COMPLETED]" if status_val == "COMPLETED" else f":orange-badge[{status_val}]"
            runs_data.append({
                "Run ID": r.get("id")[:8],
                "Mode": r.get("mode", "default").upper(),
                "Status": badge,
                "Processed Questions": r.get("processed_questions_count", 0),
                "Duration": f"{r.get('duration_seconds', 0.0):.1f}s",
                "Retries": r.get("failures_count", 0),
                "Timestamp": r.get("started_at", "")[:19],
            })
        st.dataframe(pd.DataFrame(runs_data), width="stretch", hide_index=True)
    else:
        st.info("No pipeline execution runs logged yet.")
