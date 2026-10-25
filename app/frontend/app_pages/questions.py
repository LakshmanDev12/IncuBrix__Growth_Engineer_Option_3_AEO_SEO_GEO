"""Question Explorer & Ingestion Hub for IncuBrix Visibility Intelligence."""

from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd
import streamlit as st

try:
    from ui_components import (
        get_api_data,
        get_api_text,
        post_api_data,
        patch_api_data,
        render_page_header,
        render_empty_state,
        render_sidebar_global,
    )
except ImportError:
    from app.frontend.ui_components import (
        get_api_data,
        get_api_text,
        post_api_data,
        patch_api_data,
        render_page_header,
        render_empty_state,
        render_sidebar_global,
    )

filters = render_sidebar_global()

render_page_header(
    title="Question Explorer",
    subtitle="Audit, curate, and ingest creator queries with search intent classification and measurement history.",
    breadcrumb="Intelligence / Question Explorer",
    badge_text="Query Catalog",
)

# Ingestion & Export Toolbar Expander
with st.expander("Question Ingestion & CSV Export", icon=":material/upload_file:"):
    tab_import_text, tab_import_csv, tab_export = st.tabs(["Raw Text Ingestion", "CSV Batch Ingestion", "Export Catalog"])
    
    with tab_import_text:
        st.caption("Paste creator questions (one per line).")
        raw_text = st.text_area("Questions Input", height=120, key="txt_ingest_questions", placeholder="How do I sell digital downloads online?\nWhat is the best platform for creator memberships?")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            t_market = st.selectbox("Market Target", ["US", "UK", "CA", "AU"], key="txt_ingest_market")
        with col_t2:
            t_source = st.text_input("Source Provenance", value="creator_community", key="txt_ingest_source")
        
        if st.button("Ingest Questions", key="btn_ingest_text", type="primary"):
            lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
            if lines:
                payload = {
                    "questions": lines,
                    "market": t_market,
                    "source": t_source,
                }
                res = post_api_data("/questions/import-text", payload)
                if res:
                    st.toast(f"Ingested {res.get('imported_count', len(lines))} questions!", icon=":material/check_circle:")
                    st.rerun()
                else:
                    st.error("Failed to ingest questions.")
            else:
                st.warning("Please enter at least one question line.")

    with tab_import_csv:
        st.caption("Upload standard CSV containing 'question' or 'text' column.")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"], key="csv_uploader_questions")
        if uploaded_file is not None:
            csv_content = uploaded_file.getvalue().decode("utf-8")
            if st.button("Process CSV Ingestion", key="btn_ingest_csv_confirm"):
                with st.spinner("Importing questions..."):
                    res = post_api_data("/questions/import-csv", {"csv_content": csv_content})
                    if res:
                        st.toast(f"Imported {res.get('imported_count')} questions from CSV!", icon=":material/check_circle:")
                        st.rerun()
                    else:
                        st.error("Failed to process CSV file.")

    with tab_export:
        st.caption("Download all persisted creator questions and metadata.")
        export_csv_text = get_api_text("/questions/export.csv")
        if export_csv_text:
            st.download_button(
                "Download questions.csv",
                data=export_csv_text,
                file_name="questions.csv",
                mime="text/csv",
                key="btn_dl_questions_csv",
            )
        else:
            st.info("No questions to export.")

st.space("small")

# Filters Row
col_f1, col_f2, col_f3 = st.columns([0.45, 0.3, 0.25])
with col_f1:
    search_query = st.text_input("Search Question Text", key="q_search_input", placeholder="Filter by keyword...", label_visibility="collapsed")
with col_f2:
    intent_filter = st.selectbox("Intent", ["All", "informational", "transactional", "commercial", "navigational"], key="q_intent_filter")
with col_f3:
    status_filter = st.selectbox("Status", ["All", "approved", "unreviewed", "rejected"], key="q_status_filter")

# Fetch Questions
q_params: Dict[str, Any] = {"limit": 100}
if filters["market"]:
    q_params["market"] = filters["market"]
if intent_filter != "All":
    q_params["intent"] = intent_filter
if status_filter != "All":
    q_params["review_status"] = status_filter

questions = get_api_data("/questions", params=q_params) or []

# Client-side text filter if keyword provided
if search_query.strip():
    questions = [q for q in questions if search_query.lower() in q.get("text", "").lower()]

if not questions:
    render_empty_state(
        title="No Questions Match Current Filters",
        description="Try relaxing your search terms or use the ingestion toolbar above to import new questions.",
        icon=":material/help_outline:",
    )
else:
    st.caption(f"Showing **{len(questions)}** creator questions:")
    
    for q in questions:
        q_id = q.get("id")
        status = q.get("review_status", "unreviewed").lower()
        if status == "approved":
            status_badge = ":green-badge[APPROVED]"
        elif status == "rejected":
            status_badge = ":red-badge[REJECTED]"
        else:
            status_badge = ":orange-badge[UNREVIEWED]"
            
        intent_disp = q.get("intent", "general").upper()
        
        with st.container(border=True):
            col_left, col_right = st.columns([0.75, 0.25])
            
            with col_left:
                st.markdown(f"**{q.get('text')}**")
                st.caption(f"ID: `{q_id[:8]}` | Market: `{q.get('market')}` | Intent: `{intent_disp}` | Source: `{q.get('source_provenance') or 'community'}`")
            
            with col_right:
                st.markdown(f"{status_badge}")
                # Review Curation Actions
                if status == "unreviewed":
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button("Approve", key=f"app_q_{q_id}", type="primary"):
                            patch_api_data(f"/questions/{q_id}/review", {"review_status": "approved"})
                            st.toast("Question approved!", icon=":material/check_circle:")
                            st.rerun()
                    with btn_c2:
                        if st.button("Reject", key=f"rej_q_{q_id}"):
                            patch_api_data(f"/questions/{q_id}/review", {"review_status": "rejected"})
                            st.toast("Question rejected.", icon=":material/cancel:")
                            st.rerun()
                elif status == "approved":
                    if st.button("Harvest Now", key=f"harv_q_{q_id}"):
                        with st.spinner("Harvesting observations..."):
                            post_api_data(f"/observations/harvest/{q_id}")
                            st.toast("Harvest complete!", icon=":material/refresh:")
                            st.rerun()
