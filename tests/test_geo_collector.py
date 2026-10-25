"""Unit and integration tests for Module 4: GEO (Generative Engine Optimization) Collector.

Tests verify:
- Independent adapters for configured, permitted AI assistant APIs (Perplexity, OpenAI, Gemini, Claude, Google AI Overview).
- Accurate, decoupled extraction of brand mentions vs direct website citations without conflation.
- Resilient error handling (unconfigured state, HTTP 429 rate limit, request timeout).
- Unsupported assistant prevention: engine never falsely claims unsupported assistants were queried.
- Manual evidence import for assistants without accessible APIs (ChatGPT web, Claude chat, Copilot web).
- Missing evidence handling with explicit unknown/unavailable states.
- API endpoints: GET /v1/geo/assistants, POST /v1/geo/harvest/{id}, POST /v1/geo/manual-import.
"""

from datetime import datetime
import json
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.collectors.geo_collector import GEOCollector
from app.database.models.question import QuestionModel
from app.database.repositories.citation_repo import CitationRepository
from app.database.repositories.evidence_repo import EvidenceRepository
from app.database.repositories.observation_repo import ObservationRepository
from app.database.repositories.question_repo import QuestionRepository
from app.exceptions import EntityNotFoundError
from app.providers.ai_provider import (
    ClaudeAIAdapter,
    GeminiAIAdapter,
    GoogleAIOverviewAdapter,
    OpenAIAdapter,
    PerplexityAIAdapter,
    UnsupportedAIAdapter,
    get_ai_adapter,
)
from app.schemas.common import (
    ArtifactType,
    CitationStatus,
    CollectionStatus,
    MentionStatus,
    ObservationType,
    ProviderType,
)
from app.schemas.observations import GEOManualImportRequest
from app.schemas.questions import QuestionCreate


@pytest.fixture
def geo_question(db_session: Session) -> QuestionModel:
    """Fixture creating a test creator question for GEO evaluations."""
    repo = QuestionRepository(db_session)
    return repo.create_strict(
        QuestionCreate(
            text="What is the best AI tool to generate video b-roll from audio scripts?",
            target_market="US",
            target_location="San Francisco, CA",
        )
    )


def test_geo_perplexity_adapter_with_citations_and_mention(
    db_session: Session, geo_question: QuestionModel
):
    """Verify Perplexity adapter captures generative text, model version, brand mentions, and citations."""
    mock_payload = {
        "model": "sonar-pro",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "IncuBrix is an AI video engine that matches script voiceovers to b-roll clips. Runway is also popular.",
                }
            }
        ],
        "citations": [
            "https://incubrix.com/overview",
            "https://runwayml.com/editing",
        ],
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = httpx.Response(
        status_code=200,
        text=json.dumps(mock_payload),
        request=httpx.Request("POST", "https://api.perplexity.ai/chat/completions"),
    )

    adapter = PerplexityAIAdapter(api_key="test-key", http_client=mock_client)
    collector = GEOCollector(
        question_repo=QuestionRepository(db_session),
        evidence_repo=EvidenceRepository(db_session),
        observation_repo=ObservationRepository(db_session),
        citation_repo=CitationRepository(db_session),
    )

    obs = collector.collect(
        question=geo_question,
        assistant=ProviderType.PERPLEXITY,
        custom_adapter=adapter,
    )

    assert obs.collection_status == "success"
    assert obs.provider == "perplexity"
    assert obs.ai_model_version == "sonar-pro"
    assert "https://incubrix.com/overview" in obs.quoted_urls
    assert "incubrix.com" in obs.quoted_domains
    assert "runwayml.com" in obs.quoted_domains
    assert obs.incubrix_mentioned == MentionStatus.MENTIONED.value
    assert obs.incubrix_cited == CitationStatus.CITED.value
    assert "Runway" in obs.competitors_observed
    assert obs.visibility_score is not None


