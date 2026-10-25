"""Schemas for Creator Questions, Ingestion, and Manual Review Curation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.database.base import utc_now
from app.schemas.common import ReviewStatus


class QuestionBase(BaseModel):
    """Shared fields for creator questions."""

    text: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Core question or search prompt evaluated for visibility.",
        examples=["How do creators turn long scripts into engaging video b-roll?"],
    )
    target_market: str = Field(
        default="US",
        min_length=2,
        max_length=50,
        description="Target geographical market code or description (e.g., US, UK, Global).",
    )
    target_location: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Optional city/region specific geo-location string.",
        examples=["New York, NY", "Austin, TX"],
    )
    language: str = Field(
        default="en",
        min_length=2,
        max_length=10,
        description="ISO 639-1 language code.",
    )
    intent: Optional[str] = Field(
        default="informational",
        max_length=50,
        description="Search/AEO intent (informational, commercial, navigational, transactional, comparison).",
    )
    persona: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Target user persona (e.g., solo creator, agency editor).",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Categorization tags for filtering and batch analysis.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this question is actively monitored by scheduled pipelines.",
    )

    # Ingestion Provenance & Curation Status
    review_status: ReviewStatus = Field(
        default=ReviewStatus.PENDING,
        description="Manual curation and review status (pending, approved, rejected, flagged).",
    )
    source_url: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Original source link where creator question was discovered.",
    )
    source_platform: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Source platform or community (e.g. YouTube, Reddit, Quora, TikTok).",
    )
    source_timestamp: Optional[datetime] = Field(
        default=None,
        description="Original publication or discovery timestamp from the source.",
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("meta", "metadata"),
        serialization_alias="metadata",
        description="Structured contextual metadata (creator handle, post ID, thread title).",
    )

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @field_validator("source_url", mode="before")
    @classmethod
    def validate_source_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format while allowing missing or empty URLs."""
        if v is None:
            return None
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                return None
            parsed = urlparse(cleaned)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError("Invalid source URL. Must be a valid HTTP or HTTPS URL.")
            return cleaned
        return str(v)


class QuestionCreate(QuestionBase):
    """Payload for creating a new creator question."""
    pass


class QuestionUpdate(BaseModel):
    """Payload for updating an existing creator question."""

    text: Optional[str] = Field(None, min_length=5, max_length=1000)
    target_market: Optional[str] = Field(None, min_length=2, max_length=50)
    target_location: Optional[str] = Field(None, max_length=150)
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    intent: Optional[str] = Field(None, max_length=50)
    persona: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    review_status: Optional[ReviewStatus] = None
    source_url: Optional[str] = None
    source_platform: Optional[str] = None
    source_timestamp: Optional[datetime] = None
    meta: Optional[Dict[str, Any]] = None

    @field_validator("source_url", mode="before")
    @classmethod
    def validate_update_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = str(v).strip()
        if not cleaned:
            return None
        parsed = urlparse(cleaned)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("Invalid source URL. Must be a valid HTTP or HTTPS URL.")
        return cleaned


class QuestionReviewUpdate(BaseModel):
    """Payload for updating curation/review status."""

    review_status: ReviewStatus = Field(
        ..., description="Target curation review status (approved, rejected, flagged)."
    )
    notes: Optional[str] = Field(
        default=None, max_length=1000, description="Curator reviewer notes."
    )


class QuestionRead(QuestionBase):
    """Serialized representation of a stored creator question."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique question identifier.",
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class IngestionRowError(BaseModel):
    """Validation failure detail for an imported CSV row."""

    row_number: int = Field(..., description="1-indexed row number in the imported CSV.")
    field: str = Field(..., description="Field name where failure occurred.")
    reason: str = Field(..., description="Description of the validation failure.")
    raw_value: Optional[str] = Field(None, description="The raw offending value from the CSV.")


class QuestionIngestionSummary(BaseModel):
    """Summary metrics of a batch question CSV ingestion."""

    total_rows: int = Field(0, description="Total data rows parsed from the CSV file.")
    imported_count: int = Field(0, description="Successfully ingested and created questions.")
    duplicates_count: int = Field(0, description="Questions skipped due to duplicate text.")
    invalid_count: int = Field(0, description="Rows rejected due to schema or URL validation errors.")
    imported_ids: List[str] = Field(default_factory=list, description="IDs of newly created questions.")
    errors: List[IngestionRowError] = Field(default_factory=list, description="List of row-level errors.")
