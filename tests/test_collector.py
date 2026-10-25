"""Integration tests for AutomatedCollector and harvest API endpoints."""

import json
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_ai_provider, get_search_provider
from app.collectors.automated_collector import AutomatedCollector
from app.database.models.question import QuestionModel
from app.database.repositories.citation_repo import CitationRepository
from app.database.repositories.evidence_repo import EvidenceRepository
from app.database.repositories.observation_repo import ObservationRepository
from app.database.repositories.question_repo import QuestionRepository
from app.main import app
from app.providers.ai_provider import AIProvider
from app.providers.search_provider import SearchProvider
from app.schemas.common import CitationStatus, CollectionStatus, MentionStatus, ProviderType
from app.schemas.questions import QuestionCreate


@pytest.fixture
def test_question(db_session: Session) -> QuestionModel:
    """Fixture creating a test creator question."""
    repo = QuestionRepository(db_session)
    return repo.create_strict(
        QuestionCreate(
            text="How do creators turn podcast audio into video b-roll?",
            target_market="US",
            target_location="New York, NY",
        )
    )


def test_automated_collector_full_success_pipeline(db_session: Session, test_question: QuestionModel):
    """Verify automated collection stores raw evidence, parses mentions, scores, and deduplicates."""
    mock_payload = {
        "searchParameters": {"q": test_question.text, "gl": "us"},
        "answerBox": {
            "snippet": "IncuBrix matches voiceover segments with AI-selected b-roll clips.",
            "link": "https://incubrix.com/overview",
        },
        "organic": [
            {
                "title": "IncuBrix Video Workflow",
                "link": "https://incubrix.com",
                "snippet": "Automated video generation for creators.",
                "position": 1,
            },
            {
                "title": "Descript Editing Suite",
                "link": "https://descript.com",
                "snippet": "Podcast transcription and video tools.",
                "position": 2,
            },
        ],
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = httpx.Response(
        status_code=200,
        text=json.dumps(mock_payload),
        request=httpx.Request("POST", "https://google.serper.dev/search"),
    )

    provider = SearchProvider(api_key="test-key", http_client=mock_client)
    ev_repo = EvidenceRepository(db_session)
    obs_repo = ObservationRepository(db_session)
    cite_repo = CitationRepository(db_session)

    collector = AutomatedCollector(
        provider=provider,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
        citation_repo=cite_repo,
    )

    # 1. First collection execution
    obs = collector.collect(test_question)

    assert obs.id is not None
    assert obs.question_id == test_question.id
    assert obs.collection_status == "success"
    assert obs.incubrix_mentioned == MentionStatus.MENTIONED.value
    assert obs.incubrix_cited == CitationStatus.CITED.value
    assert "Descript" in obs.competitors_observed
    assert "incubrix.com" in obs.quoted_domains
    assert "descript.com" in obs.quoted_domains
    assert "https://incubrix.com/overview" in obs.quoted_urls
    assert "https://descript.com" in obs.quoted_urls
    assert "answer_box" in obs.observed_features
    assert "organic_results" in obs.observed_features
    assert obs.rank_position == 1
    assert obs.answer_box_present is True
    assert obs.visibility_score == 100

    # Verify raw evidence artifact provenance and SHA-256 hash
    assert obs.artifact_id is not None
    evidence = ev_repo.get_by_id(obs.artifact_id)
    assert evidence is not None
    assert len(evidence.content_hash) == 64
    assert evidence.question_id == test_question.id
    assert "google_search" in evidence.collected_by

    # Verify competitor citation target was captured
    targets = cite_repo.list_by_domain("descript.com")
    assert len(targets) >= 1
    assert targets[0].question_id == test_question.id

    # 2. Duplicate prevention test: second run on same day returns existing record
    obs_duplicate = collector.collect(test_question)
    assert obs_duplicate.id == obs.id
    assert obs_repo.count() == 1


def test_automated_collector_unconfigured_resilience(db_session: Session, test_question: QuestionModel):
    """Verify collector handles unconfigured provider without crashing or false negatives."""
    provider = SearchProvider(api_key=None)  # Not configured
    ev_repo = EvidenceRepository(db_session)
    obs_repo = ObservationRepository(db_session)

    collector = AutomatedCollector(
        provider=provider,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
    )

    obs = collector.collect(test_question)

    assert obs.collection_status == CollectionStatus.UNAVAILABLE.value
    assert obs.error_code == "PROVIDER_NOT_CONFIGURED"
    assert obs.incubrix_mentioned == MentionStatus.UNKNOWN.value
    assert obs.incubrix_cited == CitationStatus.UNAVAILABLE.value
    assert obs.visibility_score is None  # Unavailable collections cannot be scored


def test_harvest_api_endpoint(client: TestClient, test_question: QuestionModel):
    """Verify POST /v1/observations/harvest/{question_id} route."""
    mock_payload = {
        "searchParameters": {"q": test_question.text},
        "organic": [
            {
                "title": "IncuBrix Video",
                "link": "https://incubrix.com",
                "snippet": "IncuBrix video engine turns audio into b-roll clips.",
                "position": 1,
            }
        ],
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = httpx.Response(
        status_code=200,
        text=json.dumps(mock_payload),
        request=httpx.Request("POST", "https://google.serper.dev/search"),
    )

    # Override search provider to use test mock client
    mock_search = SearchProvider(api_key="test-key", http_client=mock_client)
    app.dependency_overrides[get_search_provider] = lambda: mock_search

    try:
        resp = client.post(
            f"/v1/observations/harvest/{test_question.id}",
            params={"provider_type": "google_search", "market": "US"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["question_id"] == test_question.id
        assert data["incubrix_mentioned"] == "mentioned"
        assert data["incubrix_cited"] == "cited"
        assert data["collection_status"] == "success"
        assert data["visibility_score"] is not None
    finally:
        app.dependency_overrides.pop(get_search_provider, None)


def test_harvest_nonexistent_question_404(client: TestClient):
    """Verify harvesting for a nonexistent question returns 404."""
    resp = client.post("/v1/observations/harvest/nonexistent-uuid")
    assert resp.status_code == 404
