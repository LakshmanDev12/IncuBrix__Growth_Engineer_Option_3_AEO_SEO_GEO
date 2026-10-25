"""SEO & AEO Analytics for IncuBrix Visibility Intelligence."""

from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

try:
    from ui_components import (
        get_api_data,
        get_provenance_badge_markdown,
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
        get_provenance_badge_markdown,
        render_page_header,
        render_kpi_card,
        render_empty_state,
        render_sidebar_global,
        get_plotly_layout,
        apply_saas_theme,
    )

apply_saas_theme()
filters = render_sidebar_global()

render_page_header(
    title="SEO & AEO Analytics",
    subtitle="Deep search ranking positions, Google SERP answer boxes, featured snippets, and evidence provenance.",
    breadcrumb="Intelligence / SEO & AEO",
    badge_text="Search Intelligence",
)

# Filters Row
col_f1, col_f2, col_f3 = st.columns([0.45, 0.3, 0.25], vertical_alignment="bottom")
with col_f1:
    search_term = st.text_input("Filter by Question Keyword", key="seo_kw_search", placeholder="e.g. video, download, sell...")
with col_f2:
    rank_filter = st.selectbox("Rank Position Tier", ["All", "Top 3 (#1-#3)", "Top 10 (#1-#10)", "Ranked (Any)", "Unranked"], key="seo_rank_tier")
with col_f3:
    feature_filter = st.selectbox("Answer Box Presence", ["All", "Answer Box Present", "Standard SERP Only"], key="seo_ab_filter")

# Fetch scoring report and observations
params: Dict[str, Any] = {"limit": 100}
if filters["market"]:
    params["market"] = filters["market"]
if filters["provider"]:
    params["provider"] = filters["provider"]

report_data = get_api_data("/scoring/report", params=params)
obs_list = get_api_data("/observations", params=params) or []
questions = get_api_data("/questions", params={"limit": 100}) or []
q_map = {q["id"]: q.get("text", "") for q in questions}

# Filter for SEO & AEO relevant records (ranking evaluation)
seo_obs = [o for o in obs_list if o.get("provider") in ("google_search", "google_ai_overview", "bing_copilot") or o.get("rank_position") is not None]

# Apply client filters
if search_term.strip():
    seo_obs = [o for o in seo_obs if search_term.lower() in q_map.get(o.get("question_id"), "").lower() or search_term.lower() in (o.get("raw_answer") or "").lower()]

if rank_filter == "Top 3 (#1-#3)":
    seo_obs = [o for o in seo_obs if o.get("rank_position") is not None and 1 <= o.get("rank_position") <= 3]
elif rank_filter == "Top 10 (#1-#10)":
    seo_obs = [o for o in seo_obs if o.get("rank_position") is not None and 1 <= o.get("rank_position") <= 10]
elif rank_filter == "Ranked (Any)":
    seo_obs = [o for o in seo_obs if o.get("rank_position") is not None]
elif rank_filter == "Unranked":
    seo_obs = [o for o in seo_obs if o.get("rank_position") is None]

if feature_filter == "Answer Box Present":
    seo_obs = [o for o in seo_obs if o.get("answer_box_present") is True]
elif feature_filter == "Standard SERP Only":
    seo_obs = [o for o in seo_obs if not o.get("answer_box_present")]

st.space("small")

# KPI Summary
seo_metrics = report_data.get("seo_metrics", {}) if report_data else {}
answer_feats = report_data.get("answer_features", {}) if report_data else {}

col1, col2, col3, col4 = st.columns(4)
with col1:
    top10 = seo_metrics.get("top_10_ranking_rate_pct", 0.0)
    render_kpi_card(
        label="Top-10 Rank Rate",
        value=f"{top10:.1f}%",
        delta=f"{seo_metrics.get('top_10_count', 0)} queries",
        icon=":material/search:",
        help_text="Proportion of evaluated queries ranking in Google top 10 positions.",
        explanation="Validated organic positions.",
    )
with col2:
    top3 = seo_metrics.get("top_3_ranking_rate_pct", 0.0)
    render_kpi_card(
        label="Top-3 Rank Rate",
        value=f"{top3:.1f}%",
        delta=f"{seo_metrics.get('top_3_count', 0)} queries",
        icon=":material/emoji_events:",
        help_text="Proportion of evaluated queries ranking in top 3 podium spots.",
        explanation="Podium organic presence.",
    )
with col3:
    avg_pos = seo_metrics.get("average_rank_position")
    render_kpi_card(
        label="Average Organic Rank",
        value=f"#{avg_pos:.1f}" if avg_pos else "N/A",
        icon=":material/format_list_numbered:",
        help_text="Mean organic position among ranked results.",
        explanation="Calculated over ranked set.",
    )
with col4:
    ab_rate = answer_feats.get("feature_presence_rate_pct", seo_metrics.get("answer_box_rate_pct", 0.0))
    render_kpi_card(
        label="Answer Feature Rate",
        value=f"{ab_rate:.1f}%",
        delta=f"{answer_feats.get('feature_present_count', seo_metrics.get('answer_box_present_count', 0))} boxes",
        icon=":material/featured_play_list:",
        help_text="Presence of featured snippet or SERP direct answer box.",
        explanation="Zero-click answer inclusion.",
    )

