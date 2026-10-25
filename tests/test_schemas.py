"""Unit tests for schema validation and missing data handling."""

import pytest
from pydantic import ValidationError

from app.schemas.audit import AuditFindingCreate
from app.schemas.citation import CitationTargetCreate
from app.schemas.common import (
    AuditSeverity,
    AuditStatus,
    CitationGapType,
    CitationStatus,
    CollectionStatus,
    MentionStatus,
    ObservationType,
    PipelineRunStatus,
    ProviderType,
)
from app.schemas.content import ContentBriefCreate, GeneratedPageCreate
from app.schemas.evidence import EvidenceArtifactCreate
from app.schemas.observations import ObservationCreate
from app.schemas.pipeline import PipelineRunCreate
from app.schemas.questions import QuestionCreate
from tests.fixtures.synthetic_test_data import (
    SAMPLE_MISSING_DATA_OBSERVATION,
    SAMPLE_OBSERVATION_CREATE,
    SAMPLE_QUESTION_CREATE,
)


def test_question_schema_valid():
    """Verify QuestionCreate validates correct fields and defaults."""
    q = QuestionCreate(
        text="How do creators add automated b-roll to podcasts?",
        target_market="US",
        language="en",
    )
    assert q.text == "How do creators add automated b-roll to podcasts?"
    assert q.target_market == "US"
    assert q.target_location is None
    assert q.intent == "informational"
    assert q.is_active is True


def test_question_schema_short_text_rejected():
    """Verify questions with < 5 characters are rejected."""
    with pytest.raises(ValidationError):
        QuestionCreate(text="Why?")


def test_observation_supports_all_required_fields():
    """Requirement 3: Verify every observation supports:
    - Question ID
    - Search market and location settings
    - Measurement timestamp
    - Provider and observation type
    - Raw answer or a reference to its stored artifact
    - IncuBrix mention status
    - IncuBrix citation status
    - Competitor names where observed
    - Evidence references
    - Collection status and error details
    """
    obs = SAMPLE_OBSERVATION_CREATE
    assert obs.question_id == "dummy-question-id"
    assert obs.market == "US"
    assert obs.location == "Austin, TX"
    assert obs.measured_at is not None
    assert obs.provider == ProviderType.GOOGLE_SEARCH
    assert obs.observation_type == ObservationType.SEARCH_ENGINE
    assert obs.raw_answer is not None
    assert obs.incubrix_mentioned == MentionStatus.MENTIONED
    assert obs.incubrix_cited == CitationStatus.CITED
    assert "CompetitorOne" in obs.competitors_observed
    assert "incubrix.com" in obs.quoted_domains
    assert obs.collection_status == CollectionStatus.SUCCESS
    assert obs.error_code is None
    assert obs.error_details is None


def test_missing_data_never_treated_as_negative():
    """Requirement 4: Verify nullable fields and explicit unknown/unavailable states.

    Missing evidence must never be treated as negative (False).
    """
    obs = SAMPLE_MISSING_DATA_OBSERVATION

    # Statuses must be explicit UNKNOWN or UNAVAILABLE, NOT negative or boolean False
    assert obs.incubrix_mentioned == MentionStatus.UNKNOWN
    assert obs.incubrix_mentioned != MentionStatus.NOT_MENTIONED
    assert obs.incubrix_cited == CitationStatus.UNAVAILABLE
    assert obs.incubrix_cited != CitationStatus.NOT_CITED

    # Nullable fields must be None, never coerced to False or 0
    assert obs.raw_answer is None
    assert obs.location is None
    assert obs.rank_position is None
    assert obs.answer_box_present is None
    assert obs.answer_box_present is not False


def test_evidence_hashing_and_deduplication_checksum():
    """Verify SHA-256 checksum computation for evidence payloads."""
    ev = EvidenceArtifactCreate(
        content="Testing deterministic SHA-256 evidence hashing.",
        collected_by="unit_test",
    )
    hash_1 = ev.compute_hash()
    assert len(hash_1) == 64
    assert hash_1 == ev.compute_hash()

    # Changing content produces different hash
    ev_different = EvidenceArtifactCreate(
        content="Different content entirely.",
        collected_by="unit_test",
    )
    assert hash_1 != ev_different.compute_hash()


def test_observation_fingerprint_generation():
    """Verify deterministic daily observation fingerprint generation."""
    fp1 = SAMPLE_OBSERVATION_CREATE.compute_fingerprint()
    fp2 = SAMPLE_OBSERVATION_CREATE.compute_fingerprint()
    assert fp1 == fp2
    assert len(fp1) == 64


def test_audit_finding_schema_validation():
    """Verify AuditFindingCreate validation."""
    finding = AuditFindingCreate(
        target_url="https://incubrix.com/robots.txt",
        audit_category="crawlability",
        issue_code="AI_BOTS_PERMITTED",
        severity=AuditSeverity.INFO,
        status=AuditStatus.PASS,
        description="All major AI crawlers are allowed.",
        raw_metrics={"bots": ["GPTBot"]},
    )
    assert finding.status == AuditStatus.PASS
    assert finding.severity == AuditSeverity.INFO


def test_content_brief_and_page_schema_validation():
    """Verify ContentBriefCreate and GeneratedPageCreate validation."""
    brief = ContentBriefCreate(
        target_topic="Automating B-roll",
        target_query="How do creators automate b-roll?",
        primary_intent="informational",
        target_entities=["IncuBrix", "AI Video"],
        required_sections=["Intro", "Guide"],
        recommended_faqs=["Q: Fast?\nA: Yes."],
    )
    assert brief.target_word_count == 1200

    page = GeneratedPageCreate(
        brief_id="brief-123",
        title="Guide to Automated B-roll | IncuBrix",
        slug="how-creators-automate-b-roll",
        meta_description="Complete guide on automating b-roll selection with AI.",
        markdown_content="# How Creators Automate B-roll\n\nAutomate b-roll with IncuBrix.",
        schema_org_json={"@context": "https://schema.org", "@type": "TechArticle"},
    )
    assert page.slug == "how-creators-automate-b-roll"


def test_citation_target_schema_validation():
    """Verify CitationTargetCreate validation."""
    target = CitationTargetCreate(
        target_domain="searchengineland.com",
        target_url="https://searchengineland.com/article",
        competitor_domain="competitor.com",
        gap_type=CitationGapType.DIRECT_COMPETITOR,
        authority_score=90,
    )
    assert target.target_domain == "searchengineland.com"
    assert target.gap_type == CitationGapType.DIRECT_COMPETITOR


def test_pipeline_run_schema_validation():
    """Verify PipelineRunCreate validation."""
    run = PipelineRunCreate(
        pipeline_type="observation_harvesting",
        status=PipelineRunStatus.PENDING,
        total_items=25,
    )
    assert run.total_items == 25
    assert run.status == PipelineRunStatus.PENDING
