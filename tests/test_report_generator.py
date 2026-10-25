"""Unit and integration tests for Module 8: Report Generator, CSV Exporters, and Dashboard API.

Verifies:
- Provenance mode classification ('real', 'manual', 'mocked', 'unavailable').
- Visibility CSV export with provenance, joined questions, and empty state handling.
- Technical fixes CSV export with code patches and severity filtering.
- Citation targets CSV export with authority scores, pitch angles, and gap types.
- Weekly executive intelligence report synthesis (Markdown & structured JSON).
- Empty-state resilience across all exporters and reports.
- FastAPI endpoints for CSV downloads and weekly report generation.
"""

import csv
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models.observation import ObservationModel
from app.database.repositories.audit_repo import AuditFindingRepository
from app.database.repositories.citation_repo import CitationRepository
from app.database.repositories.content_repo import ContentRepository
from app.database.repositories.observation_repo import ObservationRepository
from app.database.repositories.question_repo import QuestionRepository
from app.engine.report_generator import ReportGenerator
from app.schemas.audit import AuditFindingCreate
from app.schemas.citation import CitationTargetCreate
from app.schemas.common import (
    AuditSeverity,
    AuditStatus,
    CitationStatus,
    CollectionStatus,
    MentionStatus,
    ObservationType,
    ProviderType,
    ValidationStatus,
)
from app.schemas.content import ContentBriefCreate, GeneratedPageCreate
from app.schemas.observations import ObservationCreate
from app.schemas.questions import QuestionCreate
from app.schemas.reports import WeeklyReportResponse


# ==============================================================================
# 1. Provenance Mode Classification Tests
# ==============================================================================


def test_determine_provenance_mode_real():
    """Verify live automated observations are classified as 'real'."""
    obs = ObservationModel(
        question_id="q1",
        market="US",
        provider="google_search",
        observation_type="search_engine",
        collection_status="success",
        meta={},
    )
    assert ReportGenerator.determine_provenance_mode(obs) == "real"

    obs_perplexity = ObservationModel(
        question_id="q1",
        market="US",
        provider="perplexity",
        observation_type="ai_assistant",
        collection_status="success",
        meta={"temperature": 0.2},
    )
    assert ReportGenerator.determine_provenance_mode(obs_perplexity) == "real"


def test_determine_provenance_mode_manual():
    """Verify manual evidence and operator transcript imports are classified as 'manual'."""
    obs1 = ObservationModel(
        question_id="q1",
        market="US",
        provider="manual_search",
        collection_status="success",
        meta={"is_manual_evidence": True},
    )
    assert ReportGenerator.determine_provenance_mode(obs1) == "manual"

    obs2 = ObservationModel(
        question_id="q1",
        market="US",
        provider="chatgpt",
        collection_status="success",
        meta={"imported_by": "analyst-vklak"},
    )
    assert ReportGenerator.determine_provenance_mode(obs2) == "manual"

    obs3 = ObservationModel(
        question_id="q1",
        market="US",
        provider="claude",
        collection_status="success",
        meta={"operator_id": "op-99"},
    )
    assert ReportGenerator.determine_provenance_mode(obs3) == "manual"

    obs4 = ObservationModel(
        question_id="q1",
        market="US",
        provider="manual_importer",
        collection_status="success",
        meta={},
    )
    assert ReportGenerator.determine_provenance_mode(obs4) == "manual"


def test_determine_provenance_mode_mocked():
    """Verify synthetic fixtures and mock responses are classified as 'mocked'."""
    obs1 = ObservationModel(
        question_id="q1",
        market="US",
        provider="google_search",
        collection_status="success",
        meta={"is_synthetic_test_fixture": True},
    )
    assert ReportGenerator.determine_provenance_mode(obs1) == "mocked"

    obs2 = ObservationModel(
        question_id="q1",
        market="US",
        provider="perplexity",
        collection_status="success",
        meta={"is_mock": True},
    )
    assert ReportGenerator.determine_provenance_mode(obs2) == "mocked"

    obs3 = ObservationModel(
        question_id="q1",
        market="US",
        provider="gemini",
        collection_status="success",
        raw_answer="[TEST DATA] Synthetic generative response for testing",
    )
    assert ReportGenerator.determine_provenance_mode(obs3) == "mocked"