st.space("medium")

# Plotly Visualizations: Rank Distribution & Feature Breakdown
col_plot1, col_plot2 = st.columns([0.6, 0.4])

with col_plot1:
    with st.container(border=True):
        st.markdown("#### :material/bar_chart: Organic Ranking Tier Distribution")
        st.caption("Distribution of evaluated queries across position brackets.")
        
        tiers = ["Top 3 (#1-#3)", "Top 4-10", "Page 2 (#11-#20)", "Unranked"]
        top3_cnt = sum(1 for o in seo_obs if o.get("rank_position") and 1 <= o.get("rank_position") <= 3)
        top10_cnt = sum(1 for o in seo_obs if o.get("rank_position") and 4 <= o.get("rank_position") <= 10)
        p2_cnt = sum(1 for o in seo_obs if o.get("rank_position") and 11 <= o.get("rank_position") <= 20)
        unranked_cnt = sum(1 for o in seo_obs if o.get("rank_position") is None)
        
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Bar(
            x=tiers,
            y=[top3_cnt, top10_cnt, p2_cnt, unranked_cnt],
            marker=dict(color=["#8b5cf6", "#10b981", "#f59e0b", "#6b7280"]),
            text=[top3_cnt, top10_cnt, p2_cnt, unranked_cnt],
            textposition="auto",
        ))
        fig_dist.update_layout(get_plotly_layout(height=240, showlegend=False))
        st.plotly_chart(fig_dist, width="stretch")

with col_plot2:
    with st.container(border=True):
        st.markdown("#### :material/pie_chart: Answer Feature Coverage")
        st.caption("SERP real estate capturing direct snippets vs standard results.")
        
        has_feat = sum(1 for o in seo_obs if o.get("answer_box_present"))
        standard_only = len(seo_obs) - has_feat
        
        fig_feat = go.Figure(data=[go.Pie(
            labels=["Answer Box / Snippet", "Standard Blue Links"],
            values=[has_feat, standard_only if standard_only > 0 else 1],
            hole=0.55,
            marker=dict(colors=["#8b5cf6", "#1f2937"]),
        )])
        fig_feat.update_layout(get_plotly_layout(height=240))
        st.plotly_chart(fig_feat, width="stretch")

st.space("medium")

# Search Observation Table
st.markdown("### Search Ranking & Answer Feature Evidence")
st.caption("Inspecting rankings, snippet captures, and source provenance for tracked queries.")

if not seo_obs:
    render_empty_state(
        title="No Matching Search Records",
        description="No search engine observation records match the specified keyword and position filters.",
        icon=":material/search_off:",
    )
else:
    table_rows = []
    for o in seo_obs:
        prov = get_provenance_badge_markdown(o)
        rank_val = o.get("rank_position")
        rank_disp = f"#{rank_val}" if rank_val is not None else "Unranked"
        q_text = q_map.get(o.get("question_id"), "Query #" + (o.get("question_id") or "")[:8])
        
        table_rows.append({
            "Provenance": prov,
            "Target Query": q_text[:65] + ("..." if len(q_text) > 65 else ""),
            "Provider": o.get("provider", "").upper(),
            "Market": o.get("market"),
            "Rank": rank_disp,
            "Answer Box": "Yes" if o.get("answer_box_present") else "No",
            "Score": f"{o.get('visibility_score', 0):.1f}" if o.get("visibility_score") is not None else "N/A",
            "Measured At": (o.get("measured_at") or "")[:19],
        })

    df_seo = pd.DataFrame(table_rows)
    st.dataframe(df_seo, width="stretch", hide_index=True)

    st.space("medium")

    # Detailed Snippet & Source URL Expanders
    st.markdown("### Evidence & Source URL Inspection")
    for idx, o in enumerate(seo_obs[:12]):
        prov_badge = get_provenance_badge_markdown(o)
        rank_val = o.get("rank_position")
        rank_str = f"Rank: #{rank_val}" if rank_val is not None else "Unranked"
        q_text = q_map.get(o.get("question_id"), "Query #" + (o.get("question_id") or "")[:8])
        
        with st.expander(f"{prov_badge} {o.get('provider').upper()} | {q_text[:50]}... | {rank_str}"):
            col_l, col_r = st.columns([0.65, 0.35])
            with col_l:
                st.write(f"**Full Question**: {q_text}")
                st.write(f"**Answer Box Present**: `{o.get('answer_box_present')}`")
                if o.get("quoted_domains"):
                    st.write(f"**Quoted SERP Domains**: {', '.join(o['quoted_domains'])}")
                if o.get("competitors_observed"):
                    st.write(f"**Competitors in SERP**: {', '.join(o['competitors_observed'])}")
            with col_r:
                st.write(f"**Visibility Score**: `{o.get('visibility_score', 'N/A')}`")
                st.write(f"**Measured Timestamp**: `{o.get('measured_at')}`")
            
            st.text_area(
                "Captured Search Result / Snippet Evidence",
                value=o.get("raw_answer") or "(No raw snippet text captured)",
                height=90,
                disabled=True,
                key=f"seo_raw_{o.get('id', idx)}",
            )
