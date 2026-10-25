"""Unit and integration tests for Module 5: Visibility Scoring and Comparative Analytics.

Tests verify:
- Heuristic visibility score calculation (0-100).
- SEO metrics (Top-10 rate, Top-3 rate, average rank, answer box presence rate).
- GEO / AEO metrics (AI mention rate, AI citation rate, competitors observed).
- Strict exclusion of non-success and unknown observations from valid denominators.
- Zero denominator safety (no division-by-zero errors).
- Missing values and explicit nullability handling.
- Repeated record deduplication.
- Date range period comparisons and delta computations.
- Breakdown by market, provider, and question.
- REST API endpoints (/v1/scoring/report, /v1/scoring/compare, /v1/scoring/breakdown).
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models.question import QuestionModel
from app.database.repositories.observation_repo import ObservationRepository
from app.database.repositories.question_repo import QuestionRepository
from app.engine.scoring import calculate_visibility_score
from app.engine.visibility_metrics import VisibilityMetricsCalculator
from app.schemas.common import (
    CitationStatus,
    CollectionStatus,
    MentionStatus,
    ObservationType,
    ProviderType,
)
from app.schemas.observations import ObservationCreate
from app.schemas.questions import QuestionCreate


# ==============================================================================
# Base Heuristic Scoring Tests
# ==============================================================================


def test_perfect_visibility_score():
    """Rank 1 + Answer box + Mentioned + Cited = 100."""
    obs = ObservationCreate(
        question_id="q-test",
        market="US",
        measured_at=datetime.now(timezone.utc),
        provider=ProviderType.GOOGLE_SEARCH,
        observation_type=ObservationType.SEARCH_ENGINE,
        rank_position=1,
        answer_box_present=True,
        incubrix_mentioned=MentionStatus.MENTIONED,
        incubrix_cited=CitationStatus.CITED,
        collection_status=CollectionStatus.SUCCESS,
    )
    assert calculate_visibility_score(obs) == 100


def test_ai_assistant_unranked_mention_only():
    """AI Assistant with rank=None, answer_box=None, Mentioned=Yes, Cited=No = 20."""
    obs = ObservationCreate(
        question_id="q-test",
        market="US",
        measured_at=datetime.now(timezone.utc),
        provider=ProviderType.PERPLEXITY,
        observation_type=ObservationType.AI_ASSISTANT,
        rank_position=None,
        answer_box_present=None,
        incubrix_mentioned=MentionStatus.MENTIONED,
        incubrix_cited=CitationStatus.NOT_CITED,
        collection_status=CollectionStatus.SUCCESS,
    )
    assert calculate_visibility_score(obs) == 20


def test_failed_collection_returns_none():
    """If collection failed, score is None."""
    obs = ObservationCreate(
        question_id="q-test",
        market="US",
        measured_at=datetime.now(timezone.utc),
        provider=ProviderType.GOOGLE_SEARCH,
        collection_status=CollectionStatus.FAILED,
        error_code="TIMEOUT",
    )
    assert calculate_visibility_score(obs) is None


def test_unknown_evidence_not_penalized_with_false_score():
    """All unknown attributes without confirmed data returns None."""
    obs = ObservationCreate(
        question_id="q-test",
        market="US",
        measured_at=datetime.now(timezone.utc),
        provider=ProviderType.CHATGPT,
        rank_position=None,
        answer_box_present=None,
        incubrix_mentioned=MentionStatus.UNKNOWN,
        incubrix_cited=CitationStatus.UNAVAILABLE,
        collection_status=CollectionStatus.SUCCESS,
    )
    assert calculate_visibility_score(obs) is None


# ==============================================================================
# Visibility Metrics Calculator Tests (Module 5)
# ==============================================================================


def test_metrics_calculation_seo_aeo_geo_success():
    """Verify calculation of SEO, AEO, and GEO rates from valid observations."""
    obs_list = [
        # Obs 1: Rank 1 (Top 10 & Top 3), Answer Box, Mentioned, Cited, Scored 100
        ObservationCreate(
            question_id="q1",
            market="US",
            measured_at=datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc),
            provider=ProviderType.GOOGLE_SEARCH,
            observation_type=ObservationType.SEARCH_ENGINE,
            rank_position=1,
            answer_box_present=True,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.CITED,
            collection_status=CollectionStatus.SUCCESS,
            observed_features=["answer_box", "organic_results"],
        ),
        # Obs 2: Rank 5 (Top 10, not Top 3), No Answer Box, Mentioned, Not Cited, Scored 50
        ObservationCreate(
            question_id="q2",
            market="US",
            measured_at=datetime(2026, 10, 20, 11, 0, tzinfo=timezone.utc),
            provider=ProviderType.GOOGLE_SEARCH,
            observation_type=ObservationType.SEARCH_ENGINE,
            rank_position=5,
            answer_box_present=False,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.NOT_CITED,
            collection_status=CollectionStatus.SUCCESS,
            observed_features=["organic_results"],
        ),
        # Obs 3: Rank 15 (Not Top 10), Not Mentioned, Not Cited, Scored 5
        ObservationCreate(
            question_id="q3",
            market="US",
            measured_at=datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc),
            provider=ProviderType.GOOGLE_SEARCH,
            observation_type=ObservationType.SEARCH_ENGINE,
            rank_position=15,
            answer_box_present=False,
            incubrix_mentioned=MentionStatus.NOT_MENTIONED,
            incubrix_cited=CitationStatus.NOT_CITED,
            collection_status=CollectionStatus.SUCCESS,
            competitors_observed=["Runway"],
        ),
        # Obs 4: Generative AI (Unranked), Mentioned, Cited, Scored 40
        ObservationCreate(
            question_id="q4",
            market="US",
            measured_at=datetime(2026, 10, 20, 13, 0, tzinfo=timezone.utc),
            provider=ProviderType.PERPLEXITY,
            observation_type=ObservationType.AI_ASSISTANT,
            rank_position=None,
            answer_box_present=None,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.CITED,
            collection_status=CollectionStatus.SUCCESS,
            observed_features=["generative_synthesis", "citations"],
            competitors_observed=["InVideo"],
        ),
    ]

    report = VisibilityMetricsCalculator.calculate_metrics(obs_list, deduplicate=False)

    assert report.total_raw_observations == 4
    assert report.valid_evaluated_observations == 4
    assert report.scored_observations_count == 4

    # SEO verification:
    # 3 ranking observations (pos 1, 5, 15)
    # top_10_count = 2 (pos 1 and 5) -> 2 / 3 * 100 = 66.67%
    # top_3_count = 1 (pos 1) -> 1 / 3 * 100 = 33.33%
    # avg_rank = (1 + 5 + 15) / 3 = 7.0
    assert report.seo_metrics.valid_ranking_observations == 3
    assert report.seo_metrics.unranked_observations == 1
    assert report.seo_metrics.top_10_count == 2
    assert report.seo_metrics.top_10_ranking_rate_pct == 66.67
    assert report.seo_metrics.top_3_count == 1
    assert report.seo_metrics.top_3_ranking_rate_pct == 33.33
    assert report.seo_metrics.average_rank_position == 7.0

    # Answer box present = 1 / 4 = 25.0%
    assert report.seo_metrics.answer_box_present_count == 1
    assert report.seo_metrics.answer_box_rate_pct == 25.0

    # GEO / AEO verification:
    # Mentioned = 3, Not Mentioned = 1 -> Evaluated = 4. Rate = 3 / 4 * 100 = 75.0%
    # Cited = 2, Not Cited = 2 -> Evaluated = 4. Rate = 2 / 4 * 100 = 50.0%
    assert report.geo_metrics.evaluated_mentions == 4
    assert report.geo_metrics.mentioned_count == 3
    assert report.geo_metrics.not_mentioned_count == 1
    assert report.geo_metrics.ai_mention_rate_pct == 75.0

    assert report.geo_metrics.evaluated_citations == 4
    assert report.geo_metrics.cited_count == 2
    assert report.geo_metrics.not_cited_count == 2
    assert report.geo_metrics.ai_citation_rate_pct == 50.0
    assert "Runway" in report.geo_metrics.observed_competitors
    assert "InVideo" in report.geo_metrics.observed_competitors


def test_metrics_zero_denominators_safe_handling():
    """Verify zero denominators across all metrics return 0.0 without division by zero errors."""
    # 1. Completely empty list
    empty_report = VisibilityMetricsCalculator.calculate_metrics([])
    assert empty_report.total_raw_observations == 0
    assert empty_report.valid_evaluated_observations == 0
    assert empty_report.seo_metrics.valid_ranking_observations == 0
    assert empty_report.seo_metrics.top_10_ranking_rate_pct == 0.0
    assert empty_report.seo_metrics.top_3_ranking_rate_pct == 0.0
    assert empty_report.seo_metrics.average_rank_position is None
    assert empty_report.geo_metrics.evaluated_mentions == 0
    assert empty_report.geo_metrics.ai_mention_rate_pct == 0.0
    assert empty_report.geo_metrics.evaluated_citations == 0
    assert empty_report.geo_metrics.ai_citation_rate_pct == 0.0
    assert empty_report.answer_features.feature_presence_rate_pct == 0.0
    assert empty_report.average_visibility_score is None

    # 2. Observations with zero ranked queries (e.g. only generative AI without ranks)
    ai_only = [
        ObservationCreate(
            question_id="q-ai-1",
            market="US",
            measured_at=datetime.now(timezone.utc),
            provider=ProviderType.CHATGPT,
            observation_type=ObservationType.AI_ASSISTANT,
            rank_position=None,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.UNAVAILABLE,
            collection_status=CollectionStatus.SUCCESS,
        )
    ]
    report = VisibilityMetricsCalculator.calculate_metrics(ai_only)
    assert report.seo_metrics.valid_ranking_observations == 0
    assert report.seo_metrics.top_10_ranking_rate_pct == 0.0
    assert report.seo_metrics.average_rank_position is None

    # Mentions evaluated: 1 mentioned -> 100.0%
    assert report.geo_metrics.evaluated_mentions == 1
    assert report.geo_metrics.ai_mention_rate_pct == 100.0

    # Citations: UNAVAILABLE is excluded from denominator -> denominator = 0 -> rate = 0.0
    assert report.geo_metrics.evaluated_citations == 0
    assert report.geo_metrics.unavailable_or_unknown_citation_count == 1
    assert report.geo_metrics.ai_citation_rate_pct == 0.0


def test_metrics_missing_values_and_exclusions():
    """Verify failed/unavailable collections are strictly excluded from calculation denominators."""
    obs_list = [
        # Valid observation
        ObservationCreate(
            question_id="q1",
            market="US",
            measured_at=datetime.now(timezone.utc),
            provider=ProviderType.GOOGLE_SEARCH,
            rank_position=2,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.CITED,
            collection_status=CollectionStatus.SUCCESS,
        ),
        # Failed observation (timeout)
        ObservationCreate(
            question_id="q2",
            market="US",
            measured_at=datetime.now(timezone.utc),
            provider=ProviderType.GOOGLE_SEARCH,
            rank_position=None,
            incubrix_mentioned=MentionStatus.UNKNOWN,
            incubrix_cited=CitationStatus.UNAVAILABLE,
            collection_status=CollectionStatus.FAILED,
            error_code="TIMEOUT",
        ),
        # Unavailable observation (unconfigured API)
        ObservationCreate(
            question_id="q3",
            market="US",
            measured_at=datetime.now(timezone.utc),
            provider=ProviderType.PERPLEXITY,
            rank_position=None,
            incubrix_mentioned=MentionStatus.UNKNOWN,
            incubrix_cited=CitationStatus.UNAVAILABLE,
            collection_status=CollectionStatus.UNAVAILABLE,
            error_code="PROVIDER_NOT_CONFIGURED",
        ),
    ]

    report = VisibilityMetricsCalculator.calculate_metrics(obs_list, deduplicate=False)

    assert report.total_raw_observations == 3
    assert report.valid_evaluated_observations == 1  # Only q1 is valid

    # Excluded telemetry
    assert report.excluded_observations.total_excluded == 2
    assert report.excluded_observations.failed_count == 1
    assert report.excluded_observations.unavailable_count == 1

    # Metrics computed strictly over the 1 valid observation
    assert report.seo_metrics.valid_ranking_observations == 1
    assert report.seo_metrics.top_10_count == 1
    assert report.seo_metrics.top_10_ranking_rate_pct == 100.0
    assert report.geo_metrics.ai_mention_rate_pct == 100.0
    assert report.geo_metrics.ai_citation_rate_pct == 100.0


def test_metrics_repeated_records_deduplication():
    """Verify deduplication keeps only 1 latest record per question/provider/market on the same date."""
    now = datetime(2026, 10, 21, 10, 0, tzinfo=timezone.utc)
    later = datetime(2026, 10, 21, 15, 0, tzinfo=timezone.utc)

    obs_list = [
        # Older record for q1 on 2026-10-21 (Rank 10)
        ObservationCreate(
            question_id="q1",
            market="US",
            measured_at=now,
            provider=ProviderType.GOOGLE_SEARCH,
            rank_position=10,
            incubrix_mentioned=MentionStatus.NOT_MENTIONED,
            incubrix_cited=CitationStatus.NOT_CITED,
            collection_status=CollectionStatus.SUCCESS,
        ),
        # Later record for q1 on 2026-10-21 (Rank 1 - should supersede)
        ObservationCreate(
            question_id="q1",
            market="US",
            measured_at=later,
            provider=ProviderType.GOOGLE_SEARCH,
            rank_position=1,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.CITED,
            collection_status=CollectionStatus.SUCCESS,
        ),
        # Record for different question q2 on same date
        ObservationCreate(
            question_id="q2",
            market="US",
            measured_at=now,
            provider=ProviderType.GOOGLE_SEARCH,
            rank_position=3,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.CITED,
            collection_status=CollectionStatus.SUCCESS,
        ),
    ]

    # Without deduplication -> 3 records
    raw_report = VisibilityMetricsCalculator.calculate_metrics(obs_list, deduplicate=False)
    assert raw_report.total_raw_observations == 3
    assert raw_report.deduplicated_observations == 3

    # With deduplication -> 2 records (q1's later record supersedes earlier record)
    dedup_report = VisibilityMetricsCalculator.calculate_metrics(obs_list, deduplicate=True)
    assert dedup_report.total_raw_observations == 3
    assert dedup_report.deduplicated_observations == 2
    # Ranks evaluated are pos 1 and pos 3 -> avg rank = 2.0
    assert dedup_report.seo_metrics.average_rank_position == 2.0
    assert dedup_report.seo_metrics.top_3_count == 2
    assert dedup_report.seo_metrics.top_3_ranking_rate_pct == 100.0


def test_metrics_date_period_comparison():
    """Verify side-by-side comparison across Period A and Period B computes accurate deltas."""
    # Period A: 2026-10-01 to 2026-10-10 (Baseline)
    p_a_obs = [
        ObservationCreate(
            question_id="q1",
            market="US",
            measured_at=datetime(2026, 10, 5, 12, 0),
            provider=ProviderType.GOOGLE_SEARCH,
            rank_position=8,  # In top 10
            incubrix_mentioned=MentionStatus.NOT_MENTIONED,
            incubrix_cited=CitationStatus.NOT_CITED,
            collection_status=CollectionStatus.SUCCESS,
        ),
        ObservationCreate(
            question_id="q2",
            market="US",
            measured_at=datetime(2026, 10, 6, 12, 0),
            provider=ProviderType.GOOGLE_SEARCH,
            rank_position=12,  # Not in top 10
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.NOT_CITED,
            collection_status=CollectionStatus.SUCCESS,
        ),
    ]

    # Period B: 2026-10-11 to 2026-10-20 (Improved)
    p_b_obs = [
        ObservationCreate(
            question_id="q1",
            market="US",
            measured_at=datetime(2026, 10, 15, 12, 0),
            provider=ProviderType.GOOGLE_SEARCH,
            rank_position=1,  # In top 10 & top 3
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.CITED,
            collection_status=CollectionStatus.SUCCESS,
        ),
        ObservationCreate(
            question_id="q2",
            market="US",
            measured_at=datetime(2026, 10, 16, 12, 0),
            provider=ProviderType.GOOGLE_SEARCH,
            rank_position=2,  # In top 10 & top 3
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.CITED,
            collection_status=CollectionStatus.SUCCESS,
        ),
    ]

    comparison = VisibilityMetricsCalculator.compare_periods(
        observations=p_a_obs + p_b_obs,
        period_a_start=datetime(2026, 10, 1),
        period_a_end=datetime(2026, 10, 10),
        period_b_start=datetime(2026, 10, 11),
        period_b_end=datetime(2026, 10, 20),
        period_a_label="Week 1",
        period_b_label="Week 2",
    )

    # Period A: 1 out of 2 in top 10 -> 50.0%
    # Period B: 2 out of 2 in top 10 -> 100.0%
    # Delta: +50.0 percentage points
    assert comparison.period_a_metrics.seo_metrics.top_10_ranking_rate_pct == 50.0
    assert comparison.period_b_metrics.seo_metrics.top_10_ranking_rate_pct == 100.0
    assert comparison.deltas["top_10_ranking_rate_pct"].absolute_delta == 50.0

    # Mentions: Period A = 1/2 (50.0%), Period B = 2/2 (100.0%) -> Delta: +50.0
    assert comparison.deltas["ai_mention_rate_pct"].absolute_delta == 50.0

    # Citations: Period A = 0/2 (0.0%), Period B = 2/2 (100.0%) -> Delta: +100.0
    assert comparison.deltas["ai_citation_rate_pct"].absolute_delta == 100.0


def test_metrics_grouping_by_market_and_provider():
    """Verify breakdowns by market and provider partitions observations correctly."""
    obs_list = [
        # US Google
        ObservationCreate(
            question_id="q1",
            market="US",
            measured_at=datetime.now(timezone.utc),
            provider=ProviderType.GOOGLE_SEARCH,
            rank_position=1,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.CITED,
            collection_status=CollectionStatus.SUCCESS,
        ),
        # UK Perplexity
        ObservationCreate(
            question_id="q1",
            market="UK",
            measured_at=datetime.now(timezone.utc),
            provider=ProviderType.PERPLEXITY,
            rank_position=None,
            incubrix_mentioned=MentionStatus.MENTIONED,
            incubrix_cited=CitationStatus.NOT_CITED,
            collection_status=CollectionStatus.SUCCESS,
        ),
    ]

    by_market = VisibilityMetricsCalculator.group_by_market(obs_list)
    assert "US" in by_market
    assert "UK" in by_market
    assert by_market["US"].seo_metrics.top_10_count == 1
    assert by_market["UK"].seo_metrics.valid_ranking_observations == 0

    by_provider = VisibilityMetricsCalculator.group_by_provider(obs_list)
    assert "google_search" in by_provider
    assert "perplexity" in by_provider
    assert by_provider["google_search"].geo_metrics.ai_citation_rate_pct == 100.0
    assert by_provider["perplexity"].geo_metrics.ai_citation_rate_pct == 0.0


# ==============================================================================
# REST API Endpoint Tests (/v1/scoring)
# ==============================================================================


def test_scoring_api_endpoints(client: TestClient, db_session: Session):
    """Verify /v1/scoring API routes: /report, /compare, /breakdown, /summary."""
    q_repo = QuestionRepository(db_session)
    obs_repo = ObservationRepository(db_session)

    # 1. Create a question and seed observations
    q = q_repo.create_strict(
        QuestionCreate(text="How to score AI visibility for B2B brands?", target_market="US")
    )

    obs1 = ObservationCreate(
        question_id=q.id,
        market="US",
        measured_at=datetime(2026, 10, 10, 10, 0),
        provider=ProviderType.GOOGLE_SEARCH,
        rank_position=1,
        answer_box_present=True,
        incubrix_mentioned=MentionStatus.MENTIONED,
        incubrix_cited=CitationStatus.CITED,
        collection_status=CollectionStatus.SUCCESS,
        observed_features=["answer_box", "organic_results"],
    )
    obs_repo.record_observation(obs1, visibility_score=100)

    obs2 = ObservationCreate(
        question_id=q.id,
        market="UK",
        measured_at=datetime(2026, 10, 20, 10, 0),
        provider=ProviderType.PERPLEXITY,
        rank_position=None,
        incubrix_mentioned=MentionStatus.MENTIONED,
        incubrix_cited=CitationStatus.NOT_CITED,
        collection_status=CollectionStatus.SUCCESS,
        observed_features=["generative_synthesis"],
    )
    obs_repo.record_observation(obs2, visibility_score=20)

    # 2. Test GET /v1/scoring/report
    resp = client.get("/v1/scoring/report")
    assert resp.status_code == 200
    report = resp.json()
    assert report["total_raw_observations"] == 2
    assert report["valid_evaluated_observations"] == 2
    assert report["average_visibility_score"] == 60.0
    assert report["seo_metrics"]["top_10_ranking_rate_pct"] == 100.0
    assert report["geo_metrics"]["ai_mention_rate_pct"] == 100.0
    assert report["geo_metrics"]["ai_citation_rate_pct"] == 50.0

    # Filter report by market=US
    resp_us = client.get("/v1/scoring/report?market=US")
    assert resp_us.status_code == 200
    assert resp_us.json()["valid_evaluated_observations"] == 1

    # 3. Test GET /v1/scoring/breakdown
    breakdown_resp = client.get("/v1/scoring/breakdown?group_by=market")
    assert breakdown_resp.status_code == 200
    breakdown = breakdown_resp.json()
    assert "US" in breakdown
    assert "UK" in breakdown
    assert breakdown["US"]["valid_evaluated_observations"] == 1

    # 4. Test GET /v1/scoring/compare
    compare_resp = client.get(
        "/v1/scoring/compare",
        params={
            "period_a_start": "2026-10-01T00:00:00",
            "period_a_end": "2026-10-15T23:59:59",
            "period_b_start": "2026-10-16T00:00:00",
            "period_b_end": "2026-10-31T23:59:59",
            "period_a_label": "First Half",
            "period_b_label": "Second Half",
        },
    )
    assert compare_resp.status_code == 200
    comparison = compare_resp.json()
    assert comparison["period_a_label"] == "First Half"
    assert comparison["period_b_label"] == "Second Half"
    assert "top_10_ranking_rate_pct" in comparison["deltas"]

    # 5. Test existing GET /v1/summary (regression test)
    summary_resp = client.get("/v1/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_observations"] == 2
    assert summary["average_visibility_score"] == 60.0
    assert summary["mention_stats"]["positive_mention_rate_pct"] == 100.0