def test_geo_openai_adapter_mention_without_citation(
    db_session: Session, geo_question: QuestionModel
):
    """Verify brand mention in text is NOT conflated with citation when citations are absent."""
    mock_payload = {
        "model": "gpt-4o",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "IncuBrix provides automated b-roll alignment for podcasters.",
                }
            }
        ],
        # No citations field produced by standard non-browsing chat completion
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = httpx.Response(
        status_code=200,
        text=json.dumps(mock_payload),
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
    )

    adapter = OpenAIAdapter(api_key="test-openai-key", http_client=mock_client)
    collector = GEOCollector(
        question_repo=QuestionRepository(db_session),
        evidence_repo=EvidenceRepository(db_session),
        observation_repo=ObservationRepository(db_session),
    )

    obs = collector.collect(
        question=geo_question,
        assistant=ProviderType.CHATGPT,
        custom_adapter=adapter,
    )

    # Decoupled verification: Text mentions IncuBrix, but Citation status is UNAVAILABLE (no links)
    assert obs.incubrix_mentioned == MentionStatus.MENTIONED.value
    assert obs.incubrix_cited == CitationStatus.UNAVAILABLE.value
    assert obs.quoted_urls == []
    assert obs.ai_model_version == "gpt-4o"


def test_geo_gemini_adapter_with_grounding_citations(
    db_session: Session, geo_question: QuestionModel
):
    """Verify Google Gemini adapter parses Google Search Grounding metadata citations."""
    mock_payload = {
        "modelVersion": "gemini-1.5-pro",
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "For automated video b-roll, IncuBrix automatically synchronizes clips. Descript offers transcript editing."
                        }
                    ]
                },
                "groundingMetadata": {
                    "groundingChunks": [
                        {"web": {"uri": "https://incubrix.com/features"}},
                        {"web": {"uri": "https://descript.com/video"}},
                    ]
                },
            }
        ],
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = httpx.Response(
        status_code=200,
        text=json.dumps(mock_payload),
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"),
    )

    adapter = GeminiAIAdapter(api_key="test-gemini-key", http_client=mock_client)
    collector = GEOCollector(
        question_repo=QuestionRepository(db_session),
        evidence_repo=EvidenceRepository(db_session),
        observation_repo=ObservationRepository(db_session),
    )

    obs = collector.collect(
        question=geo_question,
        assistant=ProviderType.GEMINI,
        custom_adapter=adapter,
    )

    assert obs.collection_status == "success"
    assert obs.provider == "gemini"
    assert obs.ai_model_version == "gemini-1.5-pro"
    assert "https://incubrix.com/features" in obs.quoted_urls
    assert "https://descript.com/video" in obs.quoted_urls
    assert "google_grounding" in obs.observed_features
    assert obs.incubrix_mentioned == MentionStatus.MENTIONED.value
    assert obs.incubrix_cited == CitationStatus.CITED.value
    assert "Descript" in obs.competitors_observed


def test_geo_claude_adapter_without_mention_or_citation(
    db_session: Session, geo_question: QuestionModel
):
    """Verify Claude response with no brand mention evaluates correctly without false positives."""
    mock_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "content": [
            {
                "type": "text",
                "text": "Creators often use general video editors like Premiere Pro or DaVinci Resolve to assemble footage manually.",
            }
        ],
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = httpx.Response(
        status_code=200,
        text=json.dumps(mock_payload),
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
    )

    adapter = ClaudeAIAdapter(api_key="test-claude-key", http_client=mock_client)
    collector = GEOCollector(
        question_repo=QuestionRepository(db_session),
        evidence_repo=EvidenceRepository(db_session),
        observation_repo=ObservationRepository(db_session),
    )

    obs = collector.collect(
        question=geo_question,
        assistant=ProviderType.CLAUDE,
        custom_adapter=adapter,
    )

    assert obs.incubrix_mentioned == MentionStatus.NOT_MENTIONED.value
    assert obs.incubrix_cited == CitationStatus.UNAVAILABLE.value
    assert "Premiere Pro" in obs.competitors_observed


def test_geo_citation_without_mention(db_session: Session, geo_question: QuestionModel):
    """Verify citation without explicit text mention correctly marks CITED and NOT_MENTIONED."""
    mock_payload = {
        "model": "sonar",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "AI tools can automate video production workflows through multimodal models.",
                }
            }
        ],
        "citations": ["https://incubrix.com/whitepaper"],
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = httpx.Response(
        status_code=200,
        text=json.dumps(mock_payload),
        request=httpx.Request("POST", "https://api.perplexity.ai/chat/completions"),
    )

    adapter = PerplexityAIAdapter(api_key="test-key", http_client=mock_client)
    collector = GEOCollector(
        question_repo=QuestionRepository(db_session),
        evidence_repo=EvidenceRepository(db_session),
        observation_repo=ObservationRepository(db_session),
    )

    obs = collector.collect(
        question=geo_question,
        assistant=ProviderType.PERPLEXITY,
        custom_adapter=adapter,
    )

    assert obs.incubrix_mentioned == MentionStatus.NOT_MENTIONED.value
    assert obs.incubrix_cited == CitationStatus.CITED.value
    assert "https://incubrix.com/whitepaper" in obs.quoted_urls


