"""API routes for Visibility Scoring, SEO/AEO/GEO Analytics, and Cohort Comparisons."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_observation_repository
from app.database.repositories.observation_repo import ObservationRepository
from app.engine.visibility_metrics import VisibilityMetricsCalculator
from app.schemas.scoring import (
    VisibilityMetricsReport,
    VisibilityPeriodComparison,
)

router = APIRouter(prefix="/scoring", tags=["Visibility Scoring & Analytics"])


@router.get(
    "/report",
    response_model=VisibilityMetricsReport,
    summary="Compute comprehensive SEO, AEO, and GEO visibility metrics",
)
def get_visibility_metrics_report(
    market: Optional[str] = Query(None, description="Filter by target market (e.g. US, UK)"),
    provider: Optional[str] = Query(None, description="Filter by provider or assistant (e.g. google_search, perplexity, chatgpt)"),
    question_id: Optional[str] = Query(None, description="Filter by Creator Question ID"),
    start_date: Optional[datetime] = Query(None, description="Filter observations on or after this ISO datetime"),
    end_date: Optional[datetime] = Query(None, description="Filter observations on or before this ISO datetime"),
    deduplicate: bool = Query(True, description="Deduplicate observations by daily fingerprint before calculation"),
    obs_repo: ObservationRepository = Depends(get_observation_repository),
) -> VisibilityMetricsReport:
    """Calculates documented SEO, AEO, and GEO metrics from persisted valid observations.

    Excludes failed or unknown observations from valid denominators and reports them separately.
    """
    obs_list = obs_repo.filter_observations(
        start_date=start_date,
        end_date=end_date,
        market=market,
        provider=provider,
        question_id=question_id,
        limit=10000,
    )

    filter_ctx = {
        "market": market,
        "provider": provider,
        "question_id": question_id,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "deduplicate": deduplicate,
    }

    return VisibilityMetricsCalculator.calculate_metrics(
        observations=obs_list,
        deduplicate=deduplicate,
        filter_context=filter_ctx,
    )


@router.get(
    "/compare",
    response_model=VisibilityPeriodComparison,
    summary="Compare visibility metrics side-by-side across two date ranges",
)
def compare_visibility_periods(
    period_a_start: datetime = Query(..., description="Start of baseline Period A"),
    period_a_end: datetime = Query(..., description="End of baseline Period A"),
    period_b_start: datetime = Query(..., description="Start of comparison Period B"),
    period_b_end: datetime = Query(..., description="End of comparison Period B"),
    period_a_label: str = Query("Period A", description="Label for Period A"),
    period_b_label: str = Query("Period B", description="Label for Period B"),
    market: Optional[str] = Query(None, description="Optional market filter for both periods"),
    provider: Optional[str] = Query(None, description="Optional provider filter for both periods"),
    obs_repo: ObservationRepository = Depends(get_observation_repository),
) -> VisibilityPeriodComparison:
    """Compare visibility metrics between two distinct time periods, computing deltas for all core rates."""
    if period_a_start > period_a_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period_a_start cannot be after period_a_end",
        )
    if period_b_start > period_b_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period_b_start cannot be after period_b_end",
        )

    all_obs = obs_repo.filter_observations(
        market=market,
        provider=provider,
        limit=10000,
    )

    return VisibilityMetricsCalculator.compare_periods(
        observations=all_obs,
        period_a_start=period_a_start,
        period_a_end=period_a_end,
        period_b_start=period_b_start,
        period_b_end=period_b_end,
        period_a_label=period_a_label,
        period_b_label=period_b_label,
    )


@router.get(
    "/breakdown",
    response_model=Dict[str, VisibilityMetricsReport],
    summary="Breakdown visibility metrics grouped by market, provider, or question",
)
def get_visibility_breakdown(
    group_by: str = Query("market", pattern="^(market|provider|question)$", description="Dimension to group by"),
    market: Optional[str] = Query(None, description="Filter by market before breakdown"),
    provider: Optional[str] = Query(None, description="Filter by provider before breakdown"),
    obs_repo: ObservationRepository = Depends(get_observation_repository),
) -> Dict[str, VisibilityMetricsReport]:
    """Calculate visibility metrics partitioned by dimension (market, provider, or question)."""
    obs_list = obs_repo.filter_observations(
        market=market,
        provider=provider,
        limit=10000,
    )

    if group_by == "market":
        return VisibilityMetricsCalculator.group_by_market(obs_list)
    if group_by == "provider":
        return VisibilityMetricsCalculator.group_by_provider(obs_list)
    return VisibilityMetricsCalculator.group_by_question(obs_list)
