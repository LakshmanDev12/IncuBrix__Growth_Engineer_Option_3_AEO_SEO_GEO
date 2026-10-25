"""AI Assistant and Generative Search Engine (GEO) Provider Adapters.

Supports:
- Shared BaseAIProvider interface.
- Independent adapters for configured, permitted APIs:
  * Perplexity AI (Sonar / Sonar Pro with direct citations)
  * OpenAI / ChatGPT (GPT-4o with generative synthesis)
  * Google Gemini (Gemini 1.5 Pro with Google Search Grounding)
  * Anthropic Claude (Claude 3.5 Sonnet)
  * Google AI Overview (Hybrid Overview with linked citations)
- Unsupported / unconfigured assistant handling without fabricating data or claiming queries occurred.
- Full provenance tracking with model version, quoted source URLs, raw responses, and error telemetry.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.engine.normalizer import extract_domain
from app.providers.base import BaseAIProvider, BaseProvider, ProviderResult
from app.schemas.common import CollectionStatus, ObservationType, ProviderType


class PerplexityAIAdapter(BaseAIProvider):
    """Generative AI assistant provider using Perplexity AI API."""

    provider_type: ProviderType = ProviderType.PERPLEXITY
    observation_type: ObservationType = ObservationType.AI_ASSISTANT

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        settings = get_settings()
        super().__init__(
            api_key=api_key or settings.ai_provider_api_key,
            api_url=api_url or settings.ai_provider_api_url or "https://api.perplexity.ai/chat/completions",
            model=model or settings.ai_provider_model or "sonar",
            timeout_seconds=timeout_seconds or settings.http_request_timeout_seconds,
            provider_type=self.provider_type,
            config=config,
        )
        self._http_client = http_client

    def execute_query(
        self,
        query: str,
        market: str = "US",
        location: Optional[str] = None,
    ) -> ProviderResult:
        """Query Perplexity API for creator question visibility and citations."""
        if not self.is_configured:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.UNAVAILABLE,
                error_code="PROVIDER_NOT_CONFIGURED",
                error_details="Perplexity AI provider API key is not configured. Live AI queries are prohibited without explicit credentials.",
                meta={"is_configured": False},
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        system_prompt = (
            f"You are a helpful search assistant. Answer the user's question clearly for a user in {market}. "
            f"{f'Location: {location}.' if location else ''} Include factual citations where applicable."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            "temperature": 0.2,
        }

        client = self._http_client or httpx.Client(timeout=self.timeout_seconds)
        try:
            resp = client.post(self.api_url, json=payload, headers=headers)

            if resp.status_code == 429:
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code="RATE_LIMITED",
                    error_details="HTTP 429: Rate limit exceeded on Perplexity AI provider API.",
                )

            if resp.status_code in (401, 403):
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code="AUTHENTICATION_FAILED",
                    error_details=f"HTTP {resp.status_code}: Invalid or unauthorized Perplexity API key.",
                )

            if not resp.is_success:
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code=f"HTTP_{resp.status_code}",
                    error_details=f"Perplexity returned error: {resp.text[:300]}",
                )

            raw_text = resp.text
            try:
                data = resp.json()
            except Exception:
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    raw_payload=raw_text,
                    error_code="INVALID_RESPONSE_JSON",
                    error_details="Perplexity response was not valid JSON.",
                )

        except httpx.TimeoutException:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.FAILED,
                error_code="TIMEOUT",
                error_details=f"Perplexity request timed out after {self.timeout_seconds}s.",
            )
        except Exception as exc:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.FAILED,
                error_code="NETWORK_ERROR",
                error_details=f"Perplexity connection failure: {str(exc)}",
            )
        finally:
            if not self._http_client:
                client.close()

        choices = data.get("choices", [])
        answer_text = ""
        if choices:
            msg = choices[0].get("message", {})
            answer_text = msg.get("content", "")

        citations = data.get("citations", [])
        quoted_domains = []
        quoted_urls = []
        for cite in citations:
            if isinstance(cite, str) and cite.strip():
                clean_cite = cite.strip()
                quoted_urls.append(clean_cite)
                d = extract_domain(clean_cite)
                if d:
                    quoted_domains.append(d)

        observed_features = ["generative_synthesis"]
        if citations:
            observed_features.append("citations")
        if answer_text:
            observed_features.append("direct_answer")

        return ProviderResult(
            provider=self.provider_type,
            observation_type=self.observation_type,
            query=query,
            market=market,
            location=location,
            collection_status=CollectionStatus.SUCCESS,
            raw_payload=raw_text,
            raw_answer=answer_text or None,
            rank_position=None,
            answer_box_present=None,
            quoted_domains=sorted(list(set(quoted_domains))),
            quoted_urls=sorted(list(set(quoted_urls))),
            observed_features=observed_features,
            ai_model_version=data.get("model", self.model),
            meta={
                "citations_count": len(citations),
                "citations": citations,
                "observed_features": observed_features,
            },
        )


class OpenAIAdapter(BaseAIProvider):
    """OpenAI / ChatGPT generative assistant adapter."""

    provider_type: ProviderType = ProviderType.CHATGPT
    observation_type: ObservationType = ObservationType.AI_ASSISTANT

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        settings = get_settings()
        super().__init__(
            api_key=api_key or settings.openai_api_key,
            api_url=api_url or settings.openai_api_url or "https://api.openai.com/v1/chat/completions",
            model=model or settings.openai_model or "gpt-4o",
            timeout_seconds=timeout_seconds or settings.http_request_timeout_seconds,
            provider_type=self.provider_type,
            config=config,
        )
        self._http_client = http_client

    def execute_query(
        self,
        query: str,
        market: str = "US",
        location: Optional[str] = None,
    ) -> ProviderResult:
        """Query OpenAI API with creator question prompt."""
        if not self.is_configured:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.UNAVAILABLE,
                error_code="PROVIDER_NOT_CONFIGURED",
                error_details="OpenAI / ChatGPT provider API key is not configured. Live queries are prohibited without explicit credentials.",
                meta={"is_configured": False},
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a helpful search assistant for creators in {market}. Answer clearly and concisely.",
                },
                {"role": "user", "content": query},
            ],
            "temperature": 0.2,
        }

        client = self._http_client or httpx.Client(timeout=self.timeout_seconds)
        try:
            resp = client.post(self.api_url, json=payload, headers=headers)

            if resp.status_code == 429:
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code="RATE_LIMITED",
                    error_details="HTTP 429: Rate limit exceeded on OpenAI API.",
                )

            if resp.status_code in (401, 403):
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code="AUTHENTICATION_FAILED",
                    error_details=f"HTTP {resp.status_code}: Invalid or unauthorized OpenAI API key.",
                )

            if not resp.is_success:
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code=f"HTTP_{resp.status_code}",
                    error_details=f"OpenAI returned error: {resp.text[:300]}",
                )

            raw_text = resp.text
            data = resp.json()

        except httpx.TimeoutException:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.FAILED,
                error_code="TIMEOUT",
                error_details=f"OpenAI request timed out after {self.timeout_seconds}s.",
            )
        except Exception as exc:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.FAILED,
                error_code="NETWORK_ERROR",
                error_details=f"OpenAI connection failure: {str(exc)}",
            )
        finally:
            if not self._http_client:
                client.close()

        choices = data.get("choices", [])
        answer_text = ""
        if choices:
            msg = choices[0].get("message", {})
            answer_text = msg.get("content", "")

        citations = data.get("citations", [])
        quoted_domains = []
        quoted_urls = []
        for cite in citations:
            if isinstance(cite, str) and cite.strip():
                clean_cite = cite.strip()
                quoted_urls.append(clean_cite)
                d = extract_domain(clean_cite)
                if d:
                    quoted_domains.append(d)

        observed_features = ["generative_synthesis"]
        if citations:
            observed_features.append("citations")
        if answer_text:
            observed_features.append("direct_answer")

        return ProviderResult(
            provider=self.provider_type,
            observation_type=self.observation_type,
            query=query,
            market=market,
            location=location,
            collection_status=CollectionStatus.SUCCESS,
            raw_payload=raw_text,
            raw_answer=answer_text or None,
            rank_position=None,
            answer_box_present=None,
            quoted_domains=sorted(list(set(quoted_domains))),
            quoted_urls=sorted(list(set(quoted_urls))),
            observed_features=observed_features,
            ai_model_version=data.get("model", self.model),
            meta={"citations": citations, "observed_features": observed_features},
        )


class GeminiAIAdapter(BaseAIProvider):
    """Google Gemini generative assistant adapter with Search Grounding."""

    provider_type: ProviderType = ProviderType.GEMINI
    observation_type: ObservationType = ObservationType.AI_ASSISTANT

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        settings = get_settings()
        super().__init__(
            api_key=api_key or settings.gemini_api_key,
            api_url=api_url or settings.gemini_api_url or "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
            model=model or settings.gemini_model or "gemini-1.5-pro",
            timeout_seconds=timeout_seconds or settings.http_request_timeout_seconds,
            provider_type=self.provider_type,
            config=config,
        )
        self._http_client = http_client

    def execute_query(
        self,
        query: str,
        market: str = "US",
        location: Optional[str] = None,
    ) -> ProviderResult:
        """Query Gemini API with Search Grounding enabled."""
        if not self.is_configured:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.UNAVAILABLE,
                error_code="PROVIDER_NOT_CONFIGURED",
                error_details="Google Gemini provider API key is not configured. Live queries are prohibited without explicit credentials.",
                meta={"is_configured": False},
            )

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"Answer the following creator question clearly for a user in {market}. Include factual sources: {query}"
                        }
                    ]
                }
            ],
            "tools": [{"google_search": {}}],
        }

        client = self._http_client or httpx.Client(timeout=self.timeout_seconds)
        try:
            resp = client.post(self.api_url, json=payload, headers=headers)

            if resp.status_code == 429:
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code="RATE_LIMITED",
                    error_details="HTTP 429: Rate limit exceeded on Google Gemini API.",
                )

            if resp.status_code in (401, 403):
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code="AUTHENTICATION_FAILED",
                    error_details=f"HTTP {resp.status_code}: Invalid or unauthorized Gemini API key.",
                )

            if not resp.is_success:
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code=f"HTTP_{resp.status_code}",
                    error_details=f"Gemini returned error: {resp.text[:300]}",
                )

            raw_text = resp.text
            data = resp.json()

        except httpx.TimeoutException:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.FAILED,
                error_code="TIMEOUT",
                error_details=f"Gemini request timed out after {self.timeout_seconds}s.",
            )
        except Exception as exc:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.FAILED,
                error_code="NETWORK_ERROR",
                error_details=f"Gemini connection failure: {str(exc)}",
            )
        finally:
            if not self._http_client:
                client.close()

        candidates = data.get("candidates", [])
        answer_text = ""
        quoted_urls = []
        quoted_domains = []

        if candidates:
            cand = candidates[0]
            parts = cand.get("content", {}).get("parts", [])
            if parts:
                answer_text = parts[0].get("text", "")

            # Extract Google Search Grounding URLs
            grounding = cand.get("groundingMetadata", {})
            chunks = grounding.get("groundingChunks", [])
            for chunk in chunks:
                web_uri = chunk.get("web", {}).get("uri")
                if web_uri and isinstance(web_uri, str):
                    quoted_urls.append(web_uri)
                    d = extract_domain(web_uri)
                    if d:
                        quoted_domains.append(d)

        observed_features = ["generative_synthesis"]
        if quoted_urls:
            observed_features.append("citations")
            observed_features.append("google_grounding")
        if answer_text:
            observed_features.append("direct_answer")

        return ProviderResult(
            provider=self.provider_type,
            observation_type=self.observation_type,
            query=query,
            market=market,
            location=location,
            collection_status=CollectionStatus.SUCCESS,
            raw_payload=raw_text,
            raw_answer=answer_text or None,
            rank_position=None,
            answer_box_present=None,
            quoted_domains=sorted(list(set(quoted_domains))),
            quoted_urls=sorted(list(set(quoted_urls))),
            observed_features=observed_features,
            ai_model_version=data.get("modelVersion", self.model),
            meta={"quoted_urls": quoted_urls, "observed_features": observed_features},
        )


class ClaudeAIAdapter(BaseAIProvider):
    """Anthropic Claude generative assistant adapter."""

    provider_type: ProviderType = ProviderType.CLAUDE
    observation_type: ObservationType = ObservationType.AI_ASSISTANT

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        settings = get_settings()
        super().__init__(
            api_key=api_key or settings.claude_api_key,
            api_url=api_url or settings.claude_api_url or "https://api.anthropic.com/v1/messages",
            model=model or settings.claude_model or "claude-3-5-sonnet-20241022",
            timeout_seconds=timeout_seconds or settings.http_request_timeout_seconds,
            provider_type=self.provider_type,
            config=config,
        )
        self._http_client = http_client

    def execute_query(
        self,
        query: str,
        market: str = "US",
        location: Optional[str] = None,
    ) -> ProviderResult:
        """Query Anthropic Claude API."""
        if not self.is_configured:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.UNAVAILABLE,
                error_code="PROVIDER_NOT_CONFIGURED",
                error_details="Anthropic Claude provider API key is not configured. Live queries are prohibited without explicit credentials.",
                meta={"is_configured": False},
            )

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": query}],
        }

        client = self._http_client or httpx.Client(timeout=self.timeout_seconds)
        try:
            resp = client.post(self.api_url, json=payload, headers=headers)

            if resp.status_code == 429:
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code="RATE_LIMITED",
                    error_details="HTTP 429: Rate limit exceeded on Anthropic Claude API.",
                )

            if resp.status_code in (401, 403):
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code="AUTHENTICATION_FAILED",
                    error_details=f"HTTP {resp.status_code}: Invalid or unauthorized Claude API key.",
                )

            if not resp.is_success:
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code=f"HTTP_{resp.status_code}",
                    error_details=f"Claude returned error: {resp.text[:300]}",
                )

            raw_text = resp.text
            data = resp.json()

        except httpx.TimeoutException:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.FAILED,
                error_code="TIMEOUT",
                error_details=f"Claude request timed out after {self.timeout_seconds}s.",
            )
        except Exception as exc:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.FAILED,
                error_code="NETWORK_ERROR",
                error_details=f"Claude connection failure: {str(exc)}",
            )
        finally:
            if not self._http_client:
                client.close()

        content = data.get("content", [])
        answer_text = ""
        if content and isinstance(content, list):
            for block in content:
                if block.get("type") == "text":
                    answer_text += block.get("text", "")

        return ProviderResult(
            provider=self.provider_type,
            observation_type=self.observation_type,
            query=query,
            market=market,
            location=location,
            collection_status=CollectionStatus.SUCCESS,
            raw_payload=raw_text,
            raw_answer=answer_text or None,
            rank_position=None,
            answer_box_present=None,
            quoted_domains=[],
            quoted_urls=[],
            observed_features=["generative_synthesis", "direct_answer"] if answer_text else ["generative_synthesis"],
            ai_model_version=data.get("model", self.model),
            meta={"model": data.get("model", self.model)},
        )


class GoogleAIOverviewAdapter(BaseAIProvider):
    """Google AI Overview (Hybrid Overview) SERP adapter."""

    provider_type: ProviderType = ProviderType.GOOGLE_AI_OVERVIEW
    observation_type: ObservationType = ObservationType.HYBRID_OVERVIEW

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        settings = get_settings()
        super().__init__(
            api_key=api_key or settings.serp_api_key,
            api_url=api_url or settings.serp_api_url or "https://google.serper.dev/search",
            model="google_ai_overview",
            timeout_seconds=timeout_seconds or settings.http_request_timeout_seconds,
            provider_type=self.provider_type,
            config=config,
        )
        self._http_client = http_client

    def execute_query(
        self,
        query: str,
        market: str = "US",
        location: Optional[str] = None,
    ) -> ProviderResult:
        """Query Google SERP for AI Overview presence."""
        if not self.is_configured:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.UNAVAILABLE,
                error_code="PROVIDER_NOT_CONFIGURED",
                error_details="Google AI Overview API key is not configured.",
                meta={"is_configured": False},
            )

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "gl": market.lower()}
        if location:
            payload["location"] = location

        client = self._http_client or httpx.Client(timeout=self.timeout_seconds)
        try:
            resp = client.post(self.api_url, json=payload, headers=headers)
            if not resp.is_success:
                return ProviderResult(
                    provider=self.provider_type,
                    observation_type=self.observation_type,
                    query=query,
                    market=market,
                    location=location,
                    collection_status=CollectionStatus.FAILED,
                    error_code=f"HTTP_{resp.status_code}",
                    error_details=f"SERP returned error: {resp.text[:200]}",
                )
            raw_text = resp.text
            data = resp.json()
        except Exception as exc:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.FAILED,
                error_code="NETWORK_ERROR",
                error_details=str(exc),
            )
        finally:
            if not self._http_client:
                client.close()

        # Extract AI overview or answerBox
        ai_overview = data.get("aiOverview") or data.get("answerBox", {})
        has_ai_overview = bool(ai_overview)
        answer_text = ""
        quoted_urls = []
        quoted_domains = []

        if has_ai_overview:
            answer_text = ai_overview.get("snippet") or ai_overview.get("answer") or ""
            link = ai_overview.get("link")
            if link:
                quoted_urls.append(link)
                d = extract_domain(link)
                if d:
                    quoted_domains.append(d)

        return ProviderResult(
            provider=self.provider_type,
            observation_type=self.observation_type,
            query=query,
            market=market,
            location=location,
            collection_status=CollectionStatus.SUCCESS if has_ai_overview else CollectionStatus.PARTIAL,
            raw_payload=raw_text,
            raw_answer=answer_text or None,
            rank_position=1 if has_ai_overview else None,
            answer_box_present=has_ai_overview,
            quoted_domains=sorted(list(set(quoted_domains))),
            quoted_urls=sorted(list(set(quoted_urls))),
            observed_features=["google_ai_overview"] if has_ai_overview else [],
            ai_model_version="google_sge",
            meta={"has_ai_overview": has_ai_overview},
        )


class UnsupportedAIAdapter(BaseAIProvider):
    """Fallback adapter for assistants without an accessible automated API.

    Guarantees the system never falsely claims unsupported assistants were queried.
    """

    def __init__(self, provider_type: ProviderType) -> None:
        super().__init__(provider_type=provider_type)

    @property
    def is_configured(self) -> bool:
        return False

    def execute_query(
        self,
        query: str,
        market: str = "US",
        location: Optional[str] = None,
    ) -> ProviderResult:
        """Return explicit UNAVAILABLE status without claiming queries occurred."""
        return ProviderResult(
            provider=self.provider_type,
            observation_type=self.observation_type,
            query=query,
            market=market,
            location=location,
            collection_status=CollectionStatus.UNAVAILABLE,
            error_code="UNSUPPORTED_PROVIDER",
            error_details=f"Assistant '{self.provider_type.value}' does not have an automated API adapter configured. Use manual evidence import instead.",
            meta={"is_configured": False},
        )


def get_ai_adapter(
    provider_type: ProviderType,
    api_key: Optional[str] = None,
    api_url: Optional[str] = None,
    model: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
    http_client: Optional[httpx.Client] = None,
) -> BaseAIProvider:
    """Factory returning the appropriate AI provider adapter for the requested assistant type."""
    if provider_type == ProviderType.PERPLEXITY:
        return PerplexityAIAdapter(
            api_key=api_key,
            api_url=api_url,
            model=model,
            timeout_seconds=timeout_seconds,
            http_client=http_client,
        )
    if provider_type == ProviderType.CHATGPT:
        return OpenAIAdapter(
            api_key=api_key,
            api_url=api_url,
            model=model,
            timeout_seconds=timeout_seconds,
            http_client=http_client,
        )
    if provider_type == ProviderType.GEMINI:
        return GeminiAIAdapter(
            api_key=api_key,
            api_url=api_url,
            model=model,
            timeout_seconds=timeout_seconds,
            http_client=http_client,
        )
    if provider_type == ProviderType.CLAUDE:
        return ClaudeAIAdapter(
            api_key=api_key,
            api_url=api_url,
            model=model,
            timeout_seconds=timeout_seconds,
            http_client=http_client,
        )
    if provider_type == ProviderType.GOOGLE_AI_OVERVIEW:
        return GoogleAIOverviewAdapter(
            api_key=api_key,
            api_url=api_url,
            timeout_seconds=timeout_seconds,
            http_client=http_client,
        )

    # For any assistant without an accessible automated API (e.g. BING_COPILOT, OTHER)
    return UnsupportedAIAdapter(provider_type=provider_type)


# Backward-compatibility alias
AIProvider = PerplexityAIAdapter