def test_determine_provenance_mode_unavailable():
    """Verify unavailable, failed, or pending observations are classified as 'unavailable'."""
    obs_fail = ObservationModel(
        question_id="q1",
        market="US",
        provider="google_search",
        collection_status="failed",
    )
    assert ReportGenerator.determine_provenance_mode(obs_fail) == "unavailable"

    obs_unavail = ObservationModel(
        question_id="q1",
        market="US",
        provider="deepseek",
        collection_status="unavailable",
    )
    assert ReportGenerator.determine_provenance_mode(obs_unavail) == "unavailable"

    obs_pending = ObservationModel(
        question_id="q1",
        market="US",
        provider="openai",
        collection_status=CollectionStatus.PENDING,
    )
    assert ReportGenerator.determine_provenance_mode(obs_pending) == "unavailable"


# ==============================================================================
# 2. Visibility CSV Export Tests
# ==============================================================================


def test_export_visibility_csv_empty(db_session: Session):
    """Empty state returns valid RFC 4180 header without error."""
    csv_str = ReportGenerator.export_visibility_csv(session=db_session)
    reader = list(csv.reader(io.StringIO(csv_str)))
    assert len(reader) == 1  # Only headers
    headers = reader[0]
    assert "observation_id" in headers
    assert "provenance_mode" in headers
    assert "question_text" in headers
    assert "visibility_score" in headers


def test_export_visibility_csv_populated_and_filters(db_session: Session):
    """Verify visibility CSV export includes question joins, provenance modes, and filters."""
    # Seed a question
    q_repo = QuestionRepository(db_session)
    q = q_repo.create_strict(QuestionCreate(
        text="How do creators optimize visibility?",
        target_audience="Creators",
        creator_intent="AEO Optimization",
    ))

    obs_repo = ObservationRepository(db_session)
    now = datetime.now(timezone.utc)

    # 1. Real US Google
    obs_repo.record_observation(
        ObservationCreate(
            question_id=q.id,
            market="US",
            provider=ProviderType.GOOGLE_SEARCH,
            observation_type=ObservationType.SEARCH_ENGINE,
            collection_status=CollectionStatus.SUCCESS,
            rank_position=2,
            answer_box_present=True,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.CITED,
            measured_at=now,
            competitors_observed=["Kajabi", "Teachable"],
            quoted_domains=["incubrix.com"],
            meta={"raw_provider": "google"},
        ),
        visibility_score=85,
    )

    # 2. Manual UK Perplexity
    obs_repo.record_observation(
        ObservationCreate(
            question_id=q.id,
            market="UK",
            provider=ProviderType.PERPLEXITY,
            observation_type=ObservationType.AI_ASSISTANT,
            collection_status=CollectionStatus.SUCCESS,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.NOT_CITED,
            measured_at=now - timedelta(days=2),
            meta={"is_manual_evidence": True, "operator_id": "op-1"},
        ),
        visibility_score=40,
    )

    # 3. Mocked US Gemini
    obs_repo.record_observation(
        ObservationCreate(
            question_id=q.id,
            market="US",
            provider=ProviderType.GEMINI,
            observation_type=ObservationType.AI_ASSISTANT,
            collection_status=CollectionStatus.SUCCESS,
            measured_at=now - timedelta(days=5),
            raw_answer="[TEST DATA] Synthetic output",
            meta={"is_synthetic_test_fixture": True},
        ),
        visibility_score=20,
    )

    # 4. Failed Bing US
    obs_repo.record_observation(
        ObservationCreate(
            question_id=q.id,
            market="US",
            provider=ProviderType.BING_COPILOT,
            observation_type=ObservationType.SEARCH_ENGINE,
            collection_status=CollectionStatus.FAILED,
            measured_at=now - timedelta(days=10),
        ),
        visibility_score=None,
    )

    # Export all
    csv_str = ReportGenerator.export_visibility_csv(session=db_session)
    reader = list(csv.reader(io.StringIO(csv_str)))
    assert len(reader) == 5  # 1 header + 4 rows

    prov_modes = [row[reader[0].index("provenance_mode")] for row in reader[1:]]
    assert "real" in prov_modes
    assert "manual" in prov_modes
    assert "mocked" in prov_modes
    assert "unavailable" in prov_modes

    # Check question text join
    q_texts = [row[reader[0].index("question_text")] for row in reader[1:]]
    assert all(text == "How do creators optimize visibility?" for text in q_texts)

    # Filter by market=UK
    uk_csv = ReportGenerator.export_visibility_csv(session=db_session, market="UK")
    uk_reader = list(csv.reader(io.StringIO(uk_csv)))
    assert len(uk_reader) == 2  # 1 header + 1 UK row
    assert uk_reader[1][uk_reader[0].index("market")] == "UK"

    # Filter by provider=google_search
    google_csv = ReportGenerator.export_visibility_csv(session=db_session, provider="google_search")
    google_reader = list(csv.reader(io.StringIO(google_csv)))
    assert len(google_reader) == 2  # 1 header + 1 google row

    # Filter by date
    recent_csv = ReportGenerator.export_visibility_csv(
        session=db_session,
        start_date=now - timedelta(days=3),
    )
    recent_reader = list(csv.reader(io.StringIO(recent_csv)))
    assert len(recent_reader) == 3  # Header + rows within last 3 days (google + perplexity)


