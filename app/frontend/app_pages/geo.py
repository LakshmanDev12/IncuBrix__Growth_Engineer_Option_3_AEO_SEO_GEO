"""GEO (Generative Engine Optimization) Intelligence for IncuBrix."""

from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

try:
    from ui_components import (
        get_api_data,
        post_api_data,
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
        post_api_data,
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
    title="GEO Intelligence",
    subtitle="Generative Engine Optimization tracking brand mentions, citations, and competitor presence across ChatGPT, Claude, Perplexity & Gemini.",
    breadcrumb="Intelligence / GEO Intelligence",
    badge_text="Generative AI",
)

# Fetch Assistant Capabilities & Status
assistants_info = get_api_data("/geo/assistants") or []
obs_params: Dict[str, Any] = {"limit": 100}
if filters["market"]:
    obs_params["market"] = filters["market"]
if filters["provider"]:
    obs_params["provider"] = filters["provider"]

report_data = get_api_data("/scoring/report", params=obs_params)
obs_list = get_api_data("/observations", params=obs_params) or []
questions_list = get_api_data("/questions", params={"limit": 50}) or []

# Filter for GEO-specific records (ChatGPT, Claude, Perplexity, Gemini, AI Overviews)
geo_providers = ("chatgpt", "claude", "perplexity", "gemini", "google_ai_overview", "bing_copilot")
geo_obs = [o for o in obs_list if o.get("provider") in geo_providers or o.get("incubrix_mentioned") is not None]

geo_metrics = report_data.get("geo_metrics", {}) if report_data else {}

# Top KPI row
col1, col2, col3, col4 = st.columns(4)
with col1:
    m_rate = geo_metrics.get("ai_mention_rate_pct", 0.0)
    render_kpi_card(
        label="AI Mention Rate",
        value=f"{m_rate:.1f}%",
        delta=f"{geo_metrics.get('mentioned_count', 0)} of {geo_metrics.get('evaluated_mentions', 0)}",
        icon=":material/psychology:",
        help_text="Confirmed brand presence in generative AI answers.",
        explanation="Affirmative recommendations in AI answers.",
    )
with col2:
    c_rate = geo_metrics.get("ai_citation_rate_pct", 0.0)
    render_kpi_card(
        label="AI Direct Citation Rate",
        value=f"{c_rate:.1f}%",
        delta=f"{geo_metrics.get('cited_count', 0)} direct links",
        icon=":material/link:",
        help_text="Direct clickable links pointing to Vk Analysis domains.",
        explanation="Hyperlinked citation sources in answers.",
    )
with col3:
    render_kpi_card(
        label="Evaluated Answers",
        value=len(geo_obs),
        icon=":material/fact_check:",
        help_text="Total number of AI assistant answers inspected.",
        explanation="Multi-assistant observations.",
    )
with col4:
    comp_count = len(geo_metrics.get("observed_competitors", []))
    render_kpi_card(
        label="Competitors Surfaced",
        value=comp_count,
        icon=":material/domain:",
        help_text="Distinct competing tools surfaced in answer bodies.",
        explanation="Alternative solutions suggested by AI.",
    )

st.space("medium")

# Plotly Visualizations: Mention vs Citation by Assistant
col_p1, col_p2 = st.columns([0.65, 0.35])

with col_p1:
    with st.container(border=True):
        st.markdown("#### :material/compare: Assistant Performance Breakdown")
        st.caption("Side-by-side brand mention and citation rates across active assistants.")
        
        ast_names = ["ChatGPT", "Perplexity", "Claude", "Gemini", "Bing Copilot"]
        m_vals = [
            100.0 if any(o.get("provider") == "chatgpt" and o.get("incubrix_mentioned") for o in geo_obs) else 0.0,
            100.0 if any(o.get("provider") == "perplexity" and o.get("incubrix_mentioned") for o in geo_obs) else 0.0,
            0.0, 0.0, 0.0
        ]
        c_vals = [
            100.0 if any(o.get("provider") == "chatgpt" and o.get("incubrix_cited") for o in geo_obs) else 0.0,
            100.0 if any(o.get("provider") == "perplexity" and o.get("incubrix_cited") for o in geo_obs) else 0.0,
            0.0, 0.0, 0.0
        ]
        
        fig_geo = go.Figure()
        fig_geo.add_trace(go.Bar(
            name="Brand Mention Rate (%)",
            x=ast_names,
            y=m_vals,
            marker_color="#8b5cf6",
        ))
        fig_geo.add_trace(go.Bar(
            name="Direct Citation Rate (%)",
            x=ast_names,
            y=c_vals,
            marker_color="#10b981",
        ))
        fig_geo.update_layout(get_plotly_layout(height=250, barmode="group"))
        st.plotly_chart(fig_geo, width="stretch")

with col_p2:
    with st.container(border=True):
        st.markdown("#### :material/pie_chart: Competitor Mention Share")
        st.caption("Distribution of competing tool recommendations.")
        
        comps = geo_metrics.get("observed_competitors", [])
        if comps:
            fig_comps = go.Figure(data=[go.Pie(
                labels=comps,
                values=[1] * len(comps),
                hole=0.55,
                marker=dict(colors=["#8b5cf6", "#ec4899", "#f59e0b", "#3b82f6"]),
            )])
            fig_comps.update_layout(get_plotly_layout(height=250))
            st.plotly_chart(fig_comps, width="stretch")
        else:
            st.info("No competitor mentions captured yet.")

st.space("medium")

# Multi-Assistant Readiness Matrix
st.markdown("### AI Assistant Engine Capabilities & Readiness")
st.caption("Active connectivity, live web search capabilities, and model configurations.")

