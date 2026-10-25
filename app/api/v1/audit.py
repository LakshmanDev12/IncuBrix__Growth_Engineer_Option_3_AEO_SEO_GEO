"""API routes for Technical SEO/AEO Audit Findings and Validation."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_audit_repository
from app.audit.technical_audit import TechnicalAuditor
from app.database.repositories.audit_repo import AuditFindingRepository
from app.schemas.audit import (
    AuditFindingCreate,
    AuditFindingRead,
    AuditReport,
    FixValidationRequest,
    FixValidationResponse,
    PageAuditRequest,
)

router = APIRouter(prefix="/audit", tags=["Technical Audit"])


@router.post(
    "/run",
    response_model=AuditReport,
    status_code=status.HTTP_200_OK,
    summary="Run comprehensive technical SEO/AEO audit on a page",
)
def run_page_audit(
    request: PageAuditRequest,
    repo: AuditFindingRepository = Depends(get_audit_repository),
) -> AuditReport:
    """Execute complete technical SEO, AEO, and GEO inspection on a target page.

    Inspects indexability signals, title/description metadata, headings, canonical links,
    robots.txt, sitemaps, internal links, performance, and Schema.org structured data.
    Treats llms.txt as an optional discovery check, not a guaranteed ranking requirement.
    """
    report = TechnicalAuditor.audit_page(
        target_url=request.target_url,
        html_content=request.html_content,
        status_code=request.status_code,
        headers=request.headers,
        response_time_ms=request.response_time_ms,
        robots_txt_content=request.robots_txt_content,
        sitemap_xml_content=request.sitemap_xml_content,
        llms_txt_content=request.llms_txt_content,
        allow_polite_fetch=True,
    )

    if request.store_findings and report.findings:
        create_payloads = [
            AuditFindingCreate(
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
            for f in report.findings
        ]
        saved_entities = repo.record_batch(create_payloads)
        # Reflect assigned DB ids back into report findings
        report.findings = [AuditFindingRead.model_validate(e) for e in saved_entities]

    return report


@router.post(
    "/validate/{finding_id}",
    response_model=FixValidationResponse,
    summary="Recheck and validate an audit finding remediation",
)
def validate_finding_fix(
    finding_id: str,
    request: FixValidationRequest,
    repo: AuditFindingRepository = Depends(get_audit_repository),
) -> FixValidationResponse:
    """Validate whether an audit defect has been resolved.

    Rule: Never claims a fix is validated without running an appropriate check.
    Marks unavailable checks explicitly. Updates repository validation status.
    """
    finding = repo.get_by_id(finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit finding '{finding_id}' not found.",
        )

    result = TechnicalAuditor.validate_fix(
        finding=finding,
        updated_html=request.updated_html,
        updated_content=request.updated_content,
        recheck_live=request.recheck_live,
    )

    # Persist updated status
    repo.update_validation_status(
        finding_id=finding_id,
        validation_status=result.validation_status.value,
        notes=result.explanation,
    )

    return result


@router.post(
    "/findings",
    response_model=AuditFindingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a single technical audit finding",
)
def record_audit_finding(
    data: AuditFindingCreate,
    repo: AuditFindingRepository = Depends(get_audit_repository),
) -> AuditFindingRead:
    """Store an automated or manual technical audit evaluation."""
    return repo.record_finding(data)


@router.get(
    "/findings",
    response_model=List[AuditFindingRead],
    summary="List and filter technical audit findings",
)
def list_audit_findings(
    category: Optional[str] = Query(None, description="Filter by category (e.g. indexability, metadata, canonical)"),
    url: Optional[str] = Query(None, description="Filter by target URL"),
    severity: Optional[str] = Query(None, description="Filter by severity (critical, high, medium, low, info)"),
    status_val: Optional[str] = Query(None, alias="status", description="Filter by status (pass, fail, warning, unknown)"),
    validation_status: Optional[str] = Query(None, description="Filter by validation status (unvalidated, validated, failed, unavailable)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: AuditFindingRepository = Depends(get_audit_repository),
) -> List[AuditFindingRead]:
    """Retrieve audit findings with multi-attribute filtering."""
    entities = repo.filter_findings(
        target_url=url,
        category=category,
        severity=severity,
        status_val=status_val,
        validation_status=validation_status,
        skip=skip,
        limit=limit,
    )
    return [AuditFindingRead.model_validate(e) for e in entities]


@router.get(
    "/findings/{finding_id}",
    response_model=AuditFindingRead,
    summary="Get single technical audit finding by ID",
)
def get_audit_finding(
    finding_id: str,
    repo: AuditFindingRepository = Depends(get_audit_repository),
) -> AuditFindingRead:
    """Retrieve a single audit finding by ID."""
    finding = repo.get_by_id(finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit finding '{finding_id}' not found.",
        )
    return AuditFindingRead.model_validate(finding)


@router.get(
    "/summary",
    summary="Get aggregated summary of audit findings",
)
def get_audit_summary(
    url: Optional[str] = Query(None, description="Filter summary by target URL"),
    repo: AuditFindingRepository = Depends(get_audit_repository),
) -> Dict[str, Any]:
    """Retrieve high-level audit findings statistics and validation statuses."""
    findings = repo.list_by_url(url) if url else repo.list(skip=0, limit=1000)

    total = len(findings)
    status_counts = {"pass": 0, "fail": 0, "warning": 0, "unknown": 0}
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    validation_counts = {"unvalidated": 0, "validated": 0, "failed": 0, "unavailable": 0}

    for f in findings:
        st = f.status.lower() if hasattr(f, "status") else "unknown"
        sev = f.severity.lower() if hasattr(f, "severity") else "info"
        val = f.validation_status.lower() if hasattr(f, "validation_status") else "unvalidated"

        if st in status_counts:
            status_counts[st] += 1
        if sev in severity_counts:
            severity_counts[sev] += 1
        if val in validation_counts:
            validation_counts[val] += 1

    return {
        "target_url": url,
        "total_findings": total,
        "status_distribution": status_counts,
        "severity_distribution": severity_counts,
        "validation_distribution": validation_counts,
    }
