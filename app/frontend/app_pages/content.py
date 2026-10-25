"""Content Studio for IncuBrix Publish-Ready AEO Pages."""

from __future__ import annotations

import json
from typing import Any, Dict, List
import streamlit as st

try:
    from ui_components import (
        get_api_data,
        post_api_data,
        patch_api_data,
        render_page_header,
        render_kpi_card,
        render_empty_state,
        render_sidebar_global,
    )
except ImportError:
    from app.frontend.ui_components import (
        get_api_data,
        post_api_data,
        patch_api_data,
        render_page_header,
        render_kpi_card,
        render_empty_state,
        render_sidebar_global,
    )

filters = render_sidebar_global()

render_page_header(
    title="Content Studio",
    subtitle="Generate, review, and curate publish-ready AEO page drafts with opening direct answers, internal links, and Schema.org markup.",
    breadcrumb="Content & Audits / Content Studio",
    badge_text="AEO Generation",
)

# Batch Action Toolbar
col_act1, col_act2 = st.columns([0.7, 0.3], vertical_alignment="bottom")
with col_act1:
    st.caption("Generate publish-ready content from approved questions, verified product facts, and sourced research.")
with col_act2:
    if st.button("Batch Generate 10 Page Drafts", key="btn_batch_gen_pages", type="primary"):
        with st.spinner("Generating 10 publish-ready AEO pages..."):
            res = post_api_data("/content/generate-batch", {"use_llm": False, "limit": 10})
            if res:
                st.toast(f"Generated {res.get('total_generated')} page drafts!", icon=":material/check_circle:")
                st.rerun()
            else:
                st.error("Failed to generate page drafts.")

st.space("small")

# Status Filter Pills
status_filter = st.segmented_control(
    "Publication Status Filter",
    options=["All", "unreviewed", "approved", "published"],
    default="All",
    key="content_status_pills",
    label_visibility="collapsed",
)

c_params: Dict[str, Any] = {"limit": 50}
if status_filter != "All":
    c_params["status"] = status_filter

pages = get_api_data("/content/pages", params=c_params) or []

if not pages:
    render_empty_state(
        title="No Content Drafts Available",
        description="Click 'Batch Generate 10 Page Drafts' above to generate publish-ready AEO content targeting high-value creator questions.",
        icon=":material/article:",
        action_label="Generate 10 Page Drafts",
        action_key="empty_gen_pages_btn",
    )
else:
    # Summary Metrics
    unreviewed_count = sum(1 for p in pages if p.get("publication_status") == "unreviewed")
    approved_count = sum(1 for p in pages if p.get("publication_status") in ("approved", "published"))
    avg_words = sum(p.get("word_count", 0) for p in pages) // len(pages) if pages else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        render_kpi_card(label="Total Pages Available", value=len(pages))
    with col2:
        render_kpi_card(label="Awaiting Human Review", value=unreviewed_count, delta="Unreviewed" if unreviewed_count > 0 else "All Clean")
    with col3:
        render_kpi_card(label="Approved / Published", value=approved_count, delta=f"Avg Words: {avg_words}")

    st.space("medium")
    st.markdown(f"### Page Drafts ({len(pages)})")

    for p in pages:
        p_id = p.get("id")
        p_status = p.get("publication_status", "unreviewed").lower()
        if p_status in ("approved", "published"):
            status_badge = ":green-badge[APPROVED]"
        else:
            status_badge = ":orange-badge[UNREVIEWED]"

        title = p.get("title") or "Untitled Draft"
        slug = p.get("slug") or "draft"

        with st.expander(f"{status_badge} {title} (/{slug})"):
            # Opening Direct Answer Highlight
            first_paragraphs = [
                par.strip()
                for par in p.get("markdown_content", "").split("\n\n")
                if par.strip() and not par.strip().startswith("#")
            ]
            if first_paragraphs:
                with st.container(border=True):
                    st.caption("Opening Direct Answer (First 2 Sentences)")
                    st.markdown(f"**{first_paragraphs[0]}**")

            col_m1, col_m2 = st.columns([0.65, 0.35])
            with col_m1:
                st.write(f"**Target Question**: {p.get('target_question') or 'Creator Query'}")
                st.write(f"**Meta Description**: {p.get('meta_description')}")
            with col_m2:
                st.write(f"**Word Count**: {p.get('word_count', 0)} words")
                st.write(f"**Status**: `{p_status.upper()}`")

            # Structured Data & Links Tabs
            tab_preview, tab_links, tab_citations, tab_schema = st.tabs([
                "Content Body",
                "Internal Links",
                "Sourced Citations",
                "Schema.org JSON-LD",
            ])

            with tab_preview:
                st.markdown(p.get("markdown_content", ""))

            with tab_links:
                in_links = p.get("internal_links") or []
                if in_links:
                    st.caption("Recommended internal link destinations to establish topic authority:")
                    for il in in_links:
                        st.markdown(f"- **{il.get('anchor')}** → `{il.get('url')}`")
                else:
                    st.caption("No internal links specified.")

            with tab_citations:
                cites = p.get("citations") or []
                if cites:
                    st.caption("Verified real third-party research & publisher citations:")
                    for c in cites:
                        st.markdown(f"- **{c.get('publisher')}**: [{c.get('title')}]({c.get('url')})")
                else:
                    st.caption("No citations linked.")

            with tab_schema:
                schema_obj = p.get("structured_data")
                if schema_obj:
                    st.code(json.dumps(schema_obj, indent=2), language="json")
                else:
                    st.caption("No JSON-LD structured data generated.")

            st.space("small")

            # Curation & Validation Actions
            act_col1, act_col2 = st.columns(2)
            with act_col1:
                if p_status == "unreviewed":
                    if st.button(f"Approve Draft #{p_id[:8]}", key=f"btn_app_{p_id}", type="primary"):
                        patch_res = patch_api_data(
                            f"/content/pages/{p_id}/review",
                            {"publication_status": "approved", "reviewer_notes": "Approved via Content Studio."},
                        )
                        if patch_res:
                            st.toast("Draft approved for publishing!", icon=":material/check_circle:")
                            st.rerun()
                        else:
                            st.error("Failed to approve draft.")
            with act_col2:
                if st.button(f"Validate Compliance #{p_id[:8]}", key=f"btn_val_{p_id}"):
                    with st.spinner("Validating direct answer and schema compliance..."):
                        val_res = post_api_data(f"/content/validate/{p_id}")
                        if val_res and val_res.get("is_valid"):
                            st.toast("Page passed all AEO validation checks!", icon=":material/verified:")
                        elif val_res:
                            st.warning(f"Issues: {val_res.get('issues')}")
                        else:
                            st.error("Validation failed.")
