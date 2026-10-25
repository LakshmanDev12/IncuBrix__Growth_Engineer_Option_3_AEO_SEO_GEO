"""Unit tests for Search and AI provider adapters."""

import json
from unittest.mock import MagicMock

import httpx
import pytest

from app.providers.ai_provider import AIProvider
from app.providers.base import ProviderResult
from app.providers.search_provider import SearchProvider
from app.schemas.common import CollectionStatus, ObservationType, ProviderType


def test_search_provider_unconfigured_handling():
    """Verify unconfigured search provider returns UNAVAILABLE without fabricating results."""
    provider = SearchProvider(api_key=None)
    res = provider.execute_query("How to automate video editing?")

    assert res.collection_status == CollectionStatus.UNAVAILABLE
    assert res.error_code == "PROVIDER_NOT_CONFIGURED"
    assert res.provider == ProviderType.GOOGLE_SEARCH
    assert res.raw_answer is None


def test_ai_provider_unconfigured_handling():
    """Verify unconfigured AI provider returns UNAVAILABLE without fabricating results."""
    provider = AIProvider(api_key=None)
    res = provider.execute_query("What is IncuBrix?")

    assert res.collection_status == CollectionStatus.UNAVAILABLE
    assert res.error_code == "PROVIDER_NOT_CONFIGURED"
    assert res.provider == ProviderType.PERPLEXITY
    assert res.raw_answer is None


def test_search_provider_success():
    """Verify successful parsing of Google SERP response with answerBox and organic rankings."""
    mock_payload = {
        "searchParameters": {"q": "best b-roll tools", "gl": "us"},
        "answerBox": {
            "snippet": "IncuBrix automatically analyzes video scripts to generate matched B-roll sequences.",
            "link": "https://incubrix.com/features",
        },
        "organic": [
            {
                "title": "IncuBrix - AI B-Roll Generation",
                "link": "https://incubrix.com",
                "snippet": "Turn your scripts into short videos.",
                "position": 1,
            },
            {
                "title": "Top Video Tools",
                "link": "https://competitor.com/tools",
                "snippet": "Alternative video editing software.",
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
    res = provider.execute_query("best b-roll tools", market="US")

    assert res.collection_status == CollectionStatus.SUCCESS
    assert res.provider == ProviderType.GOOGLE_SEARCH
    assert res.answer_box_present is True
    assert res.rank_position == 1
    assert "incubrix.com" in res.quoted_domains
    assert "competitor.com" in res.quoted_domains
    assert "https://incubrix.com/features" in res.quoted_urls
    assert "https://competitor.com/tools" in res.quoted_urls
    assert "answer_box" in res.observed_features
    assert "organic_results" in res.observed_features
    assert res.raw_answer is not None
    assert "IncuBrix" in res.raw_answer


def test_search_provider_rate_limit_429():
    """Verify HTTP 429 response is handled with RATE_LIMITED error code."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = httpx.Response(
        status_code=429,
        text="Rate limit exceeded",
        request=httpx.Request("POST", "https://google.serper.dev/search"),
    )

    provider = SearchProvider(api_key="test-key", http_client=mock_client)
    res = provider.execute_query("script to b-roll")

    assert res.collection_status == CollectionStatus.FAILED
    assert res.error_code == "RATE_LIMITED"


def test_search_provider_timeout():
    """Verify timeout exception produces TIMEOUT failure status."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = httpx.TimeoutException("Connection timed out")

    provider = SearchProvider(api_key="test-key", http_client=mock_client)
    res = provider.execute_query("script to b-roll")

    assert res.collection_status == CollectionStatus.FAILED
    assert res.error_code == "TIMEOUT"


def test_search_provider_auth_failure_401():
    """Verify HTTP 401 unauthorized response produces AUTHENTICATION_FAILED status."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = httpx.Response(
        status_code=401,
        text="Unauthorized",
        request=httpx.Request("POST", "https://google.serper.dev/search"),
    )

    provider = SearchProvider(api_key="invalid-key", http_client=mock_client)
    res = provider.execute_query("query")

    assert res.collection_status == CollectionStatus.FAILED
    assert res.error_code == "AUTHENTICATION_FAILED"


def test_ai_provider_success():
    """Verify successful parsing of generative AI response with citations."""
    mock_payload = {
        "model": "sonar-pro",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "IncuBrix is an AI platform that matches video scripts to contextual b-roll.",
                }
            }
        ],
        "citations": [
            "https://incubrix.com/about",
            "https://techcrunch.com/article-123",
        ],
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = httpx.Response(
        status_code=200,
        text=json.dumps(mock_payload),
        request=httpx.Request("POST", "https://api.perplexity.ai/chat/completions"),
    )

    provider = AIProvider(api_key="test-ai-key", http_client=mock_client)
    res = provider.execute_query("What is IncuBrix?")

    assert res.collection_status == CollectionStatus.SUCCESS
    assert res.provider == ProviderType.PERPLEXITY
    assert res.observation_type == ObservationType.AI_ASSISTANT
    assert res.raw_answer == "IncuBrix is an AI platform that matches video scripts to contextual b-roll."
    assert "incubrix.com" in res.quoted_domains
    assert "techcrunch.com" in res.quoted_domains
    assert "https://incubrix.com/about" in res.quoted_urls
    assert "generative_synthesis" in res.observed_features
    assert "citations" in res.observed_features
    assert res.ai_model_version == "sonar-pro"


def test_ai_provider_network_error():
    """Verify network connection exception is mapped to NETWORK_ERROR failure."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = httpx.ConnectError("Connection refused")

    provider = AIProvider(api_key="test-key", http_client=mock_client)
    res = provider.execute_query("query")

    assert res.collection_status == CollectionStatus.FAILED
    assert res.error_code == "NETWORK_ERROR"


def test_search_provider_malformed_json():
    """Verify search provider handles non-JSON response gracefully."""
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = httpx.Response(
        status_code=200,
        text="<html><body>Gateway timeout</body></html>",
        request=httpx.Request("POST", "https://google.serper.dev/search"),
    )

    provider = SearchProvider(api_key="test-key", http_client=mock_client)
    res = provider.execute_query("query")

    assert res.collection_status == CollectionStatus.FAILED
    assert res.error_code == "INVALID_RESPONSE_JSON"


def test_ai_provider_rate_limit_and_timeout():
    """Verify AI provider handles HTTP 429 rate limit and timeout."""
    mock_client_429 = MagicMock(spec=httpx.Client)
    mock_client_429.post.return_value = httpx.Response(
        status_code=429,
        text="Rate limited",
        request=httpx.Request("POST", "https://api.perplexity.ai/chat/completions"),
    )
    p_429 = AIProvider(api_key="test-key", http_client=mock_client_429)
    res_429 = p_429.execute_query("query")
    assert res_429.collection_status == CollectionStatus.FAILED
    assert res_429.error_code == "RATE_LIMITED"

    mock_client_timeout = MagicMock(spec=httpx.Client)
    mock_client_timeout.post.side_effect = httpx.TimeoutException("AI timeout")
    p_timeout = AIProvider(api_key="test-key", http_client=mock_client_timeout)
    res_timeout = p_timeout.execute_query("query")
    assert res_timeout.collection_status == CollectionStatus.FAILED
    assert res_timeout.error_code == "TIMEOUT"

