"""Schemas for Weekly Intelligence Reports and Data Exports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


def now_utc() -> datetime:
    """Return naive UTC datetime for cross-platform consistency."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ProvenanceBreakdown(BaseModel):
    """Categorized observation count by data origin mode."""

    real: int = Field(default=0, description="Real live automated search or AI provider observations.")
    manual: int = Field(default=0, description="Operator-imported manual evidence or assistant transcripts.")
    mocked: int = Field(default=0, description="Synthetic test fixtures or simulated records.")
    unavailable: int = Field(default=0, description="Failed, unconfigured, or unmeasured collection records.")


class WeeklyReportResponse(BaseModel):
    """Executive weekly AEO, SEO, and GEO visibility summary report."""

    model_config = ConfigDict(from_attributes=True)

    report_title: str = "IncuBrix Weekly Visibility & Intelligence Report"
    generated_at: datetime = Field(default_factory=now_utc)
    reporting_window_start: Optional[datetime] = None
    reporting_window_end: Optional[datetime] = None

    # Observation & Provenance
    total_observations: int = 0
    provenance_breakdown: ProvenanceBreakdown = Field(default_factory=ProvenanceBreakdown)

    # Core Metrics
    average_visibility_score: Optional[float] = None
    top_10_ranking_rate_pct: float = 0.0
    ai_mention_rate_pct: float = 0.0
    ai_citation_rate_pct: float = 0.0

    # Section Summaries
    seo_summary: Dict[str, Any] = Field(default_factory=dict)
    geo_summary: Dict[str, Any] = Field(default_factory=dict)
    audit_summary: Dict[str, Any] = Field(default_factory=dict)
    content_summary: Dict[str, Any] = Field(default_factory=dict)
    citation_summary: Dict[str, Any] = Field(default_factory=dict)

    # Formatted Markdown
    markdown_content: str = ""
