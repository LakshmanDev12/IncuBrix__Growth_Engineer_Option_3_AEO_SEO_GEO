"""Unit tests for repository layer database operations and duplicate prevention."""

import pytest
from sqlalchemy.orm import Session

from app.database.repositories.audit_repo import AuditFindingRepository
from app.database.repositories.citation_repo import CitationRepository
from app.database.repositories.content_repo import ContentRepository
from app.database.repositories.evidence_repo import EvidenceRepository
from app.database.repositories.observation_repo import ObservationRepository
from app.database.repositories.pipeline_repo import PipelineRunRepository
from app.database.repositories.question_repo import QuestionRepository
from app.exceptions import DuplicateEntityError
from app.schemas.audit import AuditFindingCreate
from app.schemas.citation import CitationTargetCreate
from app.schemas.common import AuditSeverity, AuditStatus, CitationGapType
from app.schemas.content import ContentBriefCreate, GeneratedPageCreate
from app.schemas.evidence import EvidenceArtifactCreate
from app.schemas.observations import ObservationCreate
from app.schemas.pipeline import PipelineRunCreate
from app.schemas.questions import QuestionCreate, QuestionUpdate
from tests.fixtures.synthetic_test_data import (
    SAMPLE_AUDIT_FINDING_CREATE,
    SAMPLE_CITATION_TARGET_CREATE,
    SAMPLE_CONTENT_BRIEF_CREATE,
    SAMPLE_EVIDENCE_CREATE,
    SAMPLE_OBSERVATION_CREATE,
    SAMPLE_PIPELINE_RUN_CREATE,
    SAMPLE_QUESTION_CREATE,
)


def test_question_repository_crud_and_duplicate_prevention(db_session: Session):
    """Test QuestionRepository CRUD operations and strict duplicate prevention."""
    repo = QuestionRepository(db_session)

    # 1. Create question
    created = repo.create_strict(SAMPLE_QUESTION_CREATE)
    assert created.id is not None
    assert created.text == SAMPLE_QUESTION_CREATE.text

    # 2. Duplicate prevention
    with pytest.raises(DuplicateEntityError) as exc_info:
        repo.create_strict(SAMPLE_QUESTION_CREATE)
    assert "Question already exists" in str(exc_info.value)

    # 3. Get by text
    fetched = repo.get_by_text(SAMPLE_QUESTION_CREATE.text)
    assert fetched is not None
    assert fetched.id == created.id

    # 4. Update
    updated = repo.update_question(
        created.id, QuestionUpdate(persona="independent_filmmaker")
    )
    assert updated is not None
    assert updated.persona == "independent_filmmaker"

    # 5. List
    questions = repo.list()
    assert len(questions) == 1

    # 6. Delete
    deleted = repo.delete(created.id)
    assert deleted is True
    assert repo.get_by_id(created.id) is None


def test_evidence_repository_deduplication(db_session: Session):
    """Test EvidenceRepository SHA-256 deduplication."""
    repo = EvidenceRepository(db_session)

    ev_data = EvidenceArtifactCreate(
        content="Identical evidence artifact payload for deduplication test.",
        collected_by="test_runner",
    )

    # First insert succeeds
    ev1, created1 = repo.store_evidence(ev_data, allow_existing=True)
    assert created1 is True
    assert ev1.id is not None

    # Second insert with identical payload returns existing without duplicate row
    ev2, created2 = repo.store_evidence(ev_data, allow_existing=True)
    assert created2 is False
    assert ev2.id == ev1.id
    assert repo.count() == 1

    # Strict mode raises DuplicateEntityError
    with pytest.raises(DuplicateEntityError):
        repo.store_evidence(ev_data, allow_existing=False)