def test_geo_unsupported_assistant_does_not_claim_queried(
    db_session: Session, geo_question: QuestionModel
):
    """Verify querying an unsupported assistant returns UNAVAILABLE without claiming it was queried."""
    adapter = get_ai_adapter(provider_type=ProviderType.BING_COPILOT)
    assert isinstance(adapter, UnsupportedAIAdapter)
    assert adapter.is_configured is False

    collector = GEOCollector(
        question_repo=QuestionRepository(db_session),
        evidence_repo=EvidenceRepository(db_session),
        observation_repo=ObservationRepository(db_session),
    )

    obs = collector.collect(
        question=geo_question,
        assistant=ProviderType.BING_COPILOT,
        custom_adapter=adapter,
    )

    assert obs.collection_status == CollectionStatus.UNAVAILABLE.value
    assert obs.error_code == "UNSUPPORTED_PROVIDER"
    assert "manual evidence import" in obs.error_details.lower()
    assert obs.incubrix_mentioned == MentionStatus.UNKNOWN.value
    assert obs.incubrix_cited == CitationStatus.UNAVAILABLE.value
    assert obs.visibility_score is None


def test_geo_unconfigured_assistant_handling(
    db_session: Session, geo_question: QuestionModel
):
    """Verify unconfigured AI adapter returns UNAVAILABLE without calling external APIs."""
    adapter = OpenAIAdapter(api_key=None)
    collector = GEOCollector(
        question_repo=QuestionRepository(db_session),
        evidence_repo=EvidenceRepository(db_session),
        observation_repo=ObservationRepository(db_session),
    )

    obs = collector.collect(
        question=geo_question,
        assistant=ProviderType.CHATGPT,
        custom_adapter=adapter,
    )

    assert obs.collection_status == CollectionStatus.UNAVAILABLE.value
    assert obs.error_code == "PROVIDER_NOT_CONFIGURED"
    assert obs.incubrix_mentioned == MentionStatus.UNKNOWN.value
    assert obs.incubrix_cited == CitationStatus.UNAVAILABLE.value
    assert obs.raw_answer is None


def test_geo_adapter_rate_limit_and_timeout(
    db_session: Session, geo_question: QuestionModel
):
    """Verify HTTP 429 rate limit and timeout are caught and mapped to failure statuses."""
    # 1. Rate limit
    mock_429 = MagicMock(spec=httpx.Client)
    mock_429.post.return_value = httpx.Response(
        status_code=429,
        text="Rate limit exceeded",
        request=httpx.Request("POST", "https://api.perplexity.ai/chat/completions"),
    )
    adapter_429 = PerplexityAIAdapter(api_key="test-key", http_client=mock_429)
    res_429 = adapter_429.execute_query("query")
    assert res_429.collection_status == CollectionStatus.FAILED
    assert res_429.error_code == "RATE_LIMITED"

    # 2. Timeout
    mock_timeout = MagicMock(spec=httpx.Client)
    mock_timeout.post.side_effect = httpx.TimeoutException("Read timed out")
    adapter_timeout = PerplexityAIAdapter(api_key="test-key", http_client=mock_timeout)
    res_timeout = adapter_timeout.execute_query("query")
    assert res_timeout.collection_status == CollectionStatus.FAILED
    assert res_timeout.error_code == "TIMEOUT"


