"""API routes for Report Generation and CSV Data Exports."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.engine.report_generator import ReportGenerator
from app.schemas.reports import WeeklyReportResponse

router = APIRouter(prefix="/reports", tags=["Reports & Exports Engine"])


@router.get(
    "/export/visibility.csv",
    summary="Export visibility observations as RFC 4180 CSV",
    response_class=Response,
)
def export_visibility_csv(
    market: Optional[str] = Query(None, description="Filter by market (e.g. US)"),
    provider: Optional[str] = Query(None, description="Filter by provider (e.g. google_search, perplexity)"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    db: Session = Depends(get_db),
) -> Response:
    """Export all matching visibility observations with explicit provenance mode (real, manual, mocked, unavailable)."""
    csv_content = ReportGenerator.export_visibility_csv(
        session=db,
        market=market,
        provider=provider,
        start_date=start_date,
        end_date=end_date,
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=visibility.csv"},
    )


@router.get(
    "/export/technical_fixes.csv",
    summary="Export technical audit findings as RFC 4180 CSV",
    response_class=Response,
)
def export_technical_fixes_csv(
    url: Optional[str] = Query(None, description="Filter by target URL"),
    status_val: Optional[str] = Query(None, alias="status", description="Filter by status (fail, warning, pass)"),
    db: Session = Depends(get_db),
) -> Response:
    """Export technical audit findings with recommendations and code/text patches."""
    csv_content = ReportGenerator.export_technical_fixes_csv(
        session=db,
        url=url,
        status_val=status_val,
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=technical_fixes.csv"},
    )


@router.get(
    "/export/citation_targets.csv",
    summary="Export citation target opportunities as RFC 4180 CSV",
    response_class=Response,
)
def export_citation_targets_csv(
    domain: Optional[str] = Query(None, description="Filter by target domain"),
    gap_type: Optional[str] = Query(None, description="Filter by gap type"),
    db: Session = Depends(get_db),
) -> Response:
    """Export 30-target citation opportunities with relevance and legitimate pitch angles."""
    csv_content = ReportGenerator.export_citation_targets_csv(
        session=db,
        domain=domain,
        gap_type=gap_type,
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=citation_targets.csv"},
    )


@router.get(
    "/export/weekly_report.md",
    summary="Download executive weekly visibility report as Markdown",
    response_class=Response,
)
def export_weekly_report_md(
    db: Session = Depends(get_db),
) -> Response:
    """Download executive weekly report as markdown file."""
    report = ReportGenerator.generate_weekly_report(session=db, save_to_disk=True)
    return Response(
        content=report.markdown_content,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=weekly_report.md"},
    )


@router.get(
    "/weekly",
    response_model=WeeklyReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate executive weekly visibility report",
)
def generate_weekly_report(
    start_date: Optional[datetime] = Query(None, description="Reporting window start date"),
    end_date: Optional[datetime] = Query(None, description="Reporting window end date"),
    save_to_disk: bool = Query(True, description="Whether to persist report to outputs/reports/"),
    db: Session = Depends(get_db),
) -> WeeklyReportResponse:
    """Synthesize weekly executive report with provenance breakdown, SEO/GEO KPIs, and audit postures."""
    return ReportGenerator.generate_weekly_report(
        session=db,
        start_date=start_date,
        end_date=end_date,
        save_to_disk=save_to_disk,
    )
