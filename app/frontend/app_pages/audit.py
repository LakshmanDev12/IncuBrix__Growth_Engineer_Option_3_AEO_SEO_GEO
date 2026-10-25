"""Technical SEO, AEO & Crawlability Audit Dashboard for IncuBrix."""

from __future__ import annotations

from typing import Any, Dict, List
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
    title="Technical SEO & AEO Audit",
    subtitle="Audit crawler accessibility, robots.txt AI permissions, Schema.org entity clarity, and generate actionable code patches.",
    breadcrumb="Content & Audits / Technical SEO Audit",
    badge_text="Crawlability Engine",
)

# Fetch Audit Summary
audit_summary = get_api_data("/audit/summary")

# Run Live Audit Trigger
with st.expander("Execute New Technical Audit", icon=":material/play_circle:"):
    col_u1, col_u2 = st.columns([0.75, 0.25], vertical_alignment="bottom")
    with col_u1:
        target_audit_url = st.text_input("Target URL to Audit", value="https://incubrix.com", key="txt_audit_target_url")
    with col_u2:
        if st.button("Run Audit", key="btn_run_audit_live", type="primary"):
            with st.spinner("Executing crawlability and schema audit..."):
                res = post_api_data(f"/audit/run?url={target_audit_url}")
                if res:
                    st.toast(f"Audit completed: {len(res)} findings discovered!", icon=":material/check_circle:")
                    st.rerun()
                else:
                    st.error("Audit run failed or target URL unreachable.")

st.space("small")

if not audit_summary or audit_summary.get("total_findings", 0) == 0:
    render_empty_state(
        title="No Technical Audit Findings Logged",
        description="The audit catalog is currently empty. Run an audit against your website or test fixture using the panel above.",
        icon=":material/fact_check:",
    )
else:
    sev_dist = audit_summary.get("severity_distribution", {})
    val_dist = audit_summary.get("validation_distribution", {})
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card(
            label="Total Findings",
            value=audit_summary.get("total_findings", 0),
            help_text="Total architectural, metadata, and crawler access issues identified.",
        )
    with col2:
        crit = sev_dist.get("critical", 0)
        render_kpi_card(
            label="Critical Severity",
            value=crit,
            delta="Urgent Action Required" if crit > 0 else "Clean",
            help_text="Issues actively blocking search indexing or AI crawlers.",
        )
    with col3:
        high = sev_dist.get("high", 0)
        render_kpi_card(
            label="High Priority",
            value=high,
            help_text="High-impact canonical, Schema.org, or llms.txt optimizations.",
        )
    with col4:
        val_count = val_dist.get("validated", 0)
        render_kpi_card(
            label="Validated Fixes",
            value=val_count,
            delta=f"{val_count} verified" if val_count > 0 else "0 verified",
            help_text="Remediations independently verified against validation criteria.",
        )

    st.space("medium")

    # Filters Row
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        severity_filter = st.selectbox(
            "Filter Severity",
            ["All", "critical", "high", "medium", "low"],
            key="audit_sev_filter",
        )
    with col_f2:
        category_filter = st.selectbox(
            "Filter Category",
            ["All", "indexability", "robots_txt", "structured_data", "metadata", "canonical", "llms_txt", "performance"],
            key="audit_cat_filter",
        )

    a_params: Dict[str, Any] = {"limit": 100}
    if severity_filter != "All":
        a_params["severity"] = severity_filter
    if category_filter != "All":
        a_params["category"] = category_filter

    findings = get_api_data("/audit/findings", params=a_params) or []

    st.markdown(f"### Prioritized Technical Findings ({len(findings)})")
    
    for f in findings:
        f_id = f.get("id")
        sev = f.get("severity", "medium").lower()
        if sev == "critical":
            sev_badge = ":red-badge[CRITICAL]"
        elif sev == "high":
            sev_badge = ":orange-badge[HIGH]"
        elif sev == "medium":
            sev_badge = ":blue-badge[MEDIUM]"
        else:
            sev_badge = ":gray-badge[LOW]"

        val_status = f.get("validation_status", "unvalidated").lower()
        val_badge = ":green-badge[VALIDATED]" if val_status == "validated" else ":orange-badge[UNVALIDATED]"
        
        with st.expander(f"{sev_badge} {val_badge} {f.get('issue_code')} | {f.get('audit_category')}"):
            st.write(f"**Target URL**: `{f.get('target_url')}`")
            st.write(f"**Problem Description**: {f.get('description')}")
            
            if f.get("evidence"):
                st.caption(f"**Evidence**: `{f.get('evidence')}`")
                
            if f.get("recommendation"):
                st.info(f"**Recommended Remediation**: {f.get('recommendation')}")
                
            if f.get("patch"):
                st.markdown("**Actionable Code Patch:**")
                st.code(f.get("patch"), language="html")

            # Validate action button
            if val_status != "validated":
                if st.button(f"Re-Validate Fix #{f_id[:8]}", key=f"btn_val_{f_id}", type="primary"):
                    with st.spinner("Running strict automated validation..."):
                        v_res = post_api_data(f"/audit/validate/{f_id}")
                        if v_res and v_res.get("validation_status") == "validated":
                            st.toast("Validation successful: Fix verified!", icon=":material/verified:")
                            st.rerun()
                        elif v_res:
                            st.warning(f"Validation outcome: {v_res.get('validation_status')}")
                        else:
                            st.error("Validation request failed.")
