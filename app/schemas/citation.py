"""Schemas for Citation Opportunities and Targets."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import CitationGapType


def now_utc() -> datetime:
    """Return naive UTC datetime for cross-platform SQLite compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CitationTargetBase(BaseModel):
    """Core fields for a citation target opportunity."""

    target_domain: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Domain where competitors are cited or where IncuBrix should be cited.",
        examples=["searchengineland.com", "zapier.com"],
    )
    target_url: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Specific URL hosting the authority content.",
    )
    question_id: Optional[str] = Field(
        default=None,
        description="Associated creator question ID.",
    )
    observation_id: Optional[str] = Field(
        default=None,
        description="Associated visibility observation where this gap was detected.",
    )
    competitor_domain: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Competitor domain currently cited in this position.",
    )
    anchor_context: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Surrounding text or anchor context where citation is placed.",
    )
    gap_type: CitationGapType = Field(
        default=CitationGapType.UNKNOWN,
        description="Category of citation gap.",
    )
    authority_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Authority estimation (0-100) if available.",
    )
    outreach_status: str = Field(
        default="identified",
        max_length=50,
        description="Status of citation outreach (identified, pitched, cited, closed).",
    )
    relevance: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Why this specific authority URL/domain is relevant to creator workflows or AEO.",
    )
    pitch_angle: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Legitimate editorial angle or outreach pitch for acquiring a citation.",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Curator notes or contextual discovery details.",
    )


class CitationTargetCreate(CitationTargetBase):
    """Payload to record a citation target."""

    pass


class CitationTargetRead(CitationTargetBase):
    """Serialized citation target."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class SeedCitationsResponse(BaseModel):
    """Response returned when seeding the 30-target citation opportunities catalog."""

    total_seeded: int
    domains_seeded: List[str]
    message: str
