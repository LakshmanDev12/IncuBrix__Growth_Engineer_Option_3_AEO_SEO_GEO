"""Schemas for Content Briefs and Generated Pages (AEO/GEO Optimized Content)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def now_utc() -> datetime:
    """Return naive UTC datetime for cross-platform SQLite compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ContentBriefBase(BaseModel):
    """Core fields for an AEO/SEO content brief."""

    question_id: Optional[str] = Field(
        default=None,
        description="Associated creator question driving this content strategy.",
    )
    target_topic: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Core subject matter or theme.",
    )
    target_query: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Primary target user query for answer engine optimization.",
    )
    primary_intent: str = Field(
        default="informational",
        max_length=50,
        description="Search/AEO intent.",
    )
    target_entities: List[str] = Field(
        default_factory=list,
        description="Key semantic entity names that must be explicitly established.",
    )
    required_sections: List[str] = Field(
        default_factory=list,
        description="Structured headings (H2/H3) required for generative answer capture.",
    )
    recommended_faqs: List[str] = Field(
        default_factory=list,
        description="Direct question-answer pairs optimized for citation extraction.",
    )
    target_word_count: int = Field(
        default=1200,
        ge=200,
        le=10000,
        description="Target word count.",
    )
    tone: str = Field(
        default="authoritative and actionable",
        max_length=100,
    )
    schema_type: str = Field(
        default="TechArticle",
        max_length=50,
        description="Recommended schema.org structured data type (e.g. HowTo, FAQPage, TechArticle).",
    )


class ContentBriefCreate(ContentBriefBase):
    """Payload to create a content brief."""

    pass


class ContentBriefRead(ContentBriefBase):
    """Serialized content brief."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class GeneratedPageBase(BaseModel):
    """Core fields for an AEO-optimized content page."""

    brief_id: str = Field(
        ...,
        description="Associated ContentBrief ID.",
    )
    title: str = Field(
        ...,
        min_length=5,
        max_length=250,
        description="Page title tag.",
    )
    slug: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="URL slug (e.g. /script-to-broll-guide).",
    )
    meta_description: str = Field(
        ...,
        min_length=10,
        max_length=320,
        description="SERP meta description.",
    )
    markdown_content: str = Field(
        ...,
        min_length=50,
        description="Full markdown body including direct answer, structured H2/H3 headings and FAQ blocks.",
    )
    schema_org_json: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured JSON-LD entity markup for generative AI indexers.",
    )
    publication_status: str = Field(
        default="unreviewed",
        max_length=50,
        description="Status: unreviewed, reviewed, approved, published, rejected.",
    )
    internal_links: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Suggested internal links with target URLs and descriptive anchor text.",
    )
    citations: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Third-party authoritative research citations.",
    )
    word_count: int = Field(
        default=0,
        ge=0,
        description="Word count of markdown content.",
    )


class GeneratedPageCreate(GeneratedPageBase):
    """Payload to create a generated page."""

    pass


class GeneratedPageRead(GeneratedPageBase):
    """Serialized generated page."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class ContentValidationCheck(BaseModel):
    """Single criteria check result in content validation."""

    check_name: str
    passed: bool
    details: str


class ContentValidationReport(BaseModel):
    """Comprehensive validation report for an AEO page draft."""

    is_publish_ready: bool
    title: str
    slug: str
    word_count: int
    direct_answer_verified: bool
    checks: List[ContentValidationCheck]
    recommendations: List[str] = Field(default_factory=list)


class BatchGenerateRequest(BaseModel):
    """Request payload to generate publish-ready page drafts."""

    use_llm: bool = Field(
        default=False,
        description="Whether to use configured external LLM provider or deterministic template fallback.",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of page drafts to generate.",
    )


class BatchGenerateResponse(BaseModel):
    """Response containing batch generated pages and validation reports."""

    total_generated: int
    pages: List[GeneratedPageRead]
    validation_reports: List[ContentValidationReport]


class PageReviewUpdateRequest(BaseModel):
    """Request payload to review and curate a page draft's status."""

    publication_status: str = Field(
        ...,
        description="New status: unreviewed, reviewed, approved, published, rejected.",
    )
    reviewer_notes: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Human reviewer comments or verification notes.",
    )
