"""Search Engine Provider adapter for organic Google SERP observation.

Supports featured snippet extraction, organic rank tracking, and domain mapping.
Gracefully handles missing credentials, timeouts, and rate limits without fabricating results.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings
from app.engine.normalizer import extract_domain
from app.providers.base import BaseProvider, ProviderResult
from app.schemas.common import CollectionStatus, ObservationType, ProviderType


_UNSET = object()


class SearchProvider(BaseProvider):
    """Search Engine observation provider using SERP API endpoints."""

    provider_type: ProviderType = ProviderType.GOOGLE_SEARCH
    observation_type: ObservationType = ObservationType.SEARCH_ENGINE

    def __init__(
        self,
        api_key: Any = _UNSET,
        api_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        http_client: Optional[httpx.Client] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(config)
        settings = get_settings()
        if api_key is _UNSET:
            self.api_key = self.config.get("api_key") or settings.serp_api_key
        else:
            self.api_key = api_key
        self.api_url = api_url or self.config.get(
            "api_url", settings.serp_api_url or "https://google.serper.dev/search"
        )
        self.timeout_seconds = timeout_seconds or settings.http_request_timeout_seconds
        self._http_client = http_client

    @property
    def is_configured(self) -> bool:
        """Check whether search provider API key is configured."""
        return bool(self.api_key)

    def get_capabilities(self) -> Dict[str, Any]:
        """Return search provider capabilities."""
        return {
            "provider": self.provider_type.value,
            "supports_organic_rank": True,
            "supports_answer_box": True,
            "supports_location_geo": True,
            "is_configured": self.is_configured,
        }

    def execute_query(
        self,
        query: str,
        market: str = "US",
        location: Optional[str] = None,
    ) -> ProviderResult:
        """Query Google SERP for creator question visibility."""
        # 1. Check configuration
        if not self.is_configured:
            return ProviderResult(
                provider=self.provider_type,
                observation_type=self.observation_type,
                query=query,
                market=market,
                location=location,
                collection_status=CollectionStatus.UNAVAILABLE,
                error_code="PROVIDER_NOT_CONFIGURED",
                error_details="Search provider API key is not configured. Live search queries are prohibited without explicit credentials.",
                meta={"is_configured": False},
            )

        payload = {
            "q": query,
            "gl": market.lower(),
        }
        if location:
            payload["location"] = location

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        # 2. Execute HTTP request
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
                    error_details="HTTP 429: Rate limit exceeded on search provider API.",
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
                    error_details=f"HTTP {resp.status_code}: Invalid or unauthorized API key.",
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
                    error_details=f"Provider returned error response: {resp.text[:300]}",
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
                    error_details="Provider response was not valid JSON.",
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
                error_details=f"Search request timed out after {self.timeout_seconds}s.",
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
                error_details=f"Connection failure: {str(exc)}",
            )
        finally:
            if not self._http_client:
                client.close()

        # 3. Parse SERP results
        answer_box = data.get("answerBox")
        has_answer_box = bool(answer_box)
        organic_results: List[Dict[str, Any]] = data.get("organic", [])

        quoted_domains: List[str] = []
        quoted_urls: List[str] = []
        observed_features: List[str] = []
        snippets: List[str] = []
        rank_position: Optional[int] = None
        settings = get_settings()

        if has_answer_box:
            observed_features.extend(["answer_box", "featured_snippet"])
            ans_snippet = answer_box.get("snippet") or answer_box.get("answer") or ""
            if ans_snippet:
                snippets.append(ans_snippet)
            ans_link = answer_box.get("link")
            if ans_link:
                quoted_urls.append(ans_link)
                ans_domain = extract_domain(ans_link)
                if ans_domain:
                    quoted_domains.append(ans_domain)
                    if any(bd in ans_domain for bd in settings.incubrix_domains):
                        rank_position = 1

        if organic_results:
            observed_features.append("organic_results")

        if data.get("knowledgeGraph"):
            observed_features.append("knowledge_graph")

        if data.get("peopleAlsoAsk"):
            observed_features.append("people_also_ask")

        for idx, item in enumerate(organic_results, start=1):
            link = item.get("link", "")
            if link:
                quoted_urls.append(link)
                domain = extract_domain(link)
                if domain:
                    quoted_domains.append(domain)
                    # Check if tracked brand is found at this organic rank position
                    if rank_position is None and any(bd in domain for bd in settings.incubrix_domains):
                        rank_position = idx

            snippet = item.get("snippet") or item.get("title") or ""
            if snippet:
                snippets.append(snippet)

        raw_combined = " \n".join(snippets[:5]) if snippets else None

        return ProviderResult(
            provider=self.provider_type,
            observation_type=self.observation_type,
            query=query,
            market=market,
            location=location,
            collection_status=CollectionStatus.SUCCESS,
            raw_payload=raw_text,
            source_url=data.get("searchParameters", {}).get("url"),
            raw_answer=raw_combined,
            rank_position=rank_position,
            answer_box_present=has_answer_box,
            quoted_domains=sorted(list(set(quoted_domains))),
            quoted_urls=sorted(list(set(quoted_urls))),
            observed_features=observed_features,
            meta={
                "organic_count": len(organic_results),
                "has_answer_box": has_answer_box,
                "observed_features": observed_features,
            },
        )
