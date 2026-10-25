"""Pydantic schemas for Visibility Scoring, SEO/AEO/GEO Metrics, and Comparative Analytics."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SEOMetrics(BaseModel):
    """Search Engine Optimization metrics computed over valid ranking observations."""

    valid_ranking_observations: int = Field(
        ...,
        description="Count of valid observations where search ranking was actively evaluated.",
    )
    unranked_observations: int = Field(
        ...,
        description="Count of observations where ranking was not applicable (e.g. generative AI).",
    )
    top_10_count: int = Field(
        ...,
        description="Count of observations with organic rank position between 1 and 10.",
    )
    top_3_count: int = Field(
        ...,
        description="Count of observations with organic rank position between 1 and 3.",
    )
    top_10_ranking_rate_pct: float = Field(
        ...,
        description="Percentage of evaluated ranking observations ranking in top 10 (0.0 if denominator is 0).",
    )
    top_3_ranking_rate_pct: float = Field(
        ...,
        description="Percentage of evaluated ranking observations ranking in top 3 (0.0 if denominator is 0).",
    )
    average_rank_position: Optional[float] = Field(
        default=None,
        description="Mean organic ranking position among ranked observations (None if no ranked observations).",
    )
    answer_box_present_count: int = Field(
        ...,
        description="Count of observations where a SERP answer box or featured snippet was present.",
    )
    answer_box_rate_pct: float = Field(
        ...,
        description="Percentage of ranking observations with featured snippet / answer box.",
    )

    model_config = ConfigDict(from_attributes=True)


class GEOMetrics(BaseModel):
    """Generative Engine Optimization (GEO) & AEO mention and citation metrics."""

    evaluated_mentions: int = Field(
        ...,
        description="Valid denominator for brand mentions (count of MENTIONED + NOT_MENTIONED).",
    )
    mentioned_count: int = Field(..., description="Count of confirmed brand mentions.")
    not_mentioned_count: int = Field(..., description="Count of confirmed non-mentions.")
    unknown_mention_count: int = Field(
        ...,
        description="Count of observations where mention status was UNKNOWN (excluded from denominator).",
    )
    ai_mention_rate_pct: float = Field(
        ...,
        description="Positive brand mention rate: (mentioned / evaluated_mentions) * 100.",
    )

    evaluated_citations: int = Field(
        ...,
        description="Valid denominator for citations (count of CITED + NOT_CITED).",
    )
    cited_count: int = Field(..., description="Count of confirmed direct website link citations.")
    not_cited_count: int = Field(
        ...,
        description="Count of confirmed non-citations when links were present.",
    )
    unavailable_or_unknown_citation_count: int = Field(
        ...,
        description="Count of observations where citations were UNAVAILABLE/UNKNOWN (excluded from denominator).",
    )
    ai_citation_rate_pct: float = Field(
        ...,
        description="Positive citation rate: (cited / evaluated_citations) * 100.",
    )

    observed_competitors: List[str] = Field(
        default_factory=list,
        description="Competitor brands observed in the evaluated subset.",
    )

    model_config = ConfigDict(from_attributes=True)


class AnswerFeatureMetrics(BaseModel):
    """Evaluates presence of SERP and AI answer features across valid queries."""

    evaluated_observations: int = Field(
        ...,
        description="Denominator of observations where answer features were evaluated.",
    )
    feature_present_count: int = Field(
        ...,
        description="Count of observations where at least one rich answer feature was present.",
    )
    feature_presence_rate_pct: float = Field(
        ...,
        description="Rate of answer feature presence over evaluated observations.",
    )
    features_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Breakdown of individual features (e.g. answer_box, organic_results, citations).",
    )

    model_config = ConfigDict(from_attributes=True)


class ExcludedObservationsSummary(BaseModel):
    """Telemetry capturing observations excluded from valid calculation denominators."""

    total_excluded: int = Field(
        ...,
        description="Total observations excluded from valid calculation denominators.",
    )
    failed_count: int = Field(..., description="Observations with collection_status=FAILED.")
    unavailable_count: int = Field(..., description="Observations with collection_status=UNAVAILABLE.")
    partial_count: int = Field(..., description="Observations with collection_status=PARTIAL.")
    unknown_count: int = Field(..., description="Observations with collection_status=UNKNOWN.")
    other_count: int = Field(..., description="Observations excluded for other status reasons.")

    model_config = ConfigDict(from_attributes=True)


class VisibilityMetricsReport(BaseModel):
    """Comprehensive SEO, AEO, and GEO visibility metrics report."""

    total_raw_observations: int = Field(
        ...,
        description="Total raw records retrieved prior to deduplication.",
    )
    deduplicated_observations: int = Field(
        ...,
        description="Total observations after daily fingerprint deduplication.",
    )
    valid_evaluated_observations: int = Field(
        ...,
        description="Total observations with collection_status=SUCCESS included in calculation.",
    )
    average_visibility_score: Optional[float] = Field(
        default=None,
        description="Mean visibility score (0-100) across valid evaluated records.",
    )
    scored_observations_count: int = Field(
        ...,
        description="Count of valid observations with a computed visibility score.",
    )
    score_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"high": 0, "medium": 0, "low": 0},
        description="Distribution of scores: high (>=70), medium (40-69), low (<40).",
    )
    seo_metrics: SEOMetrics = Field(..., description="Search Engine Optimization visibility metrics.")
    geo_metrics: GEOMetrics = Field(..., description="Generative Engine Optimization visibility metrics.")
    answer_features: AnswerFeatureMetrics = Field(..., description="Answer feature presence metrics.")
    excluded_observations: ExcludedObservationsSummary = Field(
        ...,
        description="Breakdown of excluded observations with non-success statuses.",
    )
    filter_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual filters applied (date range, market, provider, question).",
    )

    model_config = ConfigDict(from_attributes=True)


class MetricPeriodDelta(BaseModel):
    """Comparative change in a specific visibility metric across two periods."""

    metric_name: str
    period_a_value: Optional[float] = None
    period_b_value: Optional[float] = None
    absolute_delta: Optional[float] = None
    percentage_change_pct: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class VisibilityPeriodComparison(BaseModel):
    """Side-by-side comparison of visibility metrics between two time periods or cohorts."""

    period_a_label: str = Field(..., description="Label or date range for Period A (baseline).")
    period_b_label: str = Field(..., description="Label or date range for Period B (comparison).")
    period_a_metrics: VisibilityMetricsReport
    period_b_metrics: VisibilityMetricsReport
    deltas: Dict[str, MetricPeriodDelta] = Field(
        default_factory=dict,
        description="Computed deltas for core visibility metrics.",
    )

    model_config = ConfigDict(from_attributes=True)