# ==============================================================================
# 3. Technical Fixes CSV Export Tests
# ==============================================================================


def test_export_technical_fixes_csv_empty(db_session: Session):
    """Empty audit findings table returns valid headers."""
    csv_str = ReportGenerator.export_technical_fixes_csv(session=db_session)
    reader = list(csv.reader(io.StringIO(csv_str)))
    assert len(reader) == 1
    headers = reader[0]
    assert "finding_id" in headers
    assert "code_patch" in headers
    assert "severity" in headers


def test_export_technical_fixes_csv_populated(db_session: Session):
    """Verify technical fixes CSV export with patches and filtering."""
    audit_repo = AuditFindingRepository(db_session)
    audit_repo.record_finding(AuditFindingCreate(
        target_url="https://incubrix.com/blog",
        audit_category="indexability",
        issue_code="noindex_directive_present",
        severity=AuditSeverity.CRITICAL,
        status=AuditStatus.FAIL,
        validation_status=ValidationStatus.UNVALIDATED,
        confidence=1.0,
        description="noindex tag blocks indexing",
        recommendation="Remove noindex tag",
        patch='<meta name="robots" content="index, follow">',
    ))

    audit_repo.record_finding(AuditFindingCreate(
        target_url="https://incubrix.com/features",
        audit_category="metadata",
        issue_code="title_missing",
        severity=AuditSeverity.HIGH,
        status=AuditStatus.PASS,
        validation_status=ValidationStatus.VALIDATED,
        confidence=0.9,
        description="Title exists",
    ))

    csv_str = ReportGenerator.export_technical_fixes_csv(session=db_session)
    reader = list(csv.reader(io.StringIO(csv_str)))
    assert len(reader) == 3

    # Filter by status=fail
    fail_csv = ReportGenerator.export_technical_fixes_csv(session=db_session, status_val="fail")
    fail_reader = list(csv.reader(io.StringIO(fail_csv)))
    assert len(fail_reader) == 2
    assert "Remove noindex tag" in fail_csv
    assert fail_reader[1][fail_reader[0].index("code_patch")] == '<meta name="robots" content="index, follow">'

    # Filter by url
    url_csv = ReportGenerator.export_technical_fixes_csv(session=db_session, url="https://incubrix.com/features")
    url_reader = list(csv.reader(io.StringIO(url_csv)))
    assert len(url_reader) == 2


