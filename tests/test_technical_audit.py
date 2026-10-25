"""Comprehensive tests for Module 6 — Technical SEO/AEO/GEO Auditor.

Verifies indexability signals, metadata, headings, canonical links, sitemaps, robots.txt,
internal links, performance signals, structured data, optional llms.txt discovery checks,
composite health scoring, and strict fix validation workflows.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.audit.html_inspector import HTMLPageInspector
from app.audit.technical_audit import TechnicalAuditor
from app.database.repositories.audit_repo import AuditFindingRepository
from app.schemas.audit import AuditFindingCreate, AuditReport, PageAuditRequest
from app.schemas.common import AuditSeverity, AuditStatus, ValidationStatus
from tests.fixtures.html_fixtures import (
    DEFECTIVE_METADATA_HTML,
    GENERIC_LINKS_HTML,
    HEADING_HIERARCHY_DEFECT_HTML,
    MALFORMED_SCHEMA_HTML,
    NOINDEX_PAGE_HTML,
    PERFECT_PAGE_HTML,
    SAMPLE_INVALID_SITEMAP_XML,
    SAMPLE_LLMS_TXT,
    SAMPLE_ROBOTS_TXT_DISALLOWED,
    SAMPLE_ROBOTS_TXT_HEALTHY,
    SAMPLE_SITEMAP_XML,
)


def test_html_inspector_dom_parsing():
    """Verify HTMLPageInspector accurately extracts all DOM elements from HTML fixture."""
    inspector = HTMLPageInspector.inspect(PERFECT_PAGE_HTML, target_url="https://incubrix.com/features")

    assert inspector.title == "IncuBrix - AI Visibility Engine for Creators"
    assert "Boost your organic creator visibility" in (inspector.meta_description or "")
    assert inspector.meta_robots == ["index", "follow"]
    assert inspector.canonical_hrefs == ["https://incubrix.com/features"]
    assert inspector.h1_tags == ["IncuBrix AI Visibility Engine"]
    assert len(inspector.h2_tags) == 2
    assert inspector.h2_tags[0] == "Real-time AEO Tracking"
    assert len(inspector.images) == 1
    assert inspector.images[0]["has_alt"] is True
    assert len(inspector.json_ld_schemas) == 1
    assert inspector.json_ld_schemas[0]["@type"] == "WebPage"
    assert inspector.html_size_bytes > 0


def test_audit_indexability_signals():
    """Verify indexability audits (meta robots, HTTP status codes, X-Robots-Tag)."""
    target = "https://incubrix.com/test"

    # Status 200 OK passes
    ok_findings = TechnicalAuditor.audit_indexability(target, status_code=200, meta_robots=["index", "follow"])
    assert any(f.issue_code == "INDEXABILITY_STATUS_OK" and f.status == AuditStatus.PASS for f in ok_findings)
    assert any(f.issue_code == "INDEXABILITY_PERMITTED" and f.status == AuditStatus.PASS for f in ok_findings)

    # Status 301 Redirect warning
    redir_findings = TechnicalAuditor.audit_indexability(target, status_code=301)
    assert any(f.issue_code == "INDEXABILITY_REDIRECT" and f.status == AuditStatus.WARNING for f in redir_findings)

    # Status 500 Server Error critical failure
    err_findings = TechnicalAuditor.audit_indexability(target, status_code=500)
    assert any(f.issue_code == "INDEXABILITY_HTTP_ERROR" and f.severity == AuditSeverity.CRITICAL for f in err_findings)

    # Meta robots noindex critical failure with patch
    noindex_findings = TechnicalAuditor.audit_indexability(target, status_code=200, meta_robots=["noindex", "nofollow"])
    noindex_issue = next(f for f in noindex_findings if f.issue_code == "NOINDEX_DETECTED")
    assert noindex_issue.status == AuditStatus.FAIL
    assert noindex_issue.severity == AuditSeverity.CRITICAL
    assert 'content="index, follow"' in (noindex_issue.patch or "")

    # X-Robots-Tag header noindex
    x_findings = TechnicalAuditor.audit_indexability(target, status_code=200, headers={"X-Robots-Tag": "noindex, noarchive"})
    assert any(f.issue_code == "X_ROBOTS_NOINDEX" and f.severity == AuditSeverity.CRITICAL for f in x_findings)


def test_audit_metadata_title_and_description():
    """Verify title and description tag evaluation, bounds checking, and patch suggestions."""
    target = "https://incubrix.com/page"

    # Missing title is HIGH severity failure
    res_no_title = TechnicalAuditor.audit_metadata(target, title=None, description="Valid descriptive summary text that satisfies length requirements.")
    assert any(f.issue_code == "MISSING_TITLE" and f.severity == AuditSeverity.HIGH for f in res_no_title)

    # Short title warning
    res_short = TechnicalAuditor.audit_metadata(target, title="Short", description="Valid descriptive summary text that satisfies length requirements.")
    assert any(f.issue_code == "TITLE_TOO_SHORT" and f.status == AuditStatus.WARNING for f in res_short)

    # Optimal title passes
    res_optimal = TechnicalAuditor.audit_metadata(target, title="IncuBrix - AI Visibility Engine for Creators", description="Valid descriptive summary text that satisfies length requirements.")
    assert any(f.issue_code == "TITLE_OPTIMAL" and f.status == AuditStatus.PASS for f in res_optimal)

    # Missing description is MEDIUM severity failure
    res_no_desc = TechnicalAuditor.audit_metadata(target, title="Optimal Length Title For Creators", description=None)
    desc_issue = next(f for f in res_no_desc if f.issue_code == "MISSING_META_DESCRIPTION")
    assert desc_issue.severity == AuditSeverity.MEDIUM
    assert desc_issue.patch is not None


def test_audit_headings_and_hierarchy():
    """Verify single <h1> enforcement, multiple <h1> detection, and heading hierarchy."""
    target = "https://incubrix.com/headings"

    # Missing H1
    res_no_h1 = TechnicalAuditor.audit_headings(target, h1_tags=[], h2_tags=["Topic 1"], h3_tags=[])
    assert any(f.issue_code == "MISSING_H1" and f.status == AuditStatus.FAIL for f in res_no_h1)

    # Multiple H1s
    res_multi = TechnicalAuditor.audit_headings(target, h1_tags=["Main Title", "Duplicate Title"], h2_tags=["Topic 1"], h3_tags=[])
    assert any(f.issue_code == "MULTIPLE_H1" and f.status == AuditStatus.WARNING for f in res_multi)

    # No H2 subheadings warning
    res_no_h2 = TechnicalAuditor.audit_headings(target, h1_tags=["Main Title"], h2_tags=[], h3_tags=[])
    assert any(f.issue_code == "NO_H2_SUBHEADINGS" and f.status == AuditStatus.WARNING for f in res_no_h2)

    # Clean hierarchy passes
    res_clean = TechnicalAuditor.audit_headings(target, h1_tags=["Main Title"], h2_tags=["Sub 1", "Sub 2"], h3_tags=["Detail A"])
    assert any(f.issue_code == "H1_OPTIMAL" and f.status == AuditStatus.PASS for f in res_clean)
    assert any(f.issue_code == "HEADINGS_STRUCTURED" and f.status == AuditStatus.PASS for f in res_clean)


def test_audit_canonical_links():
    """Verify canonical link presence, relative URL warnings, and conflict detection."""
    target = "https://incubrix.com/features"

    # Missing canonical
    res_missing = TechnicalAuditor.audit_canonical(target, canonical_hrefs=[])
    assert any(f.issue_code == "MISSING_CANONICAL" and f.status == AuditStatus.FAIL for f in res_missing)

    # Multiple conflicting canonicals
    res_multi = TechnicalAuditor.audit_canonical(target, canonical_hrefs=["https://incubrix.com/a", "https://incubrix.com/b"])
    assert any(f.issue_code == "MULTIPLE_CANONICALS" and f.severity == AuditSeverity.HIGH for f in res_multi)

    # Relative canonical warning with absolute patch
    res_rel = TechnicalAuditor.audit_canonical(target, canonical_hrefs=["/features"])
    rel_issue = next(f for f in res_rel if f.issue_code == "RELATIVE_CANONICAL")
    assert rel_issue.status == AuditStatus.WARNING
    assert 'href="https://incubrix.com/features"' in (rel_issue.patch or "")

    # Valid canonical
    res_valid = TechnicalAuditor.audit_canonical(target, canonical_hrefs=["https://incubrix.com/features"])
    assert any(f.issue_code == "CANONICAL_VALID" and f.status == AuditStatus.PASS for f in res_valid)


def test_audit_robots_txt():
    """Verify robots.txt AI bot detection, blanket disallow blocking, and sitemap directives."""
    target = "https://incubrix.com"

    # Healthy robots.txt
    res_healthy = TechnicalAuditor.audit_robots_rules(SAMPLE_ROBOTS_TXT_HEALTHY, target)
    assert any(f.issue_code == "AI_BOTS_PERMITTED" and f.status == AuditStatus.PASS for f in res_healthy)

    # Disallowed robots.txt
    res_blocked = TechnicalAuditor.audit_robots_rules(SAMPLE_ROBOTS_TXT_DISALLOWED, target)
    assert any(f.issue_code == "AI_BOTS_RESTRICTED" and f.severity == AuditSeverity.MEDIUM for f in res_blocked)
    assert any(f.issue_code == "ROBOTS_MISSING_SITEMAP" and f.status == AuditStatus.WARNING for f in res_blocked)

    # Missing robots.txt
    res_missing = TechnicalAuditor.audit_robots_rules(None, target)
    assert any(f.issue_code == "MISSING_ROBOTS_TXT" and f.status == AuditStatus.FAIL for f in res_missing)


def test_audit_sitemap_xml():
    """Verify sitemap parsing, XML error handling, and target URL containment."""
    target = "https://incubrix.com/features"

    # Valid sitemap containing target URL
    res_valid = TechnicalAuditor.audit_sitemap(SAMPLE_SITEMAP_XML, target)
    assert any(f.issue_code == "SITEMAP_CONTAINS_URL" and f.status == AuditStatus.PASS for f in res_valid)

    # Invalid XML
    res_invalid = TechnicalAuditor.audit_sitemap(SAMPLE_INVALID_SITEMAP_XML, target)
    assert any(f.issue_code == "INVALID_SITEMAP_XML" and f.status == AuditStatus.FAIL for f in res_invalid)

    # Missing sitemap
    res_missing = TechnicalAuditor.audit_sitemap(None, target)
    assert any(f.issue_code == "MISSING_SITEMAP" and f.status == AuditStatus.WARNING for f in res_missing)


def test_audit_internal_links():
    """Verify placeholder link (# and javascript:) and non-descriptive anchor detection."""
    target = "https://incubrix.com/links"
    inspector = HTMLPageInspector.inspect(GENERIC_LINKS_HTML, target_url=target)

    findings = TechnicalAuditor.audit_internal_links(target, inspector.links)
    assert any(f.issue_code == "EMPTY_OR_PLACEHOLDER_LINKS" and f.status == AuditStatus.WARNING for f in findings)
    assert any(f.issue_code == "NON_DESCRIPTIVE_ANCHOR_TEXT" and f.status == AuditStatus.WARNING for f in findings)


def test_audit_performance_signals():
    """Verify performance metrics: latency bands, HTML size, render blocking scripts, image alts."""
    target = "https://incubrix.com/perf"

    # Fast latency < 600ms
    fast_res = TechnicalAuditor.audit_performance(target, response_time_ms=180.0, html_size_bytes=45_000)
    assert any(f.issue_code == "PERFORMANCE_FAST_RESPONSE" and f.status == AuditStatus.PASS for f in fast_res)

    # Slow latency > 2000ms
    slow_res = TechnicalAuditor.audit_performance(target, response_time_ms=2800.0, html_size_bytes=600_000)
    assert any(f.issue_code == "PERFORMANCE_SLOW_RESPONSE" and f.status == AuditStatus.FAIL for f in slow_res)
    assert any(f.issue_code == "PERFORMANCE_LARGE_HTML_PAYLOAD" and f.status == AuditStatus.WARNING for f in slow_res)

    # Unmeasured latency explicitly marked UNKNOWN
    unmeasured = TechnicalAuditor.audit_performance(target, response_time_ms=None)
    assert any(f.issue_code == "PERFORMANCE_LATENCY_UNAVAILABLE" and f.status == AuditStatus.UNKNOWN for f in unmeasured)

    # Images missing alt attribute
    inspector = HTMLPageInspector.inspect(MALFORMED_SCHEMA_HTML, target_url=target)
    media_res = TechnicalAuditor.audit_performance(target, images=inspector.images)
    assert any(f.issue_code == "ACCESSIBILITY_IMAGES_MISSING_ALT" and f.status == AuditStatus.WARNING for f in media_res)


def test_audit_structured_data_schema_org():
    """Verify Schema.org JSON-LD extraction, syntax validation, and missing schema warnings."""
    target = "https://incubrix.com/schema"

    # Valid schema from PERFECT_PAGE_HTML
    p_insp = HTMLPageInspector.inspect(PERFECT_PAGE_HTML, target_url=target)
    p_res = TechnicalAuditor.audit_structured_data(target, p_insp.json_ld_schemas, p_insp.json_ld_errors)
    assert any(f.issue_code == "STRUCTURED_DATA_VALID" and f.status == AuditStatus.PASS for f in p_res)

    # Malformed schema syntax from MALFORMED_SCHEMA_HTML
    m_insp = HTMLPageInspector.inspect(MALFORMED_SCHEMA_HTML, target_url=target)
    m_res = TechnicalAuditor.audit_structured_data(target, m_insp.json_ld_schemas, m_insp.json_ld_errors)
    assert any(f.issue_code == "INVALID_JSON_LD" and f.status == AuditStatus.FAIL for f in m_res)

    # Missing schema
    no_schema_res = TechnicalAuditor.audit_structured_data(target, [], [])
    assert any(f.issue_code == "MISSING_STRUCTURED_DATA" and f.status == AuditStatus.FAIL for f in no_schema_res)


def test_audit_llms_txt_optional_discovery_check():
    """Requirement: Treat llms.txt as an optional discovery check, NOT a guaranteed ranking requirement."""
    target = "https://incubrix.com"

    # Present llms.txt
    res_present = TechnicalAuditor.audit_llms_txt(SAMPLE_LLMS_TXT, target)
    present_item = next(f for f in res_present if f.issue_code == "OPTIONAL_LLMS_TXT_PRESENT")
    assert present_item.status == AuditStatus.PASS
    assert present_item.severity == AuditSeverity.INFO

    # Missing llms.txt must NOT be critical or high
    res_missing = TechnicalAuditor.audit_llms_txt(None, target)
    missing_item = next(f for f in res_missing if f.issue_code == "OPTIONAL_LLMS_TXT_MISSING")
    assert missing_item.severity == AuditSeverity.INFO
    # Verify description explicitly states it is optional and not a guaranteed ranking requirement
    assert "optional discovery" in missing_item.description.lower()
    assert "not a guaranteed search engine ranking requirement" in missing_item.description.lower()


def test_full_page_audit_orchestration_and_health_score():
    """Verify full multi-category page audit orchestration and weighted health score computation."""
    target = "https://incubrix.com/features"

    # Perfect page should yield near-perfect health score
    perfect_report = TechnicalAuditor.audit_page(
        target_url=target,
        html_content=PERFECT_PAGE_HTML,
        status_code=200,
        response_time_ms=120.0,
        robots_txt_content=SAMPLE_ROBOTS_TXT_HEALTHY,
        sitemap_xml_content=SAMPLE_SITEMAP_XML,
        llms_txt_content=SAMPLE_LLMS_TXT,
    )

    assert isinstance(perfect_report, AuditReport)
    assert perfect_report.failed_count == 0
    assert perfect_report.health_score >= 95.0
    assert len(perfect_report.findings) > 0
    assert "metadata" in perfect_report.summary_by_category
    assert "structured_data" in perfect_report.summary_by_category

    # Defective page should reflect failures and lower health score
    defective_report = TechnicalAuditor.audit_page(
        target_url=target,
        html_content=DEFECTIVE_METADATA_HTML,
        status_code=200,
        robots_txt_content=None,
        sitemap_xml_content=None,
        llms_txt_content=None,
    )
    assert defective_report.failed_count > 0
    assert defective_report.health_score < 70.0


def test_strict_fix_validation_workflow():
    """Requirement: Never claim a fix is validated without running an appropriate check.

    Mark unavailable checks explicitly.
    """
    target = "https://incubrix.com/title-test"
    finding = AuditFindingCreate(
        target_url=target,
        audit_category="metadata",
        issue_code="MISSING_TITLE",
        severity=AuditSeverity.HIGH,
        status=AuditStatus.FAIL,
        description="Missing title",
    )

    # 1. Validation attempt with NO new HTML or parameters -> UNAVAILABLE
    res_unavail = TechnicalAuditor.validate_fix(finding, updated_html=None)
    assert res_unavail.validation_status == ValidationStatus.UNAVAILABLE
    assert res_unavail.is_resolved is False
    assert "unavailable" in res_unavail.explanation.lower()

    # 2. Validation attempt with still-defective HTML (still missing title) -> FAILED
    still_broken_html = "<html><body><h1>No title here</h1></body></html>"
    res_failed = TechnicalAuditor.validate_fix(finding, updated_html=still_broken_html)
    assert res_failed.validation_status == ValidationStatus.FAILED
    assert res_failed.is_resolved is False

    # 3. Validation attempt with fixed HTML containing optimal title -> VALIDATED
    fixed_html = "<html><head><title>IncuBrix - Creator Visibility Platform</title></head><body><h1>Content</h1></body></html>"
    res_valid = TechnicalAuditor.validate_fix(finding, updated_html=fixed_html)
    assert res_valid.validation_status == ValidationStatus.VALIDATED
    assert res_valid.is_resolved is True
    assert "fix validated" in res_valid.explanation.lower()


def test_technical_audit_api_endpoints(client: TestClient, db_session: Session):
    """Verify HTTP API endpoints: /v1/audit/run, /v1/audit/validate, /v1/audit/findings, /v1/audit/summary."""
    target_url = "https://incubrix.com/api-test"

    # 1. Run audit via API with offline HTML payload
    payload = {
        "target_url": target_url,
        "html_content": DEFECTIVE_METADATA_HTML,
        "status_code": 200,
        "store_findings": True,
    }
    run_resp = client.post("/v1/audit/run", json=payload)
    assert run_resp.status_code == 200
    report_data = run_resp.json()
    assert report_data["target_url"] == target_url
    assert report_data["failed_count"] > 0
    assert len(report_data["findings"]) > 0

    # Pick a finding from the report (e.g. MISSING_TITLE)
    title_finding = next((f for f in report_data["findings"] if f["issue_code"] == "MISSING_TITLE"), None)
    assert title_finding is not None
    finding_id = title_finding["id"]

    # 2. Recheck validation via API without updated content -> returns UNAVAILABLE
    val_payload_empty = {"updated_html": None}
    val_resp_empty = client.post(f"/v1/audit/validate/{finding_id}", json=val_payload_empty)
    assert val_resp_empty.status_code == 200
    val_data_empty = val_resp_empty.json()
    assert val_data_empty["validation_status"] == "unavailable"

    # 3. Recheck validation via API with fixed HTML -> returns VALIDATED
    val_payload_fixed = {
        "updated_html": "<html><head><title>Optimal Page Title For Validation Test</title></head></html>"
    }
    val_resp_fixed = client.post(f"/v1/audit/validate/{finding_id}", json=val_payload_fixed)
    assert val_resp_fixed.status_code == 200
    val_data_fixed = val_resp_fixed.json()
    assert val_data_fixed["validation_status"] == "validated"
    assert val_data_fixed["is_resolved"] is True

    # 4. Query findings with filters
    list_resp = client.get(f"/v1/audit/findings?url={target_url}&category=metadata")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) > 0

    # 5. Query audit summary
    sum_resp = client.get(f"/v1/audit/summary?url={target_url}")
    assert sum_resp.status_code == 200
    summary = sum_resp.json()
    assert summary["total_findings"] > 0
    assert "status_distribution" in summary
    assert "validation_distribution" in summary
