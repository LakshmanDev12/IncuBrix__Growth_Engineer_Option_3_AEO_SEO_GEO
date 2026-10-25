"""Schemas for Visibility Observations (Search Engine, AI Assistant, and Hybrid Overviews).

Strictly adheres to:
1. Every visibility observation must support:
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
2. Nullable fields and explicit unknown/unavailable states. Never treat missing evidence as a negative result.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.schemas.common import (
    CitationStatus,
    CollectionStatus,
    MentionStatus,
    ObservationType,
    ProviderType,
)


class ObservationBase(BaseModel):
    """Core visibility observation properties across search engines and AI assistants."""

    question_id: str = Field(
        ...,
        description="Associated Creator Question ID.",
    )
    market: str = Field(
        default="US",
        min_length=2,
        max_length=50,
        description="Search/observation market context.",
    )
    location: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Specific geographic location setting (city, region). Nullable if not specified.",
    )
    measured_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the observation was measured or captured.",
    )
    provider: ProviderType = Field(
        default=ProviderType.OTHER,
        description="Search engine or AI assistant platform provider.",
    )
    observation_type: ObservationType = Field(
        default=ObservationType.UNKNOWN,
        description="Category of observation (search_engine, ai_assistant, hybrid_overview).",
    )

    # Raw content and/or artifact reference (nullable if fetch failed or stored externally)
    raw_answer: Optional[str] = Field(
        default=None,
        max_length=50000,
        description="Observed text response or snippet. Nullable if absent.",
    )
    artifact_id: Optional[str] = Field(
        default=None,
        description="Reference identifier to an externally stored EvidenceArtifact.",
    )

    # Explicit tri-state / unknown visibility statuses (NEVER assume missing = negative)
    incubrix_mentioned: MentionStatus = Field(
        default=MentionStatus.UNKNOWN,
        description="Explicit mention status. Defaults to UNKNOWN; never assumed False.",
    )
    incubrix_cited: CitationStatus = Field(
        default=CitationStatus.UNKNOWN,
        description="Explicit citation/link status. Defaults to UNKNOWN; never assumed False.",
    )

    # Competitors and quoted domain evidence
    competitors_observed: List[str] = Field(
        default_factory=list,
        description="List of competitor brand or tool names detected in the observation.",
    )
    quoted_domains: List[str] = Field(
        default_factory=list,
        description="Domains referenced, cited, or linked in the result.",
    )
    quoted_urls: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("quoted_urls", "quoted_source_urls"),
        description="Specific source URLs quoted, cited, or linked in the observation.",
    )
    observed_features: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("observed_features", "answer_features"),
        description="Observed answer features (e.g., answer_box, featured_snippet, organic_results, ai_overview, citations).",
    )
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="List of associated evidence artifact IDs.",
    )

    # Search & AI specific metrics (strictly nullable for explicit unavailable states)
    rank_position: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Organic search rank position (1-100) if applicable; null for AI/unranked.",
    )
    answer_box_present: Optional[bool] = Field(
        default=None,
        description="Whether a SERP featured snippet / answer box was present. Null if not applicable/unknown.",
    )
    ai_model_version: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Underlying AI model version if applicable (e.g. GPT-4o, Claude 3.5 Sonnet).",
    )

    # Collection status & error tracing
    collection_status: CollectionStatus = Field(
        default=CollectionStatus.SUCCESS,
        description="Status of the collection run.",
    )
    error_code: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Standardized error code if collection or parsing failed.",
    )
    error_details: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Detailed diagnostic or error message if collection encountered issues.",
    )

    meta: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("meta", "metadata"),
        serialization_alias="metadata",
        description="Additional structured collector metadata.",
    )

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ObservationCreate(ObservationBase):
    """Payload to record a visibility observation."""

    def compute_fingerprint(self) -> str:
        """Generate deduplication fingerprint based on observation identity parameters."""
        date_str = self.measured_at.strftime("%Y-%m-%d")
        raw = f"{self.question_id}:{self.provider.value}:{self.market}:{self.location or ''}:{date_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ObservationRead(ObservationBase):
    """Serialized visibility observation including calculated score and database identity."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    fingerprint: str = Field(
        description="Unique deterministic fingerprint to prevent duplicate observations on the same day."
    )
    visibility_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Calculated visibility heuristic score (0-100). None if data is incomplete.",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ManualEvidenceImportRequest(BaseModel):
    """Payload for operator-provided manual evidence observation import."""

    question_id: str = Field(
        ...,
        description="ID of the creator question to attach evidence to.",
    )
    raw_evidence: str = Field(
        ...,
        min_length=1,
        description="Raw text, HTML dump, or JSON snapshot observed by the operator.",
    )
    provider: ProviderType = Field(
        default=ProviderType.OTHER,
        description="Search engine or AI platform provider where evidence was captured.",
    )
    observation_type: ObservationType = Field(
        default=ObservationType.SEARCH_ENGINE,
        description="Category of observation.",
    )
    market: Optional[str] = Field(
        default=None,
        description="Target market code (e.g. US, UK). If omitted, inherits from the question.",
    )
    location: Optional[str] = Field(
        default=None,
        description="Geographic location setting (e.g. city, region).",
    )
    measured_at: Optional[datetime] = Field(
        default=None,
        description="Measurement timestamp. Defaults to current UTC timestamp.",
    )
    rank_position: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Observed organic ranking position (1-100) if applicable.",
    )
    raw_answer: Optional[str] = Field(
        default=None,
        description="Extracted answer snippet or text response summary.",
    )
    observed_features: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("observed_features", "answer_features"),
        description="Features observed in the answer (e.g. answer_box, featured_snippet, ai_overview, citations).",
    )
    quoted_source_urls: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("quoted_source_urls", "quoted_urls"),
        description="List of specific URLs quoted, cited, or linked in the evidence.",
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Public URL of the search or assistant page where evidence was gathered.",
    )
    incubrix_mentioned: Optional[MentionStatus] = Field(
        default=None,
        description="Explicit mention status override. Analyzed automatically from text if omitted.",
    )
    incubrix_cited: Optional[CitationStatus] = Field(
        default=None,
        description="Explicit citation status override. Analyzed automatically from URLs if omitted.",
    )
    competitors_observed: Optional[List[str]] = Field(
        default=None,
        description="Explicit list of competitor brands detected. Auto-detected if omitted.",
    )
    collector_notes: Optional[str] = Field(
        default=None,
        description="Operator notes describing observation context.",
    )
    operator_id: str = Field(
        default="manual_operator",
        description="Identifier of operator or researcher submitting evidence.",
    )
    ai_model_version: Optional[str] = Field(
        default=None,
        description="Underlying AI model version if applicable.",
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured metadata.",
    )

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class GEOManualImportRequest(BaseModel):
    """Payload for manual import of generative AI assistant observations (GEO).

    Tailored specifically for assistants without an accessible public API
    (e.g. ChatGPT web UI, Claude chat, Google AI Overview in browser, Bing Copilot web).
    """

    question_id: str = Field(
        ...,
        description="ID of the creator question being answered.",
    )
    assistant: ProviderType = Field(
        ...,
        description="Target AI assistant platform (chatgpt, claude, perplexity, gemini, bing_copilot, google_ai_overview).",
    )
    raw_response: str = Field(
        ...,
        min_length=1,
        description="Full raw text response, conversation transcript, or JSON dump from the AI assistant.",
    )
    ai_model_version: Optional[str] = Field(
        default=None,
        description="Underlying model version if known (e.g. GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro).",
    )
    citation_urls: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("citation_urls", "quoted_source_urls", "quoted_urls"),
        description="Direct web citations/links output by the assistant.",
    )
    market: Optional[str] = Field(
        default=None,
        description="Target search/observation market. Inherits from question if omitted.",
    )
    location: Optional[str] = Field(
        default=None,
        description="Geographic location setting.",
    )
    measured_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of observation. Defaults to UTC now.",
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Public URL or session link if accessible.",
    )
    operator_id: str = Field(
        default="geo_operator",
        description="Operator or researcher conducting manual assessment.",
    )
    collector_notes: Optional[str] = Field(
        default=None,
        description="Notes regarding prompt format or assistant behavior.",
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured metadata.",
    )

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