# ==============================================================================
# 4. Citation Targets CSV Export Tests
# ==============================================================================


def test_export_citation_targets_csv_empty(db_session: Session):
    """Empty citation targets table returns valid headers."""
    csv_str = ReportGenerator.export_citation_targets_csv(session=db_session)
    reader = list(csv.reader(io.StringIO(csv_str)))
    assert len(reader) == 1
    headers = reader[0]
    assert "target_domain" in headers
    assert "pitch_angle" in headers
    assert "authority_score" in headers


def test_export_citation_targets_csv_populated(db_session: Session):
    """Verify citation targets CSV export with authority scores, pitch angles, and filters."""
    cite_repo = CitationRepository(db_session)
    cite_repo.create_target(CitationTargetCreate(
        target_domain="searchengineland.com",
        target_url="https://searchengineland.com/aeo-guide",
        gap_type="authority_publisher",
        authority_score=91,
        relevance="Premier search authority",
        pitch_angle="Pitch AEO case study on creator visibility benchmarks",
    ))

    cite_repo.create_target(CitationTargetCreate(
        target_domain="hubspot.com",
        target_url="https://blog.hubspot.com/marketing/creator-tools",
        gap_type="directory_listing",
        authority_score=93,
        relevance="Creator marketing guides",
        pitch_angle="Contribute creator business model dataset",
    ))

    csv_str = ReportGenerator.export_citation_targets_csv(session=db_session)
    reader = list(csv.reader(io.StringIO(csv_str)))
    assert len(reader) == 3

    # Filter by domain
    domain_csv = ReportGenerator.export_citation_targets_csv(session=db_session, domain="searchengineland.com")
    d_reader = list(csv.reader(io.StringIO(domain_csv)))
    assert len(d_reader) == 2
    assert d_reader[1][d_reader[0].index("authority_score")] == "91"

    # Filter by gap_type
    gap_csv = ReportGenerator.export_citation_targets_csv(session=db_session, gap_type="directory_listing")
    g_reader = list(csv.reader(io.StringIO(gap_csv)))
    assert len(g_reader) == 2
    assert "hubspot.com" in gap_csv


# ==============================================================================
# 5. Weekly Report Synthesis Tests
# ==============================================================================


def test_generate_weekly_report_empty_state(db_session: Session):
    """Weekly report synthesis handles empty database state without dividing by zero."""
    report = ReportGenerator.generate_weekly_report(
        session=db_session,
        save_to_disk=False,
    )
    assert isinstance(report, WeeklyReportResponse)
    assert report.total_observations == 0
    assert report.provenance_breakdown.real == 0
    assert report.provenance_breakdown.manual == 0
    assert report.provenance_breakdown.mocked == 0
    assert report.provenance_breakdown.unavailable == 0
    assert report.average_visibility_score is None
    assert "Notice: Empty State Detected" in report.markdown_content
    assert "# IncuBrix Visibility Engine — Weekly Executive Intelligence Report" in report.markdown_content


