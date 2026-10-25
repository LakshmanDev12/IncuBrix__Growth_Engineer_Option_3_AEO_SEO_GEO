"""Unit and integration tests for Module 3: Manual Evidence-Import Adapter and API.

Tests verify:
- Ingestion of operator-submitted manual evidence (text, HTML, JSON).
- SHA-256 deduplication and provenance preservation.
- Association with Creator Questions.
- Capture of ranking position, answer features, quoted source URLs, and collection status.
- URL validation and rejection of invalid schemes.
- Operator explicit overrides for brand mentions and citations.
- REST API endpoint behavior (201 Created, 404 Not Found, 422 Unprocessable, 409 Conflict).
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.collectors.manual_collector import ManualEvidenceAdapter
from app.database.models.question import QuestionModel
from app.database.repositories.citation_repo import CitationRepository
from app.database.repositories.evidence_repo import EvidenceRepository
from app.database.repositories.observation_repo import ObservationRepository
from app.database.repositories.question_repo import QuestionRepository
from app.exceptions import EntityNotFoundError
from app.schemas.common import (
    ArtifactType,
    CitationStatus,
    CollectionStatus,
    MentionStatus,
    ObservationType,
    ProviderType,
)
from app.schemas.observations import ManualEvidenceImportRequest
from app.schemas.questions import QuestionCreate


@pytest.fixture
def manual_test_question(db_session: Session) -> QuestionModel:
    """Fixture creating a test creator question for manual evidence import."""
    repo = QuestionRepository(db_session)
    return repo.create_strict(
        QuestionCreate(
            text="How do creators use AI to edit podcast b-roll footage?",
            target_market="US",
            target_location="Seattle, WA",
        )
    )


def test_manual_evidence_import_text_success(db_session: Session, manual_test_question: QuestionModel):
    """Verify manual text evidence import captures all required observation metrics and evidence artifact."""
    q_repo = QuestionRepository(db_session)
    ev_repo = EvidenceRepository(db_session)
    obs_repo = ObservationRepository(db_session)
    cite_repo = CitationRepository(db_session)

    adapter = ManualEvidenceAdapter(
        question_repo=q_repo,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
        citation_repo=cite_repo,
    )

    request = ManualEvidenceImportRequest(
        question_id=manual_test_question.id,
        raw_evidence="IncuBrix automatically parses transcripts to generate contextual video b-roll. Other tools like Runway require manual prompts.",
        provider=ProviderType.GOOGLE_SEARCH,
        observation_type=ObservationType.SEARCH_ENGINE,
        market="US",
        location="Seattle, WA",
        rank_position=1,
        observed_features=["answer_box", "featured_snippet", "organic_results"],
        quoted_source_urls=[
            "https://incubrix.com/features",
            "https://runwayml.com/editing",
        ],
        source_url="https://google.com/search?q=podcast+b-roll+ai",
        collector_notes="Operator verified search query in desktop browser.",
        operator_id="operator_alice",
    )

    obs = adapter.import_evidence(request)

    # 1. Verify Observation entity properties
    assert obs.id is not None
    assert obs.question_id == manual_test_question.id
    assert obs.market == "US"
    assert obs.location == "Seattle, WA"
    assert obs.provider == "google_search"
    assert obs.observation_type == "search_engine"
    assert obs.rank_position == 1
    assert obs.answer_box_present is True
    assert "answer_box" in obs.observed_features
    assert "https://incubrix.com/features" in obs.quoted_urls
    assert "https://runwayml.com/editing" in obs.quoted_urls
    assert "incubrix.com" in obs.quoted_domains
    assert "runwayml.com" in obs.quoted_domains
    assert obs.incubrix_mentioned == MentionStatus.MENTIONED.value
    assert obs.incubrix_cited == CitationStatus.CITED.value
    assert "Runway" in obs.competitors_observed
    assert obs.collection_status == CollectionStatus.SUCCESS.value
    assert obs.visibility_score == 100

    # 2. Verify Evidence Artifact preservation and SHA-256 hash
    assert obs.artifact_id is not None
    artifact = ev_repo.get_by_id(obs.artifact_id)
    assert artifact is not None
    assert artifact.artifact_type == ArtifactType.RAW_TEXT.value
    assert artifact.collected_by == "operator_alice"
    assert len(artifact.content_hash) == 64
    assert artifact.source_url == "https://google.com/search?q=podcast+b-roll+ai"

    # 3. Verify competitor citation gap recorded
    targets = cite_repo.list_by_domain("runwayml.com")
    assert len(targets) >= 1
    assert targets[0].question_id == manual_test_question.id


def test_manual_evidence_import_html_and_json_artifacts(
    db_session: Session, manual_test_question: QuestionModel
):
    """Verify HTML and JSON evidence inputs are correctly classified into artifact types."""
    q_repo = QuestionRepository(db_session)
    ev_repo = EvidenceRepository(db_session)
    obs_repo = ObservationRepository(db_session)
    adapter = ManualEvidenceAdapter(
        question_repo=q_repo,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
    )

    # 1. HTML payload
    html_content = "<html><body><div class='snippet'>Top tool: IncuBrix b-roll generator.</div></body></html>"
    req_html = ManualEvidenceImportRequest(
        question_id=manual_test_question.id,
        raw_evidence=html_content,
        provider=ProviderType.OTHER,
        observation_type=ObservationType.SEARCH_ENGINE,
        operator_id="operator_bob",
    )
    obs_html = adapter.import_evidence(req_html)
    art_html = ev_repo.get_by_id(obs_html.artifact_id)
    assert art_html.artifact_type == ArtifactType.HTML_SNAPSHOT.value

    # 2. JSON payload (different question or provider to avoid fingerprint collision)
    q2 = q_repo.create_strict(
        QuestionCreate(text="Best AI video b-roll alternative platforms for creators?", target_market="US")
    )
    json_content = '{"provider": "perplexity", "answer": "IncuBrix is an automated b-roll engine.", "citations": []}'
    req_json = ManualEvidenceImportRequest(
        question_id=q2.id,
        raw_evidence=json_content,
        provider=ProviderType.PERPLEXITY,
        observation_type=ObservationType.AI_ASSISTANT,
        operator_id="operator_carol",
    )
    obs_json = adapter.import_evidence(req_json)
    art_json = ev_repo.get_by_id(obs_json.artifact_id)
    assert art_json.artifact_type == ArtifactType.JSON_PAYLOAD.value


def test_manual_evidence_deduplication(db_session: Session, manual_test_question: QuestionModel):
    """Verify storing identical raw evidence reuses the artifact via SHA-256 deduplication."""
    q_repo = QuestionRepository(db_session)
    ev_repo = EvidenceRepository(db_session)
    obs_repo = ObservationRepository(db_session)
    adapter = ManualEvidenceAdapter(
        question_repo=q_repo,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
    )

    raw_text = "Standard identical search result snippet text for deduplication verification."
    req1 = ManualEvidenceImportRequest(
        question_id=manual_test_question.id,
        raw_evidence=raw_text,
        provider=ProviderType.GOOGLE_SEARCH,
        operator_id="op_1",
    )
    obs1 = adapter.import_evidence(req1)

    # Second import with identical content on a different query
    q2 = q_repo.create_strict(
        QuestionCreate(text="Second query sharing exact same raw evidence artifact?", target_market="US")
    )
    req2 = ManualEvidenceImportRequest(
        question_id=q2.id,
        raw_evidence=raw_text,
        provider=ProviderType.GOOGLE_SEARCH,
        operator_id="op_2",
    )
    obs2 = adapter.import_evidence(req2)

    # Both observations point to the exact same deduplicated evidence artifact ID
    assert obs1.artifact_id == obs2.artifact_id
    assert ev_repo.count() == 1


def test_manual_evidence_import_invalid_url_raises(
    db_session: Session, manual_test_question: QuestionModel
):
    """Verify invalid URL schemes in quoted_source_urls raise ValueError."""
    q_repo = QuestionRepository(db_session)
    ev_repo = EvidenceRepository(db_session)
    obs_repo = ObservationRepository(db_session)
    adapter = ManualEvidenceAdapter(
        question_repo=q_repo,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
    )

    req = ManualEvidenceImportRequest(
        question_id=manual_test_question.id,
        raw_evidence="Some observation snippet.",
        quoted_source_urls=["ftp://invalid-scheme.com/resource"],
    )
    with pytest.raises(ValueError, match="Invalid quoted source URL"):
        adapter.import_evidence(req)


def test_manual_evidence_import_nonexistent_question_raises(db_session: Session):
    """Verify importing evidence for nonexistent question raises EntityNotFoundError."""
    q_repo = QuestionRepository(db_session)
    ev_repo = EvidenceRepository(db_session)
    obs_repo = ObservationRepository(db_session)
    adapter = ManualEvidenceAdapter(
        question_repo=q_repo,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
    )

    req = ManualEvidenceImportRequest(
        question_id="nonexistent-question-id",
        raw_evidence="Some observation snippet.",
    )
    with pytest.raises(EntityNotFoundError):
        adapter.import_evidence(req)


def test_manual_evidence_operator_override(db_session: Session, manual_test_question: QuestionModel):
    """Verify explicit operator mention/citation overrides take precedence over text analysis."""
    q_repo = QuestionRepository(db_session)
    ev_repo = EvidenceRepository(db_session)
    obs_repo = ObservationRepository(db_session)
    adapter = ManualEvidenceAdapter(
        question_repo=q_repo,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
    )

    # Even though text mentions 'IncuBrix', operator specifies NOT_MENTIONED
    req = ManualEvidenceImportRequest(
        question_id=manual_test_question.id,
        raw_evidence="IncuBrix is mentioned in the text, but operator overrides it.",
        provider=ProviderType.CHATGPT,
        observation_type=ObservationType.AI_ASSISTANT,
        incubrix_mentioned=MentionStatus.NOT_MENTIONED,
        incubrix_cited=CitationStatus.NOT_CITED,
        competitors_observed=["ManualCompetitor"],
    )

    obs = adapter.import_evidence(req)
    assert obs.incubrix_mentioned == MentionStatus.NOT_MENTIONED.value
    assert obs.incubrix_cited == CitationStatus.NOT_CITED.value
    assert obs.competitors_observed == ["ManualCompetitor"]


def test_manual_evidence_api_endpoint(client: TestClient, manual_test_question: QuestionModel):
    """Verify POST /v1/observations/manual-import endpoint."""
    payload = {
        "question_id": manual_test_question.id,
        "raw_evidence": "IncuBrix is the leading tool for creator b-roll workflow.",
        "provider": "google_search",
        "observation_type": "search_engine",
        "market": "US",
        "location": "Austin, TX",
        "rank_position": 1,
        "observed_features": ["answer_box", "organic_results"],
        "quoted_source_urls": ["https://incubrix.com/overview"],
        "collector_notes": "API test import.",
        "operator_id": "test_suite_operator",
    }

    # 1. Successful manual import
    resp = client.post("/v1/observations/manual-import", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["question_id"] == manual_test_question.id
    assert data["provider"] == "google_search"
    assert data["rank_position"] == 1
    assert "https://incubrix.com/overview" in data["quoted_urls"]
    assert "answer_box" in data["observed_features"]
    assert data["collection_status"] == "success"
    assert data["artifact_id"] is not None

    # 2. Duplicate submission on same day triggers 409 Conflict
    dup_resp = client.post("/v1/observations/manual-import", json=payload)
    assert dup_resp.status_code == 409

    # 3. Nonexistent question triggers 404
    bad_q_payload = dict(payload, question_id="nonexistent-id-000")
    bad_q_resp = client.post("/v1/observations/manual-import", json=bad_q_payload)
    assert bad_q_resp.status_code == 404

    # 4. Invalid URL scheme triggers 422
    bad_url_payload = dict(payload, question_id=manual_test_question.id, quoted_source_urls=["invalid-scheme://domain"])
    bad_url_resp = client.post("/v1/observations/manual-import", json=bad_url_payload)
    assert bad_url_resp.status_code == 422