if assistants_info:
    ast_rows = []
    for ast in assistants_info:
        is_cfg = ast.get("is_configured", False)
        status_badge = ":green-badge[READY]" if is_cfg else ":gray-badge[NOT CONFIGURED]"
        ast_rows.append({
            "Assistant": ast.get("provider_type", "").upper(),
            "Model Name": ast.get("model_name", "N/A"),
            "Live Web Access": "Yes" if ast.get("supports_live_search") else "No",
            "Streaming": "Yes" if ast.get("supports_streaming") else "No",
            "Status": status_badge,
        })
    st.dataframe(pd.DataFrame(ast_rows), width="stretch", hide_index=True)
else:
    st.caption("Unable to load assistant capabilities from API backend.")

st.space("medium")

# Interactive Harvest & Manual Import Drawer
with st.expander("Trigger Live AI Assistant Harvest / Manual Evidence Entry", icon=":material/tune:"):
    tab_harvest, tab_manual = st.tabs(["Automated Assistant Query", "Manual GEO Evidence Import"])
    
    with tab_harvest:
        st.caption("Execute a live query through a configured assistant adapter.")
        if questions_list:
            q_map = {f"{q['text'][:80]}... (ID: {q['id'][:8]})": q["id"] for q in questions_list}
            selected_q_label = st.selectbox("Select Question to Query", list(q_map.keys()), key="geo_harvest_q_select")
            target_q_id = q_map[selected_q_label]
            
            h_col1, h_col2 = st.columns(2)
            with h_col1:
                target_ast = st.selectbox("AI Assistant", ["perplexity", "chatgpt", "gemini", "claude", "google_ai_overview"], key="geo_target_ast")
            with h_col2:
                target_mkt = st.selectbox("Market Override", ["US", "UK", "CA", "AU"], index=0, key="geo_harvest_mkt")
            
            if st.button("Execute Harvest Query", key="btn_trigger_geo_harvest", type="primary"):
                with st.spinner(f"Querying {target_ast}..."):
                    h_res = post_api_data(f"/geo/harvest/{target_q_id}?assistant={target_ast}&market={target_mkt}")
                    if h_res:
                        st.toast(f"Harvest completed: status={h_res.get('collection_status')}", icon=":material/check_circle:")
                        st.rerun()
                    else:
                        st.error("Harvest query failed or timed out.")
        else:
            st.info("No questions available to query. Ingest questions in Question Explorer first.")

    with tab_manual:
        st.caption("Import verified human operator observations with strict provenance logging.")
        if questions_list:
            m_q_map = {f"{q['text'][:80]}...": q["id"] for q in questions_list}
            m_q_label = st.selectbox("Question", list(m_q_map.keys()), key="geo_manual_q_select")
            m_q_id = m_q_map[m_q_label]
            
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                m_ast = st.selectbox("Observed Assistant", ["chatgpt", "claude", "perplexity", "gemini", "google_ai_overview"], key="m_geo_ast")
                m_market = st.selectbox("Market", ["US", "UK", "CA", "AU"], index=0, key="m_geo_mkt")
                m_mentioned = st.checkbox("Vk Analysis Mentioned", value=True, key="m_geo_mentioned")
                m_cited = st.checkbox("Vk Analysis Cited with Hyperlink", value=False, key="m_geo_cited")
            with m_col2:
                m_op_id = st.text_input("Operator Identifier", value="operator_qa", key="m_geo_op_id")
                m_raw = st.text_area("Assistant Answer Text", height=100, key="m_geo_raw_ans")
            
            if st.button("Save Manual Evidence", key="btn_save_manual_geo"):
                m_payload = {
                    "question_id": m_q_id,
                    "assistant": m_ast,
                    "market": m_market,
                    "mentioned": m_mentioned,
                    "cited": m_cited,
                    "raw_response": m_raw or "Manual observation record.",
                    "operator_id": m_op_id,
                }
                m_res = post_api_data("/geo/manual-import", m_payload)
                if m_res:
                    st.success("Manual observation saved with provenance: [MANUAL]!")
                    st.rerun()
                else:
                    st.error("Failed to save manual evidence.")

st.space("medium")

# Generative AI Response Evidence Inspector
st.markdown("### Generative AI Response Inspector")
if not geo_obs:
    render_empty_state(
        title="No Generative AI Observations Recorded",
        description="Run an automated harvest or manual import above to inspect generative AI answers.",
        icon=":material/psychology_alt:",
    )
else:
    for idx, obs in enumerate(geo_obs[:15]):
        prov_badge = get_provenance_badge_markdown(obs)
        m_status = ":green-badge[MENTIONED]" if obs.get("incubrix_mentioned") else ":gray-badge[NOT MENTIONED]"
        c_status = ":blue-badge[CITED]" if obs.get("incubrix_cited") else ":gray-badge[NOT CITED]"
        
        with st.expander(f"{prov_badge} {obs.get('provider', '').upper()} | {m_status} {c_status} | Market: {obs.get('market')}"):
            col_l, col_r = st.columns([0.65, 0.35])
            with col_l:
                st.write(f"**Question ID**: `{obs.get('question_id')}`")
                if obs.get("quoted_domains"):
                    st.write(f"**Quoted Source Domains**: {', '.join(obs['quoted_domains'])}")
                if obs.get("competitors_observed"):
                    st.write(f"**Competitors Surfaced**: {', '.join(obs['competitors_observed'])}")
            with col_r:
                st.write(f"**Measured Timestamp**: `{obs.get('measured_at')}`")
                st.write(f"**Visibility Score**: `{obs.get('visibility_score', 'N/A')}`")
            
            st.text_area(
                "Assistant Answer Body",
                value=obs.get("raw_answer") or "(No answer body stored)",
                height=110,
                disabled=True,
                key=f"geo_raw_{obs.get('id', idx)}",
            )