def test_generate_weekly_report_populated(db_session: Session):
    """Weekly report calculates KPIs, provenance tallies, audit posture, and draft status."""
    q_repo = QuestionRepository(db_session)
    q = q_repo.create_strict(QuestionCreate(
        text="How do creators monetize on IncuBrix?",
        target_audience="Creators",
        creator_intent="Monetization",
    ))

    obs_repo = ObservationRepository(db_session)
    now = datetime.now(timezone.utc)

    # 1. Real
    obs_repo.record_observation(
        ObservationCreate(
            question_id=q.id,
            market="US",
            provider=ProviderType.GOOGLE_SEARCH,
            observation_type=ObservationType.SEARCH_ENGINE,
            collection_status=CollectionStatus.SUCCESS,
            rank_position=1,
            answer_box_present=True,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.CITED,
            measured_at=now,
            competitors_observed=["Patreon", "Substack"],
        ),
        visibility_score=100,
    )

    # 2. Manual
    obs_repo.record_observation(
        ObservationCreate(
            question_id=q.id,
            market="US",
            provider=ProviderType.PERPLEXITY,
            observation_type=ObservationType.AI_ASSISTANT,
            collection_status=CollectionStatus.SUCCESS,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.CITED,
            measured_at=now,
            meta={"is_manual_evidence": True},
        ),
        visibility_score=90,
    )

    # 3. Mocked
    obs_repo.record_observation(
        ObservationCreate(
            question_id=q.id,
            market="US",
            provider=ProviderType.CHATGPT,
            observation_type=ObservationType.AI_ASSISTANT,
            collection_status=CollectionStatus.SUCCESS,
            measured_at=now,
            meta={"is_mock": True},
        ),
        visibility_score=50,
    )

    # 4. Unavailable
    obs_repo.record_observation(
        ObservationCreate(
            question_id=q.id,
            market="US",
            provider=ProviderType.BING_COPILOT,
            observation_type=ObservationType.AI_ASSISTANT,
            collection_status=CollectionStatus.UNAVAILABLE,
            measured_at=now,
        ),
        visibility_score=None,
    )

    # Seed an Audit Finding
    audit_repo = AuditFindingRepository(db_session)
    audit_repo.record_finding(AuditFindingCreate(
        target_url="https://incubrix.com",
        audit_category="indexability",
        issue_code="canonical_defect",
        severity=AuditSeverity.CRITICAL,
        status=AuditStatus.FAIL,
        validation_status=ValidationStatus.UNVALIDATED,
        confidence=1.0,
        description="Missing canonical",
    ))

    # Seed a Content Page with Brief
    content_repo = ContentRepository(db_session)
    brief = content_repo.create_brief(ContentBriefCreate(
        question_id=q.id,
        target_topic="Creator Monetization",
        target_query="How do creators monetize on IncuBrix?",
        primary_intent="monetization",
        target_entities=["IncuBrix", "Subscriptions"],
        required_sections=["## Overview", "## Models"],
        recommended_faqs=["How fast can I earn?"],
        target_word_count=600,
        tone="authoritative and actionable",
        schema_type="TechArticle",
    ))
    content_repo.create_page(GeneratedPageCreate(
        brief_id=brief.id,
        slug="how-creators-monetize",
        title="Creator Monetization Guide",
        meta_description="Comprehensive guide on how creators monetize on IncuBrix.",
        markdown_content="IncuBrix enables creators to monetize through memberships and tips. Read this complete guide to optimize your creator business.",
        schema_org_json={"@type": "TechArticle"},
        publication_status="unreviewed",
        internal_links=[{"target_url": "/pricing", "anchor_text": "pricing plans"}],
        citations=[{"url": "https://incubrix.com", "source_title": "IncuBrix Platform"}],
        word_count=500,
    ))

    # Seed Citation Targets
    cite_repo = CitationRepository(db_session)
    cite_repo.create_target(CitationTargetCreate(
        target_domain="searchengineland.com",
        gap_type="authority_publisher",
        authority_score=92,
        relevance="AEO Coverage",
        pitch_angle="Pitch creator discovery benchmark",
    ))

    report = ReportGenerator.generate_weekly_report(
        session=db_session,
        save_to_disk=False,
    )

    assert report.total_observations == 4
    assert report.provenance_breakdown.real == 1
    assert report.provenance_breakdown.manual == 1
    assert report.provenance_breakdown.mocked == 1
    assert report.provenance_breakdown.unavailable == 1

    # Check metrics
    assert report.average_visibility_score is not None
    assert report.top_10_ranking_rate_pct > 0
    assert report.ai_mention_rate_pct > 0

    # Check summaries
    assert report.audit_summary["total_findings"] == 1
    assert report.audit_summary["critical_defects"] == 1
    assert report.content_summary["total_drafts"] == 1
    assert report.content_summary["unreviewed"] == 1
    assert report.citation_summary["total_targets"] == 1
    assert report.citation_summary["top_priority_targets_count"] == 1

    # Check markdown sections
    assert "## 1. Executive Summary & Visibility KPIs" in report.markdown_content
    assert "## 2. Observation Provenance & Empirical Reliability" in report.markdown_content
    assert "| **Real (Automated Live)** | `1` |" in report.markdown_content
    assert "| **Manual (Operator Import)** | `1` |" in report.markdown_content
    assert "| **Mocked (Test Fixtures)** | `1` |" in report.markdown_content
    assert "| **Unavailable / Failed** | `1` |" in report.markdown_content
    assert "Patreon" in report.markdown_content or "Substack" in report.markdown_content
    assert "searchengineland.com" in report.markdown_content