def test_observation_repository_recording_and_deduplication(db_session: Session):
    """Test ObservationRepository recording, fingerprint deduplication, and metrics."""
    q_repo = QuestionRepository(db_session)
    q = q_repo.create_strict(
        QuestionCreate(text="How to sync b-roll clips to audio?")
    )

    obs_repo = ObservationRepository(db_session)
    obs_data = ObservationCreate(
        question_id=q.id,
        market="US",
        location="Chicago, IL",
        provider=SAMPLE_OBSERVATION_CREATE.provider,
        observation_type=SAMPLE_OBSERVATION_CREATE.observation_type,
        raw_answer=SAMPLE_OBSERVATION_CREATE.raw_answer,
        incubrix_mentioned=SAMPLE_OBSERVATION_CREATE.incubrix_mentioned,
        incubrix_cited=SAMPLE_OBSERVATION_CREATE.incubrix_cited,
        rank_position=2,
        answer_box_present=True,
    )

    # Record observation
    obs, created = obs_repo.record_observation(
        obs_data, visibility_score=80, allow_existing=True
    )
    assert created is True
    assert obs.visibility_score == 80
    assert obs.fingerprint is not None

    # Duplicate observation on same day returns existing record
    obs2, created2 = obs_repo.record_observation(
        obs_data, visibility_score=80, allow_existing=True
    )
    assert created2 is False
    assert obs2.id == obs.id

    # Strict mode raises DuplicateEntityError
    with pytest.raises(DuplicateEntityError):
        obs_repo.record_observation(
            obs_data, visibility_score=80, allow_existing=False
        )

    # Metrics summary calculation
    summary = obs_repo.get_summary_metrics()
    assert summary["total_observations"] == 1
    assert summary["scored_observations"] == 1
    assert summary["average_visibility_score"] == 80.0
    assert summary["mention_stats"]["mentioned"] == 1
    assert summary["citation_stats"]["cited"] == 1


def test_audit_repository_recording(db_session: Session):
    """Test AuditFindingRepository persistence and category listing."""
    repo = AuditFindingRepository(db_session)

    finding = repo.record_finding(SAMPLE_AUDIT_FINDING_CREATE)
    assert finding.id is not None
    assert finding.issue_code == "VALID_LLMS_TXT"

    by_category = repo.list_by_category("llms_txt")
    assert len(by_category) == 1
    assert by_category[0].id == finding.id


def test_content_repository_brief_and_page_duplicate_slug(db_session: Session):
    """Test ContentRepository and duplicate slug prevention."""
    repo = ContentRepository(db_session)

    # Create brief
    brief = repo.create_brief(SAMPLE_CONTENT_BRIEF_CREATE)
    assert brief.id is not None
    assert brief.target_word_count == 1200

    # Create page
    page_data = GeneratedPageCreate(
        brief_id=brief.id,
        title="Automating B-roll With IncuBrix",
        slug="automating-b-roll-with-incubrix",
        meta_description="How to automate b-roll using AI.",
        markdown_content="# Automating B-roll\n\nAutomate b-roll clips using the IncuBrix AI pipeline and verified footage.",
        schema_org_json={"@type": "TechArticle"},
    )
    page = repo.create_page(page_data)
    assert page.id is not None
    assert page.slug == "automating-b-roll-with-incubrix"

    # Duplicate slug raises DuplicateEntityError
    with pytest.raises(DuplicateEntityError) as exc_info:
        repo.create_page(page_data)
    assert "GeneratedPage already exists" in str(exc_info.value)


def test_citation_repository_operations(db_session: Session):
    """Test CitationRepository persistence and query by domain."""
    repo = CitationRepository(db_session)

    target = repo.create_target(SAMPLE_CITATION_TARGET_CREATE)
    assert target.id is not None
    assert target.target_domain == "searchengineland.example.test"

    results = repo.list_by_domain("searchengineland.example.test")
    assert len(results) == 1
    assert results[0].id == target.id


def test_pipeline_run_repository_lifecycle(db_session: Session):
    """Test PipelineRunRepository tracking from start to completion."""
    repo = PipelineRunRepository(db_session)

    run = repo.start_run(SAMPLE_PIPELINE_RUN_CREATE)
    assert run.id is not None
    assert run.status == "running"

    completed = repo.complete_run(
        run_id=run.id,
        processed_items=10,
        successful_items=10,
        failed_items=0,
    )
    assert completed is not None
    assert completed.status == "completed"
    assert completed.successful_items == 10
    assert completed.completed_at is not None