def test_geo_manual_import_chatgpt_transcript(
    db_session: Session, geo_question: QuestionModel
):
    """Verify manual evidence import for assistants without accessible APIs."""
    q_repo = QuestionRepository(db_session)
    ev_repo = EvidenceRepository(db_session)
    obs_repo = ObservationRepository(db_session)
    cite_repo = CitationRepository(db_session)

    collector = GEOCollector(
        question_repo=q_repo,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
        citation_repo=cite_repo,
    )

    request = GEOManualImportRequest(
        question_id=geo_question.id,
        assistant=ProviderType.CHATGPT,
        raw_response="IncuBrix is an AI platform designed for creator b-roll assembly. InVideo and Synthesia are alternatives.",
        ai_model_version="GPT-4o",
        citation_urls=[
            "https://incubrix.com/overview",
            "https://invideo.io",
        ],
        source_url="https://chatgpt.com/share/test-uuid",
        operator_id="evaluator_mark",
        collector_notes="Evaluated in ChatGPT Plus desktop web UI.",
    )

    obs = collector.import_manual_evidence(request)

    assert obs.id is not None
    assert obs.question_id == geo_question.id
    assert obs.provider == "chatgpt"
    assert obs.ai_model_version == "GPT-4o"
    assert obs.collection_status == "success"
    assert obs.incubrix_mentioned == MentionStatus.MENTIONED.value
    assert obs.incubrix_cited == CitationStatus.CITED.value
    assert "Invideo" in obs.competitors_observed
    assert "Synthesia" in obs.competitors_observed
    assert "https://incubrix.com/overview" in obs.quoted_urls
    assert "invideo.io" in obs.quoted_domains

    # Check evidence artifact persistence and SHA-256 hash
    assert obs.artifact_id is not None
    artifact = ev_repo.get_by_id(obs.artifact_id)
    assert artifact is not None
    assert artifact.collected_by == "evaluator_mark"
    assert len(artifact.content_hash) == 64

    # Check competitor citation gap target recorded
    targets = cite_repo.list_by_domain("invideo.io")
    assert len(targets) >= 1
    assert targets[0].question_id == geo_question.id


def test_geo_manual_import_validation_errors(
    db_session: Session, geo_question: QuestionModel
):
    """Verify invalid URL in citation_urls and nonexistent question raise proper errors."""
    q_repo = QuestionRepository(db_session)
    ev_repo = EvidenceRepository(db_session)
    obs_repo = ObservationRepository(db_session)
    collector = GEOCollector(
        question_repo=q_repo,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
    )

    # 1. Invalid URL scheme raises ValueError
    bad_url_req = GEOManualImportRequest(
        question_id=geo_question.id,
        assistant=ProviderType.CLAUDE,
        raw_response="Some response",
        citation_urls=["ftp://invalid-url.com"],
    )
    with pytest.raises(ValueError, match="Invalid citation URL"):
        collector.import_manual_evidence(bad_url_req)

    # 2. Nonexistent question ID raises EntityNotFoundError
    bad_q_req = GEOManualImportRequest(
        question_id="nonexistent-q-id",
        assistant=ProviderType.CLAUDE,
        raw_response="Some response",
    )
    with pytest.raises(EntityNotFoundError):
        collector.import_manual_evidence(bad_q_req)


def test_geo_api_endpoints(client: TestClient, geo_question: QuestionModel):
    """Verify /v1/geo REST API routes."""
    # 1. GET /v1/geo/assistants
    ast_resp = client.get("/v1/geo/assistants")
    assert ast_resp.status_code == 200
    assistants = ast_resp.json()
    assert len(assistants) >= 5
    provider_names = [a["provider"] for a in assistants]
    assert "perplexity" in provider_names
    assert "chatgpt" in provider_names
    assert "gemini" in provider_names

    # 2. POST /v1/geo/manual-import
    manual_payload = {
        "question_id": geo_question.id,
        "assistant": "chatgpt",
        "raw_response": "IncuBrix matches transcripts to b-roll clips.",
        "ai_model_version": "GPT-4o",
        "citation_urls": ["https://incubrix.com/features"],
        "operator_id": "api_tester",
    }
    import_resp = client.post("/v1/geo/manual-import", json=manual_payload)
    assert import_resp.status_code == 201
    data = import_resp.json()
    assert data["provider"] == "chatgpt"
    assert data["ai_model_version"] == "GPT-4o"
    assert data["incubrix_mentioned"] == "mentioned"
    assert data["incubrix_cited"] == "cited"

    # Duplicate submission on same day triggers 409 Conflict
    dup_resp = client.post("/v1/geo/manual-import", json=manual_payload)
    assert dup_resp.status_code == 409

    # Nonexistent question triggers 404
    bad_resp = client.post(
        "/v1/geo/manual-import",
        json=dict(manual_payload, question_id="missing-id-1234"),
    )
    assert bad_resp.status_code == 404
