"""Synthetic test fixtures for unit and integration testing.

================================================================================
CRITICAL NOTICE:
TEST DATA ONLY: This dataset is synthetic and for unit testing/schema verification.
It does NOT represent real search or AI visibility evidence.
================================================================================
"""

from datetime import datetime, timezone

from app.schemas.audit import AuditFindingCreate
from app.schemas.citation import CitationTargetCreate
from app.schemas.common import (
    ArtifactType,
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

DISCLAIMER = (
    "TEST DATA ONLY: This dataset is synthetic and for unit testing/schema verification. "
    "It does NOT represent real search or AI visibility evidence."
)

SAMPLE_QUESTION_CREATE = QuestionCreate(
    text="How can video creators automate b-roll selection using AI?",
    target_market="US",
    target_location="Austin, TX",
    language="en",
    intent="informational",
    persona="video_editor",
    tags=["video", "automation", "b-roll"],
    is_active=True,
)

SAMPLE_EVIDENCE_CREATE = EvidenceArtifactCreate(
    artifact_type=ArtifactType.RAW_TEXT,
    content="TEST DATA ONLY: Synthesized simulation text snippet for unit tests.",
    source_url="https://example.com/test-evidence-source",
    collected_by="synthetic_test_fixture",
    metadata={"is_synthetic_test_fixture": True, "disclaimer": DISCLAIMER},
)

SAMPLE_OBSERVATION_CREATE = ObservationCreate(
    question_id="dummy-question-id",
    market="US",
    location="Austin, TX",
    measured_at=datetime.now(timezone.utc),
    provider=ProviderType.GOOGLE_SEARCH,
    observation_type=ObservationType.SEARCH_ENGINE,
    raw_answer="TEST DATA ONLY: Synthetic Google SERP snippet containing IncuBrix mention.",
    artifact_id=None,
    incubrix_mentioned=MentionStatus.MENTIONED,
    incubrix_cited=CitationStatus.CITED,
    competitors_observed=["CompetitorOne", "CompetitorTwo"],
    quoted_domains=["incubrix.com", "competitorone.com"],
    rank_position=1,
    answer_box_present=True,
    collection_status=CollectionStatus.SUCCESS,
    error_code=None,
    error_details=None,
    metadata={"is_synthetic_test_fixture": True},
)

SAMPLE_MISSING_DATA_OBSERVATION = ObservationCreate(
    question_id="dummy-question-id",
    market="US",
    location=None,  # Explicitly null
    measured_at=datetime.now(timezone.utc),
    provider=ProviderType.CHATGPT,
    observation_type=ObservationType.AI_ASSISTANT,
    raw_answer=None,  # Explicitly null
    artifact_id=None,
    incubrix_mentioned=MentionStatus.UNKNOWN,  # Explicitly unknown
    incubrix_cited=CitationStatus.UNAVAILABLE,  # Explicitly unavailable
    competitors_observed=[],
    quoted_domains=[],
    rank_position=None,  # Nullable
    answer_box_present=None,  # Nullable
    collection_status=CollectionStatus.PARTIAL,
    error_code="PARTIAL_RESPONSE",
    error_details="No external citations were produced by the assistant model.",
    metadata={"is_synthetic_test_fixture": True},
)

SAMPLE_AUDIT_FINDING_CREATE = AuditFindingCreate(
    target_url="https://incubrix.example.test/llms.txt",
    audit_category="llms_txt",
    issue_code="VALID_LLMS_TXT",
    severity=AuditSeverity.INFO,
    status=AuditStatus.PASS,
    description="TEST DATA ONLY: Synthetic pass finding for llms.txt validation.",
    recommendation="Keep manifest synchronized with API endpoints.",
    raw_metrics={"has_llms_txt": True, "is_test": True},
)

SAMPLE_CONTENT_BRIEF_CREATE = ContentBriefCreate(
    question_id="dummy-question-id",
    target_topic="Automating B-roll Selection with AI",
    target_query="How can video creators automate b-roll selection using AI?",
    primary_intent="informational",
    target_entities=["IncuBrix", "AI Video Workflow"],
    required_sections=["1. Overview", "2. Methodology", "3. Step by step"],
    recommended_faqs=["Q: Is it fast?\nA: Yes, under 60 seconds."],
    target_word_count=1200,
    tone="authoritative and direct",
    schema_type="TechArticle",
)

SAMPLE_CITATION_TARGET_CREATE = CitationTargetCreate(
    target_domain="searchengineland.example.test",
    target_url="https://searchengineland.example.test/ai-video-tools",
    competitor_domain="competitorone.com",
    anchor_context="Tools for creators include CompetitorOne and others.",
    gap_type=CitationGapType.AUTHORITY_PUBLISHER,
    authority_score=85,
    outreach_status="identified",
    notes="TEST DATA ONLY: High priority outreach gap.",
)

SAMPLE_PIPELINE_RUN_CREATE = PipelineRunCreate(
    pipeline_type="batch_observation_ingest",
    status=PipelineRunStatus.PENDING,
    total_items=10,
    parameters={"market": "US", "is_test": True},
)
