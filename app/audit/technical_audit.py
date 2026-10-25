"""Technical SEO, AEO, and GEO Audit Engine.

Evaluates indexability signals, title/description metadata, headings, canonical links,
robots.txt, sitemaps, internal links, performance signals, and Schema.org structured data.
Treats llms.txt as an optional discovery check, never as a guaranteed ranking requirement.
Produces evidence-backed findings with concrete recommendations, code patches, and strict
fix validation workflows.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx

from app.audit.html_inspector import HTMLPageInspector
from app.logging_config import get_logger
from app.schemas.audit import (
    AuditFindingCreate,
    AuditFindingRead,
    AuditReport,
    FixValidationResponse,
)
from app.schemas.common import AuditSeverity, AuditStatus, ValidationStatus

logger = get_logger("incubrix.audit")


class TechnicalAuditor:
    """Production modular Technical SEO, AEO, and GEO auditor."""

    USER_AGENT = "IncuBrix-Auditor/1.0 (+https://incubrix.com/bot)"

    # -------------------------------------------------------------------------
    # 1. Indexability Signals
    # -------------------------------------------------------------------------
    @staticmethod
    def audit_indexability(
        target_url: str,
        status_code: Optional[int] = 200,
        headers: Optional[Dict[str, str]] = None,
        meta_robots: Optional[List[str]] = None,
    ) -> List[AuditFindingCreate]:
        """Audit HTTP response status codes and robots directives (meta and X-Robots-Tag)."""
        findings: List[AuditFindingCreate] = []
        meta_robots_list = [r.lower() for r in (meta_robots or [])]
        headers_dict = {k.lower(): v.lower() for k, v in (headers or {}).items()}

        # 1.1 HTTP Status Code
        if status_code is None:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="indexability",
                    issue_code="INDEXABILITY_STATUS_UNKNOWN",
                    severity=AuditSeverity.INFO,
                    status=AuditStatus.UNKNOWN,
                    confidence=0.5,
                    description="HTTP response status code was unavailable or unmeasured.",
                    recommendation="Ensure the target endpoint is reachable over HTTP/HTTPS.",
                    raw_metrics={"status_code": None},
                )
            )
        elif 200 <= status_code < 300:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="indexability",
                    issue_code="INDEXABILITY_STATUS_OK",
                    severity=AuditSeverity.INFO,
                    status=AuditStatus.PASS,
                    confidence=1.0,
                    description=f"HTTP status code {status_code} indicates the page is accessible.",
                    raw_metrics={"status_code": status_code},
                )
            )
        elif 300 <= status_code < 400:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="indexability",
                    issue_code="INDEXABILITY_REDIRECT",
                    severity=AuditSeverity.LOW,
                    status=AuditStatus.WARNING,
                    confidence=1.0,
                    description=f"HTTP status code {status_code} indicates a redirect.",
                    recommendation="Ensure redirect targets resolve directly to canonical URLs to preserve crawl equity.",
                    raw_metrics={"status_code": status_code},
                )
            )
        else:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="indexability",
                    issue_code="INDEXABILITY_HTTP_ERROR",
                    severity=AuditSeverity.CRITICAL,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description=f"HTTP status code {status_code} returned; search engines cannot index error responses.",
                    recommendation="Investigate server logs or upstream routing to return HTTP 200 OK.",
                    raw_metrics={"status_code": status_code},
                )
            )

        # 1.2 Meta Robots Tag
        if "noindex" in meta_robots_list or "none" in meta_robots_list:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="indexability",
                    issue_code="NOINDEX_DETECTED",
                    severity=AuditSeverity.CRITICAL,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description="Page contains a 'noindex' directive in the <meta name='robots'> tag, blocking search indexation.",
                    recommendation="Remove 'noindex' from the meta robots tag if this page is intended for organic search/AEO discovery.",
                    patch='<meta name="robots" content="index, follow">',
                    raw_metrics={"meta_robots": meta_robots_list},
                )
            )
        elif "nofollow" in meta_robots_list:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="indexability",
                    issue_code="NOFOLLOW_DETECTED",
                    severity=AuditSeverity.MEDIUM,
                    status=AuditStatus.WARNING,
                    confidence=1.0,
                    description="Page contains a 'nofollow' directive in the meta robots tag, preventing search engines from passing link equity.",
                    recommendation="Change 'nofollow' to 'follow' if outgoing links should be crawled and credited.",
                    patch='<meta name="robots" content="index, follow">',
                    raw_metrics={"meta_robots": meta_robots_list},
                )
            )

        # 1.3 X-Robots-Tag Header
        x_robots = headers_dict.get("x-robots-tag", "")
        if "noindex" in x_robots or "none" in x_robots:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="indexability",
                    issue_code="X_ROBOTS_NOINDEX",
                    severity=AuditSeverity.CRITICAL,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description="HTTP header 'X-Robots-Tag' contains 'noindex', preventing search engines from indexing the document.",
                    recommendation="Remove the 'noindex' directive from web server configuration headers.",
                    patch="Header set X-Robots-Tag 'index, follow'",
                    raw_metrics={"x_robots_tag": x_robots},
                )
            )

        if not any(f.status in (AuditStatus.FAIL, AuditStatus.WARNING) for f in findings):
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="indexability",
                    issue_code="INDEXABILITY_PERMITTED",
                    severity=AuditSeverity.INFO,
                    status=AuditStatus.PASS,
                    confidence=1.0,
                    description="No indexability blocking directives found. The page is indexable.",
                    raw_metrics={"meta_robots": meta_robots_list, "x_robots_tag": x_robots},
                )
            )

        return findings

    # -------------------------------------------------------------------------
    # 2. Metadata (Title & Meta Description)
    # -------------------------------------------------------------------------
    @staticmethod
    def audit_metadata(
        target_url: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> List[AuditFindingCreate]:
        """Audit HTML <title> and <meta name='description'> tags."""
        findings: List[AuditFindingCreate] = []

        # 2.1 Title Check
        if not title or not title.strip():
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="metadata",
                    issue_code="MISSING_TITLE",
                    severity=AuditSeverity.HIGH,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description="Page is missing a <title> element in the HTML <head>.",
                    recommendation="Add a descriptive, concise <title> between 30 and 60 characters.",
                    patch="<title>Descriptive Topic Title - IncuBrix</title>",
                    raw_metrics={"title": None, "length": 0},
                )
            )
        else:
            clean_title = title.strip()
            title_len = len(clean_title)
            if title_len < 20:
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="metadata",
                        issue_code="TITLE_TOO_SHORT",
                        severity=AuditSeverity.LOW,
                        status=AuditStatus.WARNING,
                        confidence=1.0,
                        description=f"Title is only {title_len} characters long (recommended: 30-60 characters).",
                        recommendation="Expand the title with target topic keywords and brand branding.",
                        patch=f"<title>{clean_title} | Comprehensive Guide - IncuBrix</title>",
                        raw_metrics={"title": clean_title, "length": title_len},
                    )
                )
            elif title_len > 65:
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="metadata",
                        issue_code="TITLE_TOO_LONG",
                        severity=AuditSeverity.LOW,
                        status=AuditStatus.WARNING,
                        confidence=1.0,
                        description=f"Title is {title_len} characters long and may be truncated in search results.",
                        recommendation="Shorten the title to 60 characters or fewer to avoid truncation.",
                        raw_metrics={"title": clean_title, "length": title_len},
                    )
                )
            else:
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="metadata",
                        issue_code="TITLE_OPTIMAL",
                        severity=AuditSeverity.INFO,
                        status=AuditStatus.PASS,
                        confidence=1.0,
                        description=f"Title length ({title_len} chars) is within the optimal 30-60 character range.",
                        raw_metrics={"title": clean_title, "length": title_len},
                    )
                )

        # 2.2 Meta Description Check
        if not description or not description.strip():
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="metadata",
                    issue_code="MISSING_META_DESCRIPTION",
                    severity=AuditSeverity.MEDIUM,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description="Page is missing a <meta name='description'> tag.",
                    recommendation="Add a compelling meta description between 50 and 160 characters summarizing the page.",
                    patch='<meta name="description" content="Discover how to optimize creator visibility with automated b-roll and AI workflow engine.">',
                    raw_metrics={"description": None, "length": 0},
                )
            )
        else:
            clean_desc = description.strip()
            desc_len = len(clean_desc)
            if desc_len < 50:
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="metadata",
                        issue_code="META_DESCRIPTION_TOO_SHORT",
                        severity=AuditSeverity.LOW,
                        status=AuditStatus.WARNING,
                        confidence=1.0,
                        description=f"Meta description is only {desc_len} characters (recommended: 50-160 characters).",
                        recommendation="Expand the meta description to give searchers and AI bots a comprehensive summary.",
                        raw_metrics={"description": clean_desc, "length": desc_len},
                    )
                )
            elif desc_len > 165:
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="metadata",
                        issue_code="META_DESCRIPTION_TOO_LONG",
                        severity=AuditSeverity.LOW,
                        status=AuditStatus.WARNING,
                        confidence=1.0,
                        description=f"Meta description is {desc_len} characters long and may be truncated in search snippets.",
                        recommendation="Condense the meta description to 160 characters or fewer.",
                        raw_metrics={"description": clean_desc, "length": desc_len},
                    )
                )
            else:
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="metadata",
                        issue_code="META_DESCRIPTION_OPTIMAL",
                        severity=AuditSeverity.INFO,
                        status=AuditStatus.PASS,
                        confidence=1.0,
                        description=f"Meta description length ({desc_len} chars) is optimal.",
                        raw_metrics={"description": clean_desc, "length": desc_len},
                    )
                )

        return findings

    # -------------------------------------------------------------------------
    # 3. Headings Structure (H1, H2, H3)
    # -------------------------------------------------------------------------
    @staticmethod
    def audit_headings(
        target_url: str,
        h1_tags: List[str],
        h2_tags: List[str],
        h3_tags: List[str],
    ) -> List[AuditFindingCreate]:
        """Audit heading tag presence and hierarchical structure."""
        findings: List[AuditFindingCreate] = []
        h1_count = len(h1_tags)

        if h1_count == 0:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="headings",
                    issue_code="MISSING_H1",
                    severity=AuditSeverity.HIGH,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description="Page is missing a primary <h1> heading tag.",
                    recommendation="Add a single <h1> heading clearly stating the main page topic.",
                    patch="<h1>Automating Video B-Roll Workflows with AI</h1>",
                    raw_metrics={"h1_count": 0, "h2_count": len(h2_tags), "h3_count": len(h3_tags)},
                )
            )
        elif h1_count > 1:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="headings",
                    issue_code="MULTIPLE_H1",
                    severity=AuditSeverity.MEDIUM,
                    status=AuditStatus.WARNING,
                    confidence=1.0,
                    description=f"Page contains {h1_count} conflicting <h1> headings. Best practice is exactly one <h1>.",
                    recommendation="Consolidate headings into a single primary <h1> and convert secondary headers to <h2>.",
                    patch="<!-- Convert secondary <h1> elements to <h2> -->\n<h2>Secondary Topic Section</h2>",
                    raw_metrics={"h1_count": h1_count, "h1_texts": h1_tags},
                )
            )
        else:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="headings",
                    issue_code="H1_OPTIMAL",
                    severity=AuditSeverity.INFO,
                    status=AuditStatus.PASS,
                    confidence=1.0,
                    description=f"Page has exactly one primary <h1> heading: '{h1_tags[0]}'.",
                    raw_metrics={"h1_count": 1, "h1_text": h1_tags[0]},
                )
            )

        if len(h2_tags) == 0 and h1_count > 0:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="headings",
                    issue_code="NO_H2_SUBHEADINGS",
                    severity=AuditSeverity.LOW,
                    status=AuditStatus.WARNING,
                    confidence=0.9,
                    description="Page has no <h2> subheadings to divide content into structured sections.",
                    recommendation="Introduce <h2> subheadings to aid readability and AI content section extraction.",
                    patch="<h2>Key Capabilities</h2>\n<p>Details here...</p>",
                    raw_metrics={"h2_count": 0},
                )
            )
        elif len(h2_tags) > 0:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="headings",
                    issue_code="HEADINGS_STRUCTURED",
                    severity=AuditSeverity.INFO,
                    status=AuditStatus.PASS,
                    confidence=1.0,
                    description=f"Page has a structured heading outline with {len(h2_tags)} <h2> and {len(h3_tags)} <h3> elements.",
                    raw_metrics={"h2_count": len(h2_tags), "h3_count": len(h3_tags)},
                )
            )

        return findings

    # -------------------------------------------------------------------------
    # 4. Canonical Links
    # -------------------------------------------------------------------------
    @staticmethod
    def audit_canonical(
        target_url: str,
        canonical_hrefs: List[str],
    ) -> List[AuditFindingCreate]:
        """Audit canonical link tag presence, validity, and uniqueness."""
        findings: List[AuditFindingCreate] = []
        count = len(canonical_hrefs)

        if count == 0:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="canonical",
                    issue_code="MISSING_CANONICAL",
                    severity=AuditSeverity.MEDIUM,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description="Page does not declare a canonical URL (<link rel='canonical'>).",
                    recommendation="Add a self-referential or authoritative canonical tag to prevent duplicate content dilution.",
                    patch=f'<link rel="canonical" href="{target_url}" />',
                    raw_metrics={"canonical_count": 0},
                )
            )
        elif count > 1:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="canonical",
                    issue_code="MULTIPLE_CANONICALS",
                    severity=AuditSeverity.HIGH,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description=f"Page contains {count} conflicting canonical tags. Search engines will disregard all canonical declarations.",
                    recommendation="Remove duplicate canonical declarations, leaving a single authoritative link tag.",
                    raw_metrics={"canonical_count": count, "hrefs": canonical_hrefs},
                )
            )
        else:
            href = canonical_hrefs[0].strip()
            if not href.startswith(("http://", "https://")):
                absolute_url = urljoin(target_url, href)
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="canonical",
                        issue_code="RELATIVE_CANONICAL",
                        severity=AuditSeverity.MEDIUM,
                        status=AuditStatus.WARNING,
                        confidence=1.0,
                        description=f"Canonical URL '{href}' is relative. Search engines strongly recommend absolute URLs.",
                        recommendation="Convert relative canonical URL to an absolute URL with scheme and host.",
                        patch=f'<link rel="canonical" href="{absolute_url}" />',
                        raw_metrics={"canonical_href": href, "absolute_url": absolute_url},
                    )
                )
            else:
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="canonical",
                        issue_code="CANONICAL_VALID",
                        severity=AuditSeverity.INFO,
                        status=AuditStatus.PASS,
                        confidence=1.0,
                        description=f"Valid absolute canonical tag declared: '{href}'.",
                        raw_metrics={"canonical_href": href},
                    )
                )

        return findings

    # -------------------------------------------------------------------------
    # 5. Internal Links
    # -------------------------------------------------------------------------
    @staticmethod
    def audit_internal_links(
        target_url: str,
        links: List[Dict[str, Any]],
    ) -> List[AuditFindingCreate]:
        """Audit anchor links for broken placeholders, internal structure, and generic anchors."""
        findings: List[AuditFindingCreate] = []

        empty_links = [l for l in links if l.get("is_empty")]
        generic_terms = {"click here", "here", "read more", "learn more", "link", "more", "details"}
        generic_links = [
            l for l in links if l.get("text", "").strip().lower() in generic_terms
        ]
        internal_links = [l for l in links if l.get("is_internal") and not l.get("is_empty")]

        if empty_links:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="internal_links",
                    issue_code="EMPTY_OR_PLACEHOLDER_LINKS",
                    severity=AuditSeverity.LOW,
                    status=AuditStatus.WARNING,
                    confidence=1.0,
                    description=f"Found {len(empty_links)} placeholder links (href='', '#', or 'javascript:').",
                    recommendation="Replace placeholder links with navigable, crawlable URLs.",
                    patch='<a href="/target-topic-path">Descriptive Anchor Text</a>',
                    raw_metrics={"empty_links_count": len(empty_links)},
                )
            )

        if generic_links:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="internal_links",
                    issue_code="NON_DESCRIPTIVE_ANCHOR_TEXT",
                    severity=AuditSeverity.LOW,
                    status=AuditStatus.WARNING,
                    confidence=0.95,
                    description=(
                        f"Found {len(generic_links)} links with non-descriptive anchor text "
                        f"(e.g. 'click here', 'read more'). Non-descriptive anchors reduce semantic topical relevance."
                    ),
                    recommendation="Replace generic phrases with keyword-rich phrases describing the target resource.",
                    patch='<!-- Instead of "Click here": -->\n<a href="/features">Explore automated AI b-roll features</a>',
                    raw_metrics={"generic_links_count": len(generic_links)},
                )
            )

        if len(internal_links) > 0 and not empty_links:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="internal_links",
                    issue_code="INTERNAL_LINKS_HEALTHY",
                    severity=AuditSeverity.INFO,
                    status=AuditStatus.PASS,
                    confidence=1.0,
                    description=f"Page has {len(internal_links)} valid internal links facilitating navigation and crawl depth.",
                    raw_metrics={"internal_links_count": len(internal_links), "total_links": len(links)},
                )
            )

        return findings

    # -------------------------------------------------------------------------
    # 6. Basic Performance Signals
    # -------------------------------------------------------------------------
    @staticmethod
    def audit_performance(
        target_url: str,
        response_time_ms: Optional[float] = None,
        html_size_bytes: int = 0,
        scripts: Optional[List[Dict[str, Any]]] = None,
        images: Optional[List[Dict[str, Any]]] = None,
    ) -> List[AuditFindingCreate]:
        """Audit basic web performance signals including latency, payload size, and media attributes."""
        findings: List[AuditFindingCreate] = []
        scripts_list = scripts or []
        images_list = images or []

        # 6.1 Response Latency
        if response_time_ms is not None:
            if response_time_ms < 600:
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="performance",
                        issue_code="PERFORMANCE_FAST_RESPONSE",
                        severity=AuditSeverity.INFO,
                        status=AuditStatus.PASS,
                        confidence=1.0,
                        description=f"Response time ({response_time_ms:.1f}ms) is fast and within recommended limits.",
                        raw_metrics={"response_time_ms": response_time_ms},
                    )
                )
            elif response_time_ms <= 2000:
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="performance",
                        issue_code="PERFORMANCE_MODERATE_RESPONSE",
                        severity=AuditSeverity.LOW,
                        status=AuditStatus.WARNING,
                        confidence=1.0,
                        description=f"Response time ({response_time_ms:.1f}ms) is moderate; target under 600ms for optimal crawl speed.",
                        recommendation="Implement edge caching or database query optimization to reduce server latency.",
                        raw_metrics={"response_time_ms": response_time_ms},
                    )
                )
            else:
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="performance",
                        issue_code="PERFORMANCE_SLOW_RESPONSE",
                        severity=AuditSeverity.MEDIUM,
                        status=AuditStatus.FAIL,
                        confidence=1.0,
                        description=f"Response time ({response_time_ms:.1f}ms) exceeds the 2000ms threshold.",
                        recommendation="Investigate server bottlenecks, enable HTTP/2 or HTTP/3, and leverage CDN caching.",
                        raw_metrics={"response_time_ms": response_time_ms},
                    )
                )
        else:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="performance",
                    issue_code="PERFORMANCE_LATENCY_UNAVAILABLE",
                    severity=AuditSeverity.INFO,
                    status=AuditStatus.UNKNOWN,
                    confidence=0.0,
                    description="Response time was not measured or unavailable (e.g. offline fixture evaluation).",
                    raw_metrics={"response_time_ms": None},
                )
            )

        # 6.2 HTML Payload Size
        if html_size_bytes > 500_000:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="performance",
                    issue_code="PERFORMANCE_LARGE_HTML_PAYLOAD",
                    severity=AuditSeverity.LOW,
                    status=AuditStatus.WARNING,
                    confidence=1.0,
                    description=f"HTML payload size ({html_size_bytes / 1024:.1f} KB) exceeds the recommended 500 KB ceiling.",
                    recommendation="Minify HTML markup, trim inline JSON blobs or base64 assets, and enable Brotli/Gzip compression.",
                    raw_metrics={"size_bytes": html_size_bytes},
                )
            )

        # 6.3 Render-blocking external scripts
        render_blocking = [s for s in scripts_list if s.get("is_render_blocking")]
        if len(render_blocking) > 5:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="performance",
                    issue_code="PERFORMANCE_MANY_RENDER_BLOCKING_SCRIPTS",
                    severity=AuditSeverity.LOW,
                    status=AuditStatus.WARNING,
                    confidence=0.9,
                    description=f"Page has {len(render_blocking)} synchronous render-blocking scripts in the initial document.",
                    recommendation="Add 'defer' or 'async' attributes to non-critical external scripts.",
                    patch='<script src="/path/to/script.js" defer></script>',
                    raw_metrics={"render_blocking_count": len(render_blocking)},
                )
            )

        # 6.4 Image Alt Attributes
        missing_alt = [img for img in images_list if not img.get("has_alt")]
        if missing_alt:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="performance",
                    issue_code="ACCESSIBILITY_IMAGES_MISSING_ALT",
                    severity=AuditSeverity.MEDIUM,
                    status=AuditStatus.WARNING,
                    confidence=1.0,
                    description=f"Found {len(missing_alt)} images lacking descriptive 'alt' attributes.",
                    recommendation="Add informative 'alt' text to every image to assist screen readers and image search crawlers.",
                    patch='<img src="b-roll-generator.webp" alt="Automated AI b-roll timeline generator interface" />',
                    raw_metrics={"missing_alt_count": len(missing_alt), "total_images": len(images_list)},
                )
            )
        elif images_list:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="performance",
                    issue_code="IMAGES_ALT_OPTIMAL",
                    severity=AuditSeverity.INFO,
                    status=AuditStatus.PASS,
                    confidence=1.0,
                    description=f"All {len(images_list)} images have descriptive 'alt' attributes.",
                    raw_metrics={"total_images": len(images_list)},
                )
            )

        return findings

    # -------------------------------------------------------------------------
    # 7. Structured Data (Schema.org JSON-LD)
    # -------------------------------------------------------------------------
    @staticmethod
    def audit_structured_data(
        target_url: str,
        json_ld_schemas: List[Dict[str, Any]],
        json_ld_errors: List[str],
    ) -> List[AuditFindingCreate]:
        """Audit Schema.org JSON-LD structured data presence, syntax validity, and entity clarity."""
        findings: List[AuditFindingCreate] = []

        if json_ld_errors:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="structured_data",
                    issue_code="INVALID_JSON_LD",
                    severity=AuditSeverity.HIGH,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description=f"Malformed JSON-LD detected: {json_ld_errors[0]}",
                    recommendation="Validate JSON-LD syntax using the Google Rich Results Test or Schema.org Validator.",
                    raw_metrics={"errors": json_ld_errors},
                )
            )
            return findings

        if not json_ld_schemas:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="structured_data",
                    issue_code="MISSING_STRUCTURED_DATA",
                    severity=AuditSeverity.HIGH,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description="No Schema.org JSON-LD structured data detected on the page.",
                    recommendation="Embed JSON-LD structured data (e.g. WebPage, TechArticle, FAQPage, Organization) for entity clarity.",
                    patch=(
                        '<script type="application/ld+json">\n'
                        '{\n'
                        '  "@context": "https://schema.org",\n'
                        '  "@type": "WebPage",\n'
                        '  "name": "Target Page Title",\n'
                        '  "description": "Page summary for entity disambiguation."\n'
                        '}\n'
                        '</script>'
                    ),
                    raw_metrics={"has_schema": False},
                )
            )
        else:
            types_detected = [s.get("@type", "Unknown") for s in json_ld_schemas]
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="structured_data",
                    issue_code="STRUCTURED_DATA_VALID",
                    severity=AuditSeverity.INFO,
                    status=AuditStatus.PASS,
                    confidence=1.0,
                    description=f"Valid Schema.org structured data found with @type: {', '.join(types_detected)}.",
                    raw_metrics={"schema_count": len(json_ld_schemas), "types": types_detected},
                )
            )

        return findings

    # -------------------------------------------------------------------------
    # 8. Robots.txt
    # -------------------------------------------------------------------------
    @staticmethod
    def audit_robots_rules(
        robots_txt_content: Optional[str],
        target_url: str,
    ) -> List[AuditFindingCreate]:
        """Audit robots.txt existence, search bot disallow rules, AI agent access, and sitemap directives."""
        findings: List[AuditFindingCreate] = []

        if not robots_txt_content or not robots_txt_content.strip():
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="robots_txt",
                    issue_code="MISSING_ROBOTS_TXT",
                    severity=AuditSeverity.HIGH,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description="No robots.txt file could be retrieved for the site.",
                    recommendation="Deploy a valid robots.txt file specifying permissions for standard search and AI crawlers.",
                    patch="User-agent: *\nAllow: /\n\nSitemap: https://incubrix.com/sitemap.xml",
                    raw_metrics={"has_robots_txt": False},
                )
            )
            return findings

        lower_content = robots_txt_content.lower()

        # 8.1 Search Bot Blanket Disallow
        if "user-agent: *" in lower_content and "disallow: /" in lower_content and "disallow: /" == lower_content.split("user-agent: *")[1].split("\n")[1].strip():
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="robots_txt",
                    issue_code="SEARCH_BOTS_DISALLOWED",
                    severity=AuditSeverity.CRITICAL,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description="Robots.txt contains blanket 'Disallow: /' for all user agents, completely blocking organic indexing.",
                    recommendation="Remove blanket Disallow: / directive from robots.txt.",
                    patch="User-agent: *\nAllow: /",
                    raw_metrics={"blanket_disallow": True},
                )
            )

        # 8.2 AI Bots Restricted Check
        ai_bots = ["gptbot", "claudebot", "perplexitybot", "google-extended"]
        blocked_bots = []
        for bot in ai_bots:
            if f"user-agent: {bot}" in lower_content:
                section = lower_content.split(f"user-agent: {bot}")[1].split("user-agent:")[0]
                if "disallow: /" in section:
                    blocked_bots.append(bot)

        if blocked_bots:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="robots_txt",
                    issue_code="AI_BOTS_RESTRICTED",
                    severity=AuditSeverity.MEDIUM,
                    status=AuditStatus.WARNING,
                    confidence=1.0,
                    description=f"AI web crawlers are explicitly disallowed in robots.txt: {', '.join(blocked_bots)}.",
                    recommendation="If AEO/GEO visibility is desired, permit indexation for approved AI user agents.",
                    patch=(
                        "# Permit modern AI search agents:\n"
                        "User-agent: GPTBot\nAllow: /\n"
                        "User-agent: PerplexityBot\nAllow: /\n"
                        "User-agent: ClaudeBot\nAllow: /\n"
                    ),
                    raw_metrics={"blocked_bots": blocked_bots},
                )
            )
        else:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="robots_txt",
                    issue_code="AI_BOTS_PERMITTED",
                    severity=AuditSeverity.INFO,
                    status=AuditStatus.PASS,
                    confidence=1.0,
                    description="Robots.txt exists and permits generative AI assistant crawlers.",
                    raw_metrics={"blocked_bots": []},
                )
            )

        # 8.3 Sitemap directive check
        if "sitemap:" not in lower_content:
            parsed = urlparse(target_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else "https://incubrix.com"
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="robots_txt",
                    issue_code="ROBOTS_MISSING_SITEMAP",
                    severity=AuditSeverity.LOW,
                    status=AuditStatus.WARNING,
                    confidence=0.9,
                    description="Robots.txt does not declare a 'Sitemap:' directive.",
                    recommendation="Add a Sitemap directive pointing to your primary XML sitemap URL.",
                    patch=f"Sitemap: {base_url}/sitemap.xml",
                    raw_metrics={"has_sitemap_directive": False},
                )
            )

        return findings

    # -------------------------------------------------------------------------
    # 9. Sitemap XML
    # -------------------------------------------------------------------------
    @staticmethod
    def audit_sitemap(
        sitemap_xml_content: Optional[str],
        target_url: str,
    ) -> List[AuditFindingCreate]:
        """Audit XML sitemap presence, XML syntax validity, and target URL inclusion."""
        findings: List[AuditFindingCreate] = []

        if not sitemap_xml_content or not sitemap_xml_content.strip():
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="sitemap",
                    issue_code="MISSING_SITEMAP",
                    severity=AuditSeverity.MEDIUM,
                    status=AuditStatus.WARNING,
                    confidence=0.9,
                    description="XML sitemap was not provided or could not be retrieved.",
                    recommendation="Publish an XML sitemap at /sitemap.xml to accelerate URL discovery by search engines.",
                    patch=(
                        '<?xml version="1.0" encoding="UTF-8"?>\n'
                        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                        f'  <url><loc>{target_url}</loc></url>\n'
                        '</urlset>'
                    ),
                    raw_metrics={"has_sitemap": False},
                )
            )
            return findings

        # Parse XML
        try:
            root = ET.fromstring(sitemap_xml_content)
            urls = []
            for elem in root.iter():
                if elem.tag.endswith("loc") and elem.text:
                    urls.append(elem.text.strip())

            contains_target = any(target_url.rstrip("/") == u.rstrip("/") for u in urls)
            if contains_target:
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="sitemap",
                        issue_code="SITEMAP_CONTAINS_URL",
                        severity=AuditSeverity.INFO,
                        status=AuditStatus.PASS,
                        confidence=1.0,
                        description=f"XML sitemap is valid and contains the target URL ({len(urls)} total URLs indexed).",
                        raw_metrics={"url_count": len(urls), "contains_target": True},
                    )
                )
            else:
                findings.append(
                    AuditFindingCreate(
                        target_url=target_url,
                        audit_category="sitemap",
                        issue_code="SITEMAP_VALID",
                        severity=AuditSeverity.INFO,
                        status=AuditStatus.PASS,
                        confidence=1.0,
                        description=f"XML sitemap is valid with {len(urls)} URLs listed.",
                        raw_metrics={"url_count": len(urls), "contains_target": False},
                    )
                )
        except ET.ParseError as err:
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="sitemap",
                    issue_code="INVALID_SITEMAP_XML",
                    severity=AuditSeverity.MEDIUM,
                    status=AuditStatus.FAIL,
                    confidence=1.0,
                    description=f"Sitemap XML parsing failed: {err}",
                    recommendation="Ensure the sitemap is well-formed XML conforming to the sitemaps.org schema.",
                    raw_metrics={"parse_error": str(err)},
                )
            )

        return findings

    # -------------------------------------------------------------------------
    # 10. Optional llms.txt Discovery Check
    # -------------------------------------------------------------------------
    @staticmethod
    def audit_llms_txt(
        llms_txt_content: Optional[str],
        target_url: str,
    ) -> List[AuditFindingCreate]:
        """Evaluate presence of /llms.txt.

        IMPORTANT: Treated as an optional discovery check, NOT a guaranteed ranking requirement.
        Severity is kept low/info and description emphasizes optional discovery nature.
        """
        findings: List[AuditFindingCreate] = []

        if not llms_txt_content or not llms_txt_content.strip():
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="llms_txt",
                    issue_code="OPTIONAL_LLMS_TXT_MISSING",
                    severity=AuditSeverity.INFO,
                    status=AuditStatus.WARNING,
                    confidence=0.85,
                    description=(
                        "Optional discovery file /llms.txt was not detected. "
                        "Note: llms.txt is an optional discovery standard for AI agents and LLMs, "
                        "not a guaranteed search engine ranking requirement."
                    ),
                    recommendation="Consider publishing an optional /llms.txt file to guide generative AI agents navigating site architecture.",
                    patch=(
                        "# IncuBrix Documentation\n\n"
                        "> Optional discovery manifest for LLM consumption\n\n"
                        "- [API Reference](/docs): Core endpoints\n"
                        "- [Architecture](/docs/architecture): System overview\n"
                    ),
                    raw_metrics={"present": False, "is_optional": True},
                )
            )
        else:
            has_title = llms_txt_content.strip().startswith("#")
            findings.append(
                AuditFindingCreate(
                    target_url=target_url,
                    audit_category="llms_txt",
                    issue_code="OPTIONAL_LLMS_TXT_PRESENT",
                    severity=AuditSeverity.INFO,
                    status=AuditStatus.PASS,
                    confidence=1.0,
                    description="The site provides an optional /llms.txt discovery manifest to assist LLM agents.",
                    recommendation="Keep links and brand descriptions synchronized in /llms.txt.",
                    raw_metrics={"present": True, "has_h1": has_title, "length": len(llms_txt_content), "is_optional": True},
                )
            )

        return findings

    # -------------------------------------------------------------------------
    # 11. Full Page Audit Orchestration & Health Score
    # -------------------------------------------------------------------------
    @classmethod
    def audit_page(
        cls,
        target_url: str,
        html_content: Optional[str] = None,
        status_code: Optional[int] = 200,
        headers: Optional[Dict[str, str]] = None,
        response_time_ms: Optional[float] = None,
        robots_txt_content: Optional[str] = None,
        sitemap_xml_content: Optional[str] = None,
        llms_txt_content: Optional[str] = None,
        allow_polite_fetch: bool = False,
    ) -> AuditReport:
        """Run all technical SEO, AEO, and GEO checks on a target page or offline fixture."""
        all_findings: List[AuditFindingCreate] = []

        # Polite live fetch if HTML is not provided and permitted
        if not html_content and allow_polite_fetch and target_url.startswith(("http://", "https://")):
            try:
                with httpx.Client(
                    timeout=5.0,
                    follow_redirects=True,
                    headers={"User-Agent": cls.USER_AGENT},
                ) as client:
                    resp = client.get(target_url)
                    html_content = resp.text
                    status_code = resp.status_code
                    headers = dict(resp.headers)
                    response_time_ms = resp.elapsed.total_seconds() * 1000.0
            except Exception as exc:
                logger.warning("Polite fetch failed for %s: %s", target_url, exc)
                status_code = 500
                html_content = ""

        # Parse DOM via HTMLPageInspector
        inspector = HTMLPageInspector.inspect(html_content or "", target_url=target_url)

        # 1. Indexability
        all_findings.extend(
            cls.audit_indexability(
                target_url=target_url,
                status_code=status_code,
                headers=headers,
                meta_robots=inspector.meta_robots,
            )
        )

        # 2. Metadata (Title & Description)
        all_findings.extend(
            cls.audit_metadata(
                target_url=target_url,
                title=inspector.title,
                description=inspector.meta_description,
            )
        )

        # 3. Headings
        all_findings.extend(
            cls.audit_headings(
                target_url=target_url,
                h1_tags=inspector.h1_tags,
                h2_tags=inspector.h2_tags,
                h3_tags=inspector.h3_tags,
            )
        )

        # 4. Canonical
        all_findings.extend(
            cls.audit_canonical(
                target_url=target_url,
                canonical_hrefs=inspector.canonical_hrefs,
            )
        )

        # 5. Internal Links
        all_findings.extend(
            cls.audit_internal_links(
                target_url=target_url,
                links=inspector.links,
            )
        )

        # 6. Performance
        all_findings.extend(
            cls.audit_performance(
                target_url=target_url,
                response_time_ms=response_time_ms,
                html_size_bytes=inspector.html_size_bytes,
                scripts=inspector.scripts,
                images=inspector.images,
            )
        )

        # 7. Structured Data
        all_findings.extend(
            cls.audit_structured_data(
                target_url=target_url,
                json_ld_schemas=inspector.json_ld_schemas,
                json_ld_errors=inspector.json_ld_errors,
            )
        )

        # 8. Robots.txt
        all_findings.extend(
            cls.audit_robots_rules(
                robots_txt_content=robots_txt_content,
                target_url=target_url,
            )
        )

        # 9. Sitemap XML
        all_findings.extend(
            cls.audit_sitemap(
                sitemap_xml_content=sitemap_xml_content,
                target_url=target_url,
            )
        )

        # 10. Optional llms.txt discovery
        all_findings.extend(
            cls.audit_llms_txt(
                llms_txt_content=llms_txt_content,
                target_url=target_url,
            )
        )

        # Tally counts & category breakdown
        passed = sum(1 for f in all_findings if f.status == AuditStatus.PASS)
        warning = sum(1 for f in all_findings if f.status == AuditStatus.WARNING)
        failed = sum(1 for f in all_findings if f.status == AuditStatus.FAIL)
        unknown = sum(1 for f in all_findings if f.status == AuditStatus.UNKNOWN)

        summary_by_category: Dict[str, Dict[str, int]] = {}
        for f in all_findings:
            cat = f.audit_category
            if cat not in summary_by_category:
                summary_by_category[cat] = {"pass": 0, "warning": 0, "fail": 0, "unknown": 0}
            summary_by_category[cat][f.status.value] += 1

        health_score = cls.calculate_health_score(all_findings)

        read_findings = [
            AuditFindingRead(
                target_url=f.target_url,
                audit_category=f.audit_category,
                issue_code=f.issue_code,
                severity=f.severity,
                status=f.status,
                confidence=f.confidence,
                description=f.description,
                recommendation=f.recommendation,
                patch=f.patch,
                validation_status=f.validation_status,
                raw_metrics=f.raw_metrics,
                evaluated_at=f.evaluated_at,
            )
            for f in all_findings
        ]

        return AuditReport(
            target_url=target_url,
            audited_at=datetime.now(timezone.utc).replace(tzinfo=None),
            total_findings=len(all_findings),
            passed_count=passed,
            warning_count=warning,
            failed_count=failed,
            unknown_count=unknown,
            health_score=health_score,
            findings=read_findings,
            summary_by_category=summary_by_category,
        )

    @staticmethod
    def calculate_health_score(findings: List[Any]) -> float:
        """Calculate weighted composite technical health score from 0.0 to 100.0."""
        score = 100.0
        for f in findings:
            status = f.status.value if hasattr(f.status, "value") else str(f.status)
            severity = f.severity.value if hasattr(f.severity, "value") else str(f.severity)

            if status == "fail":
                if severity == "critical":
                    score -= 35.0
                elif severity == "high":
                    score -= 18.0
                elif severity == "medium":
                    score -= 10.0
                elif severity == "low":
                    score -= 4.0
            elif status == "warning":
                if severity == "high":
                    score -= 8.0
                elif severity == "medium":
                    score -= 4.0
                elif severity == "low":
                    score -= 2.0
            elif status == "unknown":
                score -= 1.0

        return max(0.0, min(100.0, round(score, 1)))

    # -------------------------------------------------------------------------
    # 12. Strict Fix Validation
    # -------------------------------------------------------------------------
    @classmethod
    def validate_fix(
        cls,
        finding: Any,
        updated_html: Optional[str] = None,
        updated_content: Optional[str] = None,
        recheck_live: bool = False,
    ) -> FixValidationResponse:
        """Recheck and validate whether an audit finding defect has been remedied.

        Rule: Never claim a fix is validated without running an appropriate check.
        Mark unavailable checks explicitly.
        """
        finding_id = getattr(finding, "id", "unknown-id")
        target_url = getattr(finding, "target_url", "")
        issue_code = getattr(finding, "issue_code", "")

        # 1. Check if inspection payload is missing
        if updated_html is None and updated_content is None and not recheck_live:
            return FixValidationResponse(
                finding_id=finding_id,
                target_url=target_url,
                issue_code=issue_code,
                validation_status=ValidationStatus.UNAVAILABLE,
                is_resolved=False,
                explanation="Cannot validate fix: required inspection payload or network target was unavailable.",
            )

        # 2. Live polite recheck
        if recheck_live and not updated_html and target_url.startswith(("http://", "https://")):
            try:
                with httpx.Client(
                    timeout=5.0,
                    follow_redirects=True,
                    headers={"User-Agent": cls.USER_AGENT},
                ) as client:
                    resp = client.get(target_url)
                    updated_html = resp.text
            except Exception as exc:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.UNAVAILABLE,
                    is_resolved=False,
                    explanation=f"Cannot validate fix: live fetch to {target_url} failed ({exc}).",
                )

        # Parse updated HTML if available
        inspector = (
            HTMLPageInspector.inspect(updated_html, target_url=target_url)
            if updated_html is not None
            else None
        )

        # 3. Targeted check execution
        if issue_code in ("MISSING_TITLE", "TITLE_TOO_SHORT", "TITLE_TOO_LONG"):
            if inspector is None:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.UNAVAILABLE,
                    is_resolved=False,
                    explanation="Updated HTML markup required to validate title fix.",
                )
            results = cls.audit_metadata(target_url, title=inspector.title, description="dummy-ok-length-meta-description-to-pass")
            title_finding = next((r for r in results if r.issue_code in ("TITLE_OPTIMAL", issue_code)), None)
            if title_finding and title_finding.status == AuditStatus.PASS:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.VALIDATED,
                    is_resolved=True,
                    explanation="Fix validated: page title is now present and within optimal length bounds.",
                )
            return FixValidationResponse(
                finding_id=finding_id,
                target_url=target_url,
                issue_code=issue_code,
                validation_status=ValidationStatus.FAILED,
                is_resolved=False,
                explanation="Fix validation failed: title issue remains unresolved in the provided markup.",
            )

        elif issue_code in ("MISSING_META_DESCRIPTION", "META_DESCRIPTION_TOO_SHORT", "META_DESCRIPTION_TOO_LONG"):
            if inspector is None:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.UNAVAILABLE,
                    is_resolved=False,
                    explanation="Updated HTML markup required to validate meta description fix.",
                )
            results = cls.audit_metadata(target_url, title="Valid Page Title That Passes", description=inspector.meta_description)
            desc_finding = next((r for r in results if r.issue_code in ("META_DESCRIPTION_OPTIMAL", issue_code)), None)
            if desc_finding and desc_finding.status == AuditStatus.PASS:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.VALIDATED,
                    is_resolved=True,
                    explanation="Fix validated: meta description is now present and meets length criteria.",
                )
            return FixValidationResponse(
                finding_id=finding_id,
                target_url=target_url,
                issue_code=issue_code,
                validation_status=ValidationStatus.FAILED,
                is_resolved=False,
                explanation="Fix validation failed: meta description is still missing or sub-optimal.",
            )

        elif issue_code in ("MISSING_H1", "MULTIPLE_H1", "NO_H2_SUBHEADINGS"):
            if inspector is None:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.UNAVAILABLE,
                    is_resolved=False,
                    explanation="Updated HTML markup required to validate heading structure.",
                )
            results = cls.audit_headings(target_url, inspector.h1_tags, inspector.h2_tags, inspector.h3_tags)
            failed = any(r.status in (AuditStatus.FAIL, AuditStatus.WARNING) and r.issue_code == issue_code for r in results)
            if not failed:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.VALIDATED,
                    is_resolved=True,
                    explanation="Fix validated: heading outline satisfies topic structure requirements.",
                )
            return FixValidationResponse(
                finding_id=finding_id,
                target_url=target_url,
                issue_code=issue_code,
                validation_status=ValidationStatus.FAILED,
                is_resolved=False,
                explanation="Fix validation failed: heading defect remains in the markup.",
            )

        elif issue_code in ("MISSING_CANONICAL", "MULTIPLE_CANONICALS", "RELATIVE_CANONICAL"):
            if inspector is None:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.UNAVAILABLE,
                    is_resolved=False,
                    explanation="Updated HTML markup required to validate canonical link.",
                )
            results = cls.audit_canonical(target_url, inspector.canonical_hrefs)
            is_valid = any(r.issue_code == "CANONICAL_VALID" for r in results)
            if is_valid:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.VALIDATED,
                    is_resolved=True,
                    explanation="Fix validated: valid absolute canonical link tag confirmed.",
                )
            return FixValidationResponse(
                finding_id=finding_id,
                target_url=target_url,
                issue_code=issue_code,
                validation_status=ValidationStatus.FAILED,
                is_resolved=False,
                explanation="Fix validation failed: canonical tag is still missing, relative, or duplicated.",
            )

        elif issue_code in ("NOINDEX_DETECTED", "NOFOLLOW_DETECTED"):
            if inspector is None:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.UNAVAILABLE,
                    is_resolved=False,
                    explanation="Updated HTML markup required to validate meta robots directive.",
                )
            results = cls.audit_indexability(target_url, status_code=200, meta_robots=inspector.meta_robots)
            still_blocked = any(r.issue_code == issue_code for r in results)
            if not still_blocked:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.VALIDATED,
                    is_resolved=True,
                    explanation="Fix validated: blocking meta robots directive removed.",
                )
            return FixValidationResponse(
                finding_id=finding_id,
                target_url=target_url,
                issue_code=issue_code,
                validation_status=ValidationStatus.FAILED,
                is_resolved=False,
                explanation="Fix validation failed: blocking meta robots directive is still present.",
            )

        elif issue_code in ("MISSING_STRUCTURED_DATA", "INVALID_JSON_LD"):
            if inspector is None:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.UNAVAILABLE,
                    is_resolved=False,
                    explanation="Updated HTML markup required to validate structured data.",
                )
            results = cls.audit_structured_data(target_url, inspector.json_ld_schemas, inspector.json_ld_errors)
            is_valid = any(r.issue_code == "STRUCTURED_DATA_VALID" for r in results)
            if is_valid:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.VALIDATED,
                    is_resolved=True,
                    explanation="Fix validated: valid Schema.org JSON-LD structured data detected.",
                )
            return FixValidationResponse(
                finding_id=finding_id,
                target_url=target_url,
                issue_code=issue_code,
                validation_status=ValidationStatus.FAILED,
                is_resolved=False,
                explanation="Fix validation failed: structured data is still missing or contains syntax errors.",
            )

        elif issue_code in ("MISSING_ROBOTS_TXT", "AI_BOTS_RESTRICTED", "SEARCH_BOTS_DISALLOWED", "ROBOTS_MISSING_SITEMAP"):
            content = updated_content or updated_html
            if not content:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.UNAVAILABLE,
                    is_resolved=False,
                    explanation="Updated robots.txt content required to validate fix.",
                )
            results = cls.audit_robots_rules(content, target_url)
            still_defective = any(r.issue_code == issue_code for r in results)
            if not still_defective:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.VALIDATED,
                    is_resolved=True,
                    explanation="Fix validated: robots.txt rule updated successfully.",
                )
            return FixValidationResponse(
                finding_id=finding_id,
                target_url=target_url,
                issue_code=issue_code,
                validation_status=ValidationStatus.FAILED,
                is_resolved=False,
                explanation="Fix validation failed: robots.txt defect persists in the updated content.",
            )

        elif issue_code in ("MISSING_SITEMAP", "INVALID_SITEMAP_XML"):
            content = updated_content or updated_html
            if not content:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.UNAVAILABLE,
                    is_resolved=False,
                    explanation="Updated sitemap XML content required to validate fix.",
                )
            results = cls.audit_sitemap(content, target_url)
            still_defective = any(r.issue_code == issue_code for r in results)
            if not still_defective:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.VALIDATED,
                    is_resolved=True,
                    explanation="Fix validated: XML sitemap is now well-formed and valid.",
                )
            return FixValidationResponse(
                finding_id=finding_id,
                target_url=target_url,
                issue_code=issue_code,
                validation_status=ValidationStatus.FAILED,
                is_resolved=False,
                explanation="Fix validation failed: sitemap is still invalid or missing.",
            )

        elif issue_code == "ACCESSIBILITY_IMAGES_MISSING_ALT":
            if inspector is None:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.UNAVAILABLE,
                    is_resolved=False,
                    explanation="Updated HTML markup required to validate image alt attributes.",
                )
            missing = [img for img in inspector.images if not img.get("has_alt")]
            if not missing:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.VALIDATED,
                    is_resolved=True,
                    explanation="Fix validated: all images now possess descriptive alt attributes.",
                )
            return FixValidationResponse(
                finding_id=finding_id,
                target_url=target_url,
                issue_code=issue_code,
                validation_status=ValidationStatus.FAILED,
                is_resolved=False,
                explanation=f"Fix validation failed: {len(missing)} images still lack alt attributes.",
            )

        elif issue_code in ("EMPTY_OR_PLACEHOLDER_LINKS", "NON_DESCRIPTIVE_ANCHOR_TEXT"):
            if inspector is None:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.UNAVAILABLE,
                    is_resolved=False,
                    explanation="Updated HTML markup required to validate anchor links.",
                )
            results = cls.audit_internal_links(target_url, inspector.links)
            still_defective = any(r.issue_code == issue_code for r in results)
            if not still_defective:
                return FixValidationResponse(
                    finding_id=finding_id,
                    target_url=target_url,
                    issue_code=issue_code,
                    validation_status=ValidationStatus.VALIDATED,
                    is_resolved=True,
                    explanation="Fix validated: internal anchor links remediated.",
                )
            return FixValidationResponse(
                finding_id=finding_id,
                target_url=target_url,
                issue_code=issue_code,
                validation_status=ValidationStatus.FAILED,
                is_resolved=False,
                explanation="Fix validation failed: placeholder links or generic anchor texts still detected.",
            )

        return FixValidationResponse(
            finding_id=finding_id,
            target_url=target_url,
            issue_code=issue_code,
            validation_status=ValidationStatus.UNAVAILABLE,
            is_resolved=False,
            explanation=f"Issue code '{issue_code}' has no automated offline re-check handler.",
        )
