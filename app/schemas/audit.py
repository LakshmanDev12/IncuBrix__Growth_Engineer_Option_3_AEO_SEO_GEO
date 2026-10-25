"""Schemas for Technical SEO, AEO, and GEO Audit Findings."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import AuditSeverity, AuditStatus, ValidationStatus


def now_utc() -> datetime:
    """Return naive UTC datetime for cross-platform SQLite compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuditFindingBase(BaseModel):
    """Core fields for technical audit findings."""

    target_url: str = Field(
        ...,
        max_length=2000,
        description="Target URL or endpoint evaluated (e.g., https://incubrix.com/robots.txt).",
    )
    audit_category: str = Field(
        ...,
        max_length=100,
        description=(
            "Audit category (e.g. indexability, metadata, headings, canonical, "
            "robots_txt, sitemap, internal_links, performance, structured_data, llms_txt)."
        ),
    )
    issue_code: str = Field(
        ...,
        max_length=100,
        description="Unique code identifying the rule or check (e.g. NOINDEX_DETECTED).",
    )
    severity: AuditSeverity = Field(
        default=AuditSeverity.MEDIUM,
        description="Severity level of the finding.",
    )
    status: AuditStatus = Field(
        default=AuditStatus.UNKNOWN,
        description="Evaluation status (pass, fail, warning, unknown). Defaults to unknown.",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for this finding (0.0 to 1.0).",
    )
    description: str = Field(
        ...,
        max_length=2000,
        description="Summary of the finding or defect detected.",
    )
    recommendation: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Concrete architectural or technical recommendation to resolve the finding.",
    )
    patch: Optional[str] = Field(
        default=None,
        description="Concrete code or text patch suggestion to remediate the finding.",
    )
    validation_status: ValidationStatus = Field(
        default=ValidationStatus.UNVALIDATED,
        description="Remediation validation state (unvalidated, validated, failed, unavailable).",
    )
    raw_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Observed HTTP status codes, response headers, parsed schema fields, etc.",
    )


class AuditFindingCreate(AuditFindingBase):
    """Payload to create a technical audit finding."""

    evaluated_at: datetime = Field(default_factory=now_utc)


class AuditFindingRead(AuditFindingBase):
    """Serialized technical audit finding."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    evaluated_at: datetime = Field(default_factory=now_utc)
    created_at: datetime = Field(default_factory=now_utc)


class PageAuditRequest(BaseModel):
    """Request payload to trigger a technical SEO/AEO audit on a target page."""

    target_url: str = Field(
        ...,
        max_length=2000,
        description="Target public page URL to audit (e.g. https://incubrix.com/features).",
    )
    html_content: Optional[str] = Field(
        default=None,
        description="Optional pre-fetched raw HTML content for offline or test fixture auditing.",
    )
    status_code: Optional[int] = Field(
        default=200,
        description="HTTP status code (default 200 for offline fixtures).",
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional HTTP response headers (e.g. X-Robots-Tag, Content-Type).",
    )
    response_time_ms: Optional[float] = Field(
        default=None,
        description="Observed network response time in milliseconds.",
    )
    robots_txt_content: Optional[str] = Field(
        default=None,
        description="Optional robots.txt content for the site.",
    )
    sitemap_xml_content: Optional[str] = Field(
        default=None,
        description="Optional sitemap.xml content for the site.",
    )
    llms_txt_content: Optional[str] = Field(
        default=None,
        description="Optional llms.txt manifest content (evaluated as optional discovery check).",
    )
    store_findings: bool = Field(
        default=True,
        description="Whether to persist generated findings to the database repository.",
    )


class AuditReport(BaseModel):
    """Aggregated technical audit report for a page or domain."""

    model_config = ConfigDict(from_attributes=True)

    target_url: str
    audited_at: datetime = Field(default_factory=now_utc)
    total_findings: int
    passed_count: int
    warning_count: int
    failed_count: int
    unknown_count: int
    health_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Composite technical health score from 0.0 to 100.0.",
    )
    findings: List[AuditFindingRead]
    summary_by_category: Dict[str, Dict[str, int]] = Field(default_factory=dict)


class FixValidationRequest(BaseModel):
    """Request payload to recheck and validate a remediation for an audit finding."""

    updated_html: Optional[str] = Field(
        default=None,
        description="Updated HTML page markup to re-evaluate.",
    )
    updated_content: Optional[str] = Field(
        default=None,
        description="Updated auxiliary content (e.g. robots.txt, sitemap XML, llms.txt).",
    )
    recheck_live: bool = Field(
        default=False,
        description="Whether to re-fetch the target URL over the network (polite 1-page check).",
    )


class FixValidationResponse(BaseModel):
    """Result of rechecking and validating an audit finding fix."""

    finding_id: str
    target_url: str
    issue_code: str
    validation_status: ValidationStatus
    is_resolved: bool
    explanation: str
    validated_at: datetime = Field(default_factory=now_utc)