def test_generate_weekly_report_persistence(db_session: Session, tmp_path: Path):
    """Verify weekly report disk persistence writes markdown and json files."""
    with patch.object(ReportGenerator, "REPORTS_DIR", tmp_path):
        report = ReportGenerator.generate_weekly_report(
            session=db_session,
            save_to_disk=True,
        )
        assert report is not None

        # Verify files were created
        md_files = list(tmp_path.glob("weekly_report_*.md"))
        json_files = list(tmp_path.glob("weekly_report_*.json"))
        assert len(md_files) == 1
        assert len(json_files) == 1

        md_text = md_files[0].read_text(encoding="utf-8")
        assert "Weekly Executive Intelligence Report" in md_text


# ==============================================================================
# 6. REST API Endpoints Tests
# ==============================================================================


def test_api_export_visibility_csv(client: TestClient, db_session: Session):
    """Test GET /v1/reports/export/visibility.csv endpoint."""
    resp = client.get("/v1/reports/export/visibility.csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment; filename=visibility.csv" in resp.headers["content-disposition"]
    assert "observation_id" in resp.text
    assert "provenance_mode" in resp.text


def test_api_export_technical_fixes_csv(client: TestClient, db_session: Session):
    """Test GET /v1/reports/export/technical_fixes.csv endpoint."""
    resp = client.get("/v1/reports/export/technical_fixes.csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment; filename=technical_fixes.csv" in resp.headers["content-disposition"]
    assert "finding_id" in resp.text
    assert "code_patch" in resp.text


def test_api_export_citation_targets_csv(client: TestClient, db_session: Session):
    """Test GET /v1/reports/export/citation_targets.csv endpoint."""
    resp = client.get("/v1/reports/export/citation_targets.csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment; filename=citation_targets.csv" in resp.headers["content-disposition"]
    assert "target_domain" in resp.text
    assert "pitch_angle" in resp.text


def test_api_generate_weekly_report(client: TestClient, db_session: Session):
    """Test GET /v1/reports/weekly endpoint."""
    resp = client.get("/v1/reports/weekly?save_to_disk=false")
    assert resp.status_code == 200
    data = resp.json()
    assert data["report_title"] == "IncuBrix Weekly Visibility & Intelligence Report"
    assert "provenance_breakdown" in data
    assert "real" in data["provenance_breakdown"]
    assert "manual" in data["provenance_breakdown"]
    assert "mocked" in data["provenance_breakdown"]
    assert "unavailable" in data["provenance_breakdown"]
    assert "markdown_content" in data
    assert "audit_summary" in data
    assert "content_summary" in data
    assert "citation_summary" in data
