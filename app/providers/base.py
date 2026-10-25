"""Abstract provider specifications for search engines and AI assistants."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.schemas.common import CollectionStatus, ObservationType, ProviderType


@dataclass
class ProviderResult:
    """Standardized response container returned by all search and AI providers."""

    provider: ProviderType
    observation_type: ObservationType
    query: str
    market: str = "US"
    location: Optional[str] = None
    collection_status: CollectionStatus = CollectionStatus.SUCCESS

    # Raw response body or formatted dump for evidence preservation
    raw_payload: Optional[str] = None
    source_url: Optional[str] = None

    # Observed metrics
    raw_answer: Optional[str] = None
    rank_position: Optional[int] = None
    answer_box_present: Optional[bool] = None
    quoted_domains: List[str] = field(default_factory=list)
    quoted_urls: List[str] = field(default_factory=list)
    observed_features: List[str] = field(default_factory=list)
    ai_model_version: Optional[str] = None

    # Diagnostics and errors
    error_code: Optional[str] = None
    error_details: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


class BaseProvider(ABC):
    """Abstract interface for external search and AI assistant platforms.

    All implementations must gracefully handle timeouts, rate limits, and unconfigured states.
    Never fabricate results or claim an external provider was queried when it was not.
    """

    provider_type: ProviderType
    observation_type: ObservationType

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}

    @property
    def is_configured(self) -> bool:
        """Check whether provider API credentials and endpoints are configured."""
        return False

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return provider capability metadata."""
        pass

    @abstractmethod
    def execute_query(
        self,
        query: str,
        market: str = "US",
        location: Optional[str] = None,
    ) -> ProviderResult:
        """Execute a search query or prompt against the provider."""
        pass


class BaseAIProvider(BaseProvider):
    """Abstract interface specifically for generative AI assistants and answer engines.

    Provides common configuration attributes (API keys, URLs, model identifiers) and
    standardizes prompt dispatch and generative answer/citation parsing.
    Never fabricates responses or claims an assistant was queried when unconfigured.
    """

    observation_type: ObservationType = ObservationType.AI_ASSISTANT

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        provider_type: Optional[ProviderType] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(config)
        self.api_key = api_key or self.config.get("api_key")
        self.api_url = api_url or self.config.get("api_url")
        self.model = model or self.config.get("model")
        self.timeout_seconds = timeout_seconds or 10.0
        if provider_type:
            self.provider_type = provider_type

    @property
    def is_configured(self) -> bool:
        """Check whether AI provider credentials and endpoint are configured."""
        return bool(self.api_key)

    def get_capabilities(self) -> Dict[str, Any]:
        """Return AI provider capabilities."""
        return {
            "provider": self.provider_type.value,
            "observation_type": self.observation_type.value,
            "supports_citations": True,
            "supports_generative_synthesis": True,
            "model": self.model,
            "is_configured": self.is_configured,
        }

