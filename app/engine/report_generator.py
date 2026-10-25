"""Report Generator and Data Exporter for IncuBrix Visibility Engine.

Provides:
- CSV exports for visibility.csv, technical_fixes.csv, and citation_targets.csv.
- Weekly executive intelligence reports in Markdown and structured JSON.
- Explicit classification of observation provenance: 'real', 'manual', 'mocked', 'unavailable'.
- Comprehensive empty-state handling without crashing on zero-record states.
- Saving generated reports to disk under outputs/reports/.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import PROJECT_ROOT
from app.database.models.audit import AuditFindingModel
from app.database.models.citation import CitationTargetModel
from app.database.models.content import GeneratedPageModel
from app.database.models.observation import ObservationModel
from app.database.models.question import QuestionModel
from app.engine.visibility_metrics import VisibilityMetricsCalculator
from app.logging_config import get_logger
from app.schemas.reports import ProvenanceBreakdown, WeeklyReportResponse

logger = get_logger("incubrix.reports")


class ReportGenerator:
    """Production report generation and data export engine."""

    REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"

    @classmethod
    def ensure_reports_directory(cls) -> Path:
        """Ensure outputs/reports directory exists."""
        cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        return cls.REPORTS_DIR

    @staticmethod
    def determine_provenance_mode(obs: Any) -> str:
        """Categorize an observation into an explicit provenance mode.

        Returns one of: 'real', 'manual', 'mocked', or 'unavailable'.
        """
        status = getattr(obs, "collection_status", "")
        if hasattr(status, "value"):
            status = status.value
        status = str(status).lower()

        if status in ("unavailable", "failed", "pending"):
            return "unavailable"

        meta = getattr(obs, "meta", None)
        if not isinstance(meta, dict):
            meta = {}
        raw_answer = str(getattr(obs, "raw_answer", "") or "")

        # 1. Mocked / Synthetic test fixture
        if (
            meta.get("is_synthetic_test_fixture")
            or meta.get("is_mock")
            or "TEST DATA" in raw_answer
            or "Synthetic" in raw_answer
        ):
            return "mocked"

        # 2. Manual evidence or assistant transcript import
        if (
            meta.get("is_manual_evidence")
            or meta.get("imported_by")
            or meta.get("operator_id")
            or meta.get("is_geo_manual_import")
            or "manual" in str(getattr(obs, "provider", "")).lower()
        ):
            return "manual"

        # 3. Real live automated collection
        return "real"

    @classmethod
    def export_visibility_csv(
        cls,
        session: Session,
        market: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """Export all matching observations to RFC 4180 visibility.csv."""
        stmt = (
            select(ObservationModel, QuestionModel.text.label("question_text"))
            .outerjoin(QuestionModel, ObservationModel.question_id == QuestionModel.id)
            .order_by(ObservationModel.measured_at.desc())
        )

        if market:
            stmt = stmt.where(ObservationModel.market == market)
        if provider:
            stmt = stmt.where(ObservationModel.provider == provider)
        if start_date:
            stmt = stmt.where(ObservationModel.measured_at >= start_date)
        if end_date:
            stmt = stmt.where(ObservationModel.measured_at <= end_date)

        rows = session.execute(stmt).all()

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")

        headers = [
            "observation_id",
            "question_id",
            "question_text",
            "market",
            "location",
            "provider",
            "observation_type",
            "measured_at",
            "incubrix_mentioned",
            "incubrix_cited",
            "rank_position",
            "answer_box_present",
            "visibility_score",
            "provenance_mode",
            "collection_status",
            "competitors_observed",
            "quoted_domains",
        ]
        writer.writerow(headers)

        for obs, q_text in rows:
            prov_mode = cls.determine_provenance_mode(obs)
            competitors_str = ";".join(obs.competitors_observed or [])
            domains_str = ";".join(obs.quoted_domains or [])
            writer.writerow([
                obs.id,
                obs.question_id,
                q_text or "",
                obs.market,
                obs.location or "",
                obs.provider,
                obs.observation_type,
                obs.measured_at.isoformat() if obs.measured_at else "",
                obs.incubrix_mentioned,
                obs.incubrix_cited,
                obs.rank_position if obs.rank_position is not None else "",
                obs.answer_box_present if obs.answer_box_present is not None else "",
                obs.visibility_score if obs.visibility_score is not None else "",
                prov_mode,
                obs.collection_status,
                competitors_str,
                domains_str,
            ])

        return output.getvalue()

    @classmethod
    def export_technical_fixes_csv(
        cls,
        session: Session,
        url: Optional[str] = None,
        status_val: Optional[str] = None,
    ) -> str:
        """Export technical audit findings to RFC 4180 technical_fixes.csv."""
        stmt = select(AuditFindingModel).order_by(AuditFindingModel.evaluated_at.desc())
        if url:
            stmt = stmt.where(AuditFindingModel.target_url == url)
        if status_val:
            stmt = stmt.where(AuditFindingModel.status == status_val)

        findings = list(session.execute(stmt).scalars().all())

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")

        headers = [
            "finding_id",
            "target_url",
            "audit_category",
            "issue_code",
            "severity",
            "status",
            "validation_status",
            "confidence",
            "description",
            "recommendation",
            "code_patch",
            "evaluated_at",
        ]
        writer.writerow(headers)

        for f in findings:
            writer.writerow([
                f.id,
                f.target_url,
                f.audit_category,
                f.issue_code,
                f.severity,
                f.status,
                f.validation_status,
                f.confidence,
                f.description,
                f.recommendation or "",
                f.patch or "",
                f.evaluated_at.isoformat() if f.evaluated_at else "",
            ])

        return output.getvalue()

    @classmethod
    def export_citation_targets_csv(
        cls,
        session: Session,
        domain: Optional[str] = None,
        gap_type: Optional[str] = None,
    ) -> str:
        """Export citation opportunities to RFC 4180 citation_targets.csv."""
        stmt = select(CitationTargetModel).order_by(CitationTargetModel.created_at.desc())
        if domain:
            stmt = stmt.where(CitationTargetModel.target_domain == domain.lower().strip())
        if gap_type:
            stmt = stmt.where(CitationTargetModel.gap_type == gap_type)

        targets = list(session.execute(stmt).scalars().all())

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")

        headers = [
            "target_id",
            "target_domain",
            "target_url",
            "competitor_domain",
            "gap_type",
            "authority_score",
            "outreach_status",
            "relevance",
            "pitch_angle",
            "notes",
            "created_at",
        ]
        writer.writerow(headers)

        for t in targets:
            writer.writerow([
                t.id,
                t.target_domain,
                t.target_url or "",
                t.competitor_domain or "",
                t.gap_type,
                t.authority_score if t.authority_score is not None else "",
                t.outreach_status,
                t.relevance or "",
                t.pitch_angle or "",
                t.notes or "",
                t.created_at.isoformat() if t.created_at else "",
            ])

        return output.getvalue()

    @classmethod
    def generate_weekly_report(
        cls,
        session: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        save_to_disk: bool = True,
    ) -> WeeklyReportResponse:
        """Synthesize a structured weekly intelligence report across all stored engine records."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        start = start_date or (now - timedelta(days=7))
        end = end_date or now

        # 1. Fetch Observations within reporting window
        obs_stmt = (
            select(ObservationModel)
            .where(ObservationModel.measured_at >= start)
            .where(ObservationModel.measured_at <= end)
            .order_by(ObservationModel.measured_at.desc())
        )
        observations = list(session.execute(obs_stmt).scalars().all())

        # If zero observations in window, fallback to all observations to provide data if window was empty
        if not observations:
            all_obs = list(session.execute(select(ObservationModel)).scalars().all())
            if all_obs:
                observations = all_obs

        # 2. Tally Provenance Breakdown
        real_count = 0
        manual_count = 0
        mocked_count = 0
        unavail_count = 0

        for o in observations:
            mode = cls.determine_provenance_mode(o)
            if mode == "real":
                real_count += 1
            elif mode == "manual":
                manual_count += 1
            elif mode == "mocked":
                mocked_count += 1
            else:
                unavail_count += 1

        prov_breakdown = ProvenanceBreakdown(
            real=real_count,
            manual=manual_count,
            mocked=mocked_count,
            unavailable=unavail_count,
        )

        # 3. Calculate Visibility Metrics via VisibilityMetricsCalculator
        metrics_report = VisibilityMetricsCalculator.calculate_metrics(
            observations=observations,
            deduplicate=True,
        )

        # 4. Fetch Technical Audit Summary
        audit_stmt = select(AuditFindingModel)
        audit_findings = list(session.execute(audit_stmt).scalars().all())
        audit_critical_count = sum(1 for f in audit_findings if f.severity == "critical" and f.status == "fail")
        audit_high_count = sum(1 for f in audit_findings if f.severity == "high" and f.status == "fail")
        audit_validated_count = sum(1 for f in audit_findings if f.validation_status == "validated")
        audit_unvalidated_count = sum(1 for f in audit_findings if f.validation_status == "unvalidated")

        # 5. Fetch Content Drafts Summary
        pages_stmt = select(GeneratedPageModel)
        pages = list(session.execute(pages_stmt).scalars().all())
        pages_unreviewed = sum(1 for p in pages if p.publication_status == "unreviewed")
        pages_approved = sum(1 for p in pages if p.publication_status in ("approved", "published"))

        # 6. Fetch Citation Targets Summary
        cite_stmt = select(CitationTargetModel)
        citation_targets = list(session.execute(cite_stmt).scalars().all())
        top_targets = [t for t in citation_targets if (t.authority_score or 0) >= 90][:5]

        # 7. Construct Formatted Markdown Executive Document
        md_lines = [
            "# IncuBrix Visibility Engine — Weekly Executive Intelligence Report",
            "",
            f"**Reporting Window**: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}  ",
            f"**Generated At**: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            "",
            "---",
            "",
            "## 1. Executive Summary & Visibility KPIs",
            "",
        ]

        if not observations:
            md_lines.extend([
                "> **Notice: Empty State Detected**  ",
                "> No observations have been recorded yet. Connect automated providers or import manual evidence to populate visibility telemetry.",
                "",
            ])
        else:
            avg_score_str = f"{metrics_report.average_visibility_score:.1f}" if metrics_report.average_visibility_score is not None else "N/A"
            md_lines.extend([
                f"- **Total Evaluated Observations**: {metrics_report.valid_evaluated_observations} records",
                f"- **Mean Visibility Score**: **{avg_score_str} / 100**",
                f"- **Top-10 Organic Ranking Rate**: **{metrics_report.seo_metrics.top_10_ranking_rate_pct:.1f}%** (Top-3: {metrics_report.seo_metrics.top_3_ranking_rate_pct:.1f}%)",
                f"- **AI Assistant Brand Mention Rate**: **{metrics_report.geo_metrics.ai_mention_rate_pct:.1f}%**",
                f"- **AI Direct Website Citation Rate**: **{metrics_report.geo_metrics.ai_citation_rate_pct:.1f}%**",
                f"- **Answer-Feature Presence Rate**: **{metrics_report.answer_features.feature_presence_rate_pct:.1f}%**",
                "",
            ])

        # Section 2: Provenance Breakdown
        md_lines.extend([
            "## 2. Observation Provenance & Empirical Reliability",
            "",
            "To prevent synthetic simulations from contaminating real visibility decisions, observations are categorized by provenance:",
            "",
            f"| Provenance Mode | Record Count | Description |",
            f"| :--- | :--- | :--- |",
            f"| **Real (Automated Live)** | `{prov_breakdown.real}` | Direct live queries to configured Google Search / AI APIs |",
            f"| **Manual (Operator Import)** | `{prov_breakdown.manual}` | Human-verified assistant transcripts and evidence snapshots |",
            f"| **Mocked (Test Fixtures)** | `{prov_breakdown.mocked}` | Synthetic test data labeled for schema and unit validation |",
            f"| **Unavailable / Failed** | `{prov_breakdown.unavailable}` | Unconfigured providers or unmeasured network queries |",
            "",
        ])

        # Section 3: Observed Competitors
        if metrics_report.geo_metrics.observed_competitors:
            comp_list = ", ".join(metrics_report.geo_metrics.observed_competitors[:8])
            md_lines.extend([
                "## 3. Competitive Landscape in Generative Answers",
                "",
                f"Competitors frequently recommended by AI answer engines for target queries: **{comp_list}**.",
                "",
            ])

        # Section 4: Technical SEO & AEO Health
        md_lines.extend([
            "## 4. Technical SEO, AEO & Crawlability Posture",
            "",
            f"- **Total Audit Findings**: {len(audit_findings)} evaluated checks",
            f"- **Critical Blocking Defects**: {audit_critical_count} issues",
            f"- **High Severity Issues**: {audit_high_count} issues",
            f"- **Remediation Status**: {audit_validated_count} verified fixes | {audit_unvalidated_count} awaiting validation",
            "",
        ])

        # Section 5: Content Engine Output
        md_lines.extend([
            "## 5. Content Engine & Publishing Status",
            "",
            f"- **Generated AEO Page Drafts**: {len(pages)} pages",
            f"- **Unreviewed Drafts Awaiting Curation**: {pages_unreviewed} drafts",
            f"- **Approved / Published Pages**: {pages_approved} pages",
            "",
        ])

        # Section 6: Priority Citation Opportunities
        md_lines.extend([
            "## 6. Priority Citation Targets for Acquisition",
            "",
            f"A total of **{len(citation_targets)}** citation opportunities are tracked in the database. High-priority targets with DA >= 90:",
            "",
        ])
        if top_targets:
            for t in top_targets:
                md_lines.append(f"- **{t.target_domain}** (Authority: {t.authority_score}): *{t.pitch_angle or t.relevance}*")
        else:
            md_lines.append("- *No citation targets above DA 90 currently logged.*")
        md_lines.append("")

        md_content = "\n".join(md_lines)

        report_response = WeeklyReportResponse(
            report_title="IncuBrix Weekly Visibility & Intelligence Report",
            generated_at=now,
            reporting_window_start=start,
            reporting_window_end=end,
            total_observations=len(observations),
            provenance_breakdown=prov_breakdown,
            average_visibility_score=metrics_report.average_visibility_score,
            top_10_ranking_rate_pct=metrics_report.seo_metrics.top_10_ranking_rate_pct,
            ai_mention_rate_pct=metrics_report.geo_metrics.ai_mention_rate_pct,
            ai_citation_rate_pct=metrics_report.geo_metrics.ai_citation_rate_pct,
            seo_summary=metrics_report.seo_metrics.model_dump(),
            geo_summary=metrics_report.geo_metrics.model_dump(),
            audit_summary={
                "total_findings": len(audit_findings),
                "critical_defects": audit_critical_count,
                "high_issues": audit_high_count,
                "validated": audit_validated_count,
                "unvalidated": audit_unvalidated_count,
            },
            content_summary={
                "total_drafts": len(pages),
                "unreviewed": pages_unreviewed,
                "approved": pages_approved,
            },
            citation_summary={
                "total_targets": len(citation_targets),
                "top_priority_targets_count": len(top_targets),
            },
            markdown_content=md_content,
        )

        # 8. Save to disk under outputs/reports/ if requested
        if save_to_disk:
            try:
                reports_dir = cls.ensure_reports_directory()
                ts_str = now.strftime("%Y%m%d_%H%M%S")
                md_path = reports_dir / f"weekly_report_{ts_str}.md"
                json_path = reports_dir / f"weekly_report_{ts_str}.json"

                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(report_response.model_dump(mode="json"), f, indent=2)

                logger.info("Saved weekly report to %s and %s", md_path, json_path)
            except Exception as exc:
                logger.warning("Could not persist report to disk: %s", exc)

        return report_response
