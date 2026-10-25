"""Visibility Metrics Engine for SEO, AEO, and GEO.

Calculates documented performance metrics from persisted, valid observations:
- SEO: Top-10 ranking rate, Top-3 ranking rate, average rank, answer box presence.
- AEO / GEO: AI brand mention rate, AI direct citation rate, answer feature presence.
- Filtering and Exclusions: Non-success and unknown/unavailable states are excluded from
  valid calculation denominators and tracked as separate telemetry.
- Deduplication: Deduplicates observations across repeated daily runs.
- Cohort Comparisons: Groupings and comparative deltas by date range, market, provider, and question.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from app.schemas.common import CitationStatus, CollectionStatus, MentionStatus
from app.schemas.scoring import (
    AnswerFeatureMetrics,
    ExcludedObservationsSummary,
    GEOMetrics,
    MetricPeriodDelta,
    SEOMetrics,
    VisibilityMetricsReport,
    VisibilityPeriodComparison,
)


class VisibilityMetricsCalculator:
    """Calculates granular SEO, AEO, and GEO metrics over observation records."""

    @staticmethod
    def _get_val(obj: Any, attr: str, default: Any = None) -> Any:
        """Safely extract attribute or dictionary key from observation representations."""
        if hasattr(obj, attr):
            val = getattr(obj, attr)
            if hasattr(val, "value"):
                return val.value
            return val
        if isinstance(obj, dict):
            val = obj.get(attr, default)
            if hasattr(val, "value"):
                return val.value
            return val
        return default

    @classmethod
    def deduplicate_observations(cls, observations: List[Any]) -> List[Any]:
        """Deduplicate observations preserving the most recent record per fingerprint or day.

        Key: (question_id, provider, market, location, YYYY-MM-DD)
        """
        seen: Dict[str, Any] = {}
        for obs in observations:
            q_id = str(cls._get_val(obs, "question_id", ""))
            prov = str(cls._get_val(obs, "provider", ""))
            market = str(cls._get_val(obs, "market", "US"))
            loc = str(cls._get_val(obs, "location", "") or "")

            measured_at = cls._get_val(obs, "measured_at")
            if isinstance(measured_at, datetime):
                date_str = measured_at.strftime("%Y-%m-%d")
            elif isinstance(measured_at, str):
                date_str = measured_at[:10]
            else:
                date_str = "undated"

            key = f"{q_id}:{prov}:{market}:{loc}:{date_str}"
            # Keep latest by measured_at if duplicate
            if key not in seen:
                seen[key] = obs
            else:
                existing_measured = cls._get_val(seen[key], "measured_at")
                if measured_at and existing_measured and measured_at > existing_measured:
                    seen[key] = obs

        return list(seen.values())

    @classmethod
    def calculate_metrics(
        cls,
        observations: List[Any],
        deduplicate: bool = True,
        filter_context: Optional[Dict[str, Any]] = None,
    ) -> VisibilityMetricsReport:
        """Calculate complete documented SEO, AEO, and GEO visibility metrics."""
        total_raw = len(observations)
        processed_obs = cls.deduplicate_observations(observations) if deduplicate else list(observations)
        dedup_count = len(processed_obs)

        # 1. Filter valid evaluated observations (CollectionStatus.SUCCESS)
        valid_obs: List[Any] = []
        failed_count = 0
        unavailable_count = 0
        partial_count = 0
        unknown_status_count = 0
        other_excluded_count = 0

        for o in processed_obs:
            st = str(cls._get_val(o, "collection_status", "")).lower()
            if st in (CollectionStatus.SUCCESS.value, "success"):
                valid_obs.append(o)
            elif st in (CollectionStatus.FAILED.value, "failed"):
                failed_count += 1
            elif st in (CollectionStatus.UNAVAILABLE.value, "unavailable"):
                unavailable_count += 1
            elif st in (CollectionStatus.PARTIAL.value, "partial"):
                partial_count += 1
            elif st in (CollectionStatus.PENDING.value, "pending", "unknown"):
                unknown_status_count += 1
            else:
                other_excluded_count += 1

        total_excluded = (
            failed_count
            + unavailable_count
            + partial_count
            + unknown_status_count
            + other_excluded_count
        )
        valid_count = len(valid_obs)

        # 2. SEO Metrics (Top-10, Top-3, Avg Rank, Answer Box)
        valid_ranking: List[Any] = []
        unranked_count = 0
        top_10_count = 0
        top_3_count = 0
        answer_box_present_count = 0

        for o in valid_obs:
            rank = cls._get_val(o, "rank_position")
            if rank is not None and isinstance(rank, (int, float)) and rank > 0:
                valid_ranking.append(rank)
                if 1 <= rank <= 10:
                    top_10_count += 1
                if 1 <= rank <= 3:
                    top_3_count += 1
            else:
                unranked_count += 1

            ab_present = cls._get_val(o, "answer_box_present")
            if ab_present is True:
                answer_box_present_count += 1

        rank_denom = len(valid_ranking)
        top_10_rate = round((top_10_count / rank_denom) * 100, 2) if rank_denom > 0 else 0.0
        top_3_rate = round((top_3_count / rank_denom) * 100, 2) if rank_denom > 0 else 0.0
        avg_rank = round(sum(valid_ranking) / rank_denom, 2) if rank_denom > 0 else None
        ab_rate = round((answer_box_present_count / valid_count) * 100, 2) if valid_count > 0 else 0.0

        seo_metrics = SEOMetrics(
            valid_ranking_observations=rank_denom,
            unranked_observations=unranked_count,
            top_10_count=top_10_count,
            top_3_count=top_3_count,
            top_10_ranking_rate_pct=top_10_rate,
            top_3_ranking_rate_pct=top_3_rate,
            average_rank_position=avg_rank,
            answer_box_present_count=answer_box_present_count,
            answer_box_rate_pct=ab_rate,
        )

        # 3. GEO / AEO Metrics (Mentions and Citations strictly decoupled)
        mentioned_cnt = 0
        not_mentioned_cnt = 0
        unknown_mention_cnt = 0

        cited_cnt = 0
        not_cited_cnt = 0
        unknown_citation_cnt = 0

        competitors_seen: Set[str] = set()

        for o in valid_obs:
            m_st = str(cls._get_val(o, "incubrix_mentioned", "")).lower()
            if m_st in (MentionStatus.MENTIONED.value, "mentioned"):
                mentioned_cnt += 1
            elif m_st in (MentionStatus.NOT_MENTIONED.value, "not_mentioned"):
                not_mentioned_cnt += 1
            else:
                unknown_mention_cnt += 1

            c_st = str(cls._get_val(o, "incubrix_cited", "")).lower()
            if c_st in (CitationStatus.CITED.value, "cited"):
                cited_cnt += 1
            elif c_st in (CitationStatus.NOT_CITED.value, "not_cited"):
                not_cited_cnt += 1
            else:
                unknown_citation_cnt += 1

            comps = cls._get_val(o, "competitors_observed", [])
            if isinstance(comps, list):
                for c in comps:
                    if isinstance(c, str) and c.strip():
                        competitors_seen.add(c.strip())

        evaluated_mentions = mentioned_cnt + not_mentioned_cnt
        mention_rate = (
            round((mentioned_cnt / evaluated_mentions) * 100, 2)
            if evaluated_mentions > 0
            else 0.0
        )

        evaluated_citations = cited_cnt + not_cited_cnt
        citation_rate = (
            round((cited_cnt / evaluated_citations) * 100, 2)
            if evaluated_citations > 0
            else 0.0
        )

        geo_metrics = GEOMetrics(
            evaluated_mentions=evaluated_mentions,
            mentioned_count=mentioned_cnt,
            not_mentioned_count=not_mentioned_cnt,
            unknown_mention_count=unknown_mention_cnt,
            ai_mention_rate_pct=mention_rate,
            evaluated_citations=evaluated_citations,
            cited_count=cited_cnt,
            not_cited_count=not_cited_cnt,
            unavailable_or_unknown_citation_count=unknown_citation_cnt,
            ai_citation_rate_pct=citation_rate,
            observed_competitors=sorted(list(competitors_seen)),
        )

        # 4. Answer Feature Presence
        features_breakdown: Dict[str, int] = {}
        feature_present_count = 0

        for o in valid_obs:
            feats = cls._get_val(o, "observed_features", [])
            has_ab = cls._get_val(o, "answer_box_present") is True
            has_feat = has_ab or (isinstance(feats, list) and len(feats) > 0)

            if has_feat:
                feature_present_count += 1

            if has_ab:
                features_breakdown["answer_box"] = features_breakdown.get("answer_box", 0) + 1

            if isinstance(feats, list):
                for f in feats:
                    if isinstance(f, str) and f.strip() and f != "answer_box":
                        clean_f = f.strip().lower()
                        features_breakdown[clean_f] = features_breakdown.get(clean_f, 0) + 1

        feature_presence_rate = (
            round((feature_present_count / valid_count) * 100, 2)
            if valid_count > 0
            else 0.0
        )

        answer_features = AnswerFeatureMetrics(
            evaluated_observations=valid_count,
            feature_present_count=feature_present_count,
            feature_presence_rate_pct=feature_presence_rate,
            features_breakdown=features_breakdown,
        )

        # 5. Visibility Scores & Distribution
        scored_values = []
        score_dist = {"high": 0, "medium": 0, "low": 0}

        for o in valid_obs:
            sc = cls._get_val(o, "visibility_score")
            if sc is None:
                from app.engine.scoring import calculate_visibility_score
                sc = calculate_visibility_score(o)

            if sc is not None and isinstance(sc, (int, float)):
                scored_values.append(sc)
                if sc >= 70:
                    score_dist["high"] += 1
                elif sc >= 40:
                    score_dist["medium"] += 1
                else:
                    score_dist["low"] += 1

        avg_score = (
            round(sum(scored_values) / len(scored_values), 2)
            if scored_values
            else None
        )

        # 6. Excluded Summary
        excluded_summary = ExcludedObservationsSummary(
            total_excluded=total_excluded,
            failed_count=failed_count,
            unavailable_count=unavailable_count,
            partial_count=partial_count,
            unknown_count=unknown_status_count,
            other_count=other_excluded_count,
        )

        return VisibilityMetricsReport(
            total_raw_observations=total_raw,
            deduplicated_observations=dedup_count,
            valid_evaluated_observations=valid_count,
            average_visibility_score=avg_score,
            scored_observations_count=len(scored_values),
            score_distribution=score_dist,
            seo_metrics=seo_metrics,
            geo_metrics=geo_metrics,
            answer_features=answer_features,
            excluded_observations=excluded_summary,
            filter_context=filter_context or {},
        )

    @classmethod
    def group_by_market(cls, observations: List[Any]) -> Dict[str, VisibilityMetricsReport]:
        """Group observations by target market and calculate metrics for each."""
        grouped: Dict[str, List[Any]] = {}
        for o in observations:
            m = str(cls._get_val(o, "market", "US")).upper()
            grouped.setdefault(m, []).append(o)

        return {
            m: cls.calculate_metrics(obs_list, filter_context={"market": m})
            for m, obs_list in sorted(grouped.items())
        }

    @classmethod
    def group_by_provider(cls, observations: List[Any]) -> Dict[str, VisibilityMetricsReport]:
        """Group observations by provider / assistant platform."""
        grouped: Dict[str, List[Any]] = {}
        for o in observations:
            p = str(cls._get_val(o, "provider", "unknown")).lower()
            grouped.setdefault(p, []).append(o)

        return {
            p: cls.calculate_metrics(obs_list, filter_context={"provider": p})
            for p, obs_list in sorted(grouped.items())
        }

    @classmethod
    def group_by_question(cls, observations: List[Any]) -> Dict[str, VisibilityMetricsReport]:
        """Group observations by Creator Question ID."""
        grouped: Dict[str, List[Any]] = {}
        for o in observations:
            q_id = str(cls._get_val(o, "question_id", "unknown"))
            grouped.setdefault(q_id, []).append(o)

        return {
            q_id: cls.calculate_metrics(obs_list, filter_context={"question_id": q_id})
            for q_id, obs_list in sorted(grouped.items())
        }

    @classmethod
    def compare_periods(
        cls,
        observations: List[Any],
        period_a_start: datetime,
        period_a_end: datetime,
        period_b_start: datetime,
        period_b_end: datetime,
        period_a_label: str = "Period A",
        period_b_label: str = "Period B",
    ) -> VisibilityPeriodComparison:
        """Compare visibility metrics side-by-side across two distinct date windows."""

        def in_range(dt: Optional[datetime], start: datetime, end: datetime) -> bool:
            if not dt:
                return False
            # Normalize to naive UTC for safe comparison
            val = dt.replace(tzinfo=None) if hasattr(dt, "tzinfo") and dt.tzinfo else dt
            s = start.replace(tzinfo=None) if hasattr(start, "tzinfo") and start.tzinfo else start
            e = end.replace(tzinfo=None) if hasattr(end, "tzinfo") and end.tzinfo else end
            return s <= val <= e

        obs_a = [
            o
            for o in observations
            if in_range(cls._get_val(o, "measured_at"), period_a_start, period_a_end)
        ]
        obs_b = [
            o
            for o in observations
            if in_range(cls._get_val(o, "measured_at"), period_b_start, period_b_end)
        ]

        metrics_a = cls.calculate_metrics(
            obs_a,
            filter_context={
                "period": period_a_label,
                "start": period_a_start.isoformat(),
                "end": period_a_end.isoformat(),
            },
        )
        metrics_b = cls.calculate_metrics(
            obs_b,
            filter_context={
                "period": period_b_label,
                "start": period_b_start.isoformat(),
                "end": period_b_end.isoformat(),
            },
        )

        deltas: Dict[str, MetricPeriodDelta] = {}

        def add_delta(name: str, val_a: Optional[float], val_b: Optional[float]) -> None:
            if val_a is None and val_b is None:
                deltas[name] = MetricPeriodDelta(
                    metric_name=name,
                    period_a_value=None,
                    period_b_value=None,
                    absolute_delta=None,
                    percentage_change_pct=None,
                )
                return

            v_a = val_a or 0.0
            v_b = val_b or 0.0
            abs_diff = round(v_b - v_a, 2)
            pct_change = round(((v_b - v_a) / v_a) * 100, 2) if v_a > 0 else None

            deltas[name] = MetricPeriodDelta(
                metric_name=name,
                period_a_value=val_a,
                period_b_value=val_b,
                absolute_delta=abs_diff,
                percentage_change_pct=pct_change,
            )

        add_delta("top_10_ranking_rate_pct", metrics_a.seo_metrics.top_10_ranking_rate_pct, metrics_b.seo_metrics.top_10_ranking_rate_pct)
        add_delta("top_3_ranking_rate_pct", metrics_a.seo_metrics.top_3_ranking_rate_pct, metrics_b.seo_metrics.top_3_ranking_rate_pct)
        add_delta("ai_mention_rate_pct", metrics_a.geo_metrics.ai_mention_rate_pct, metrics_b.geo_metrics.ai_mention_rate_pct)
        add_delta("ai_citation_rate_pct", metrics_a.geo_metrics.ai_citation_rate_pct, metrics_b.geo_metrics.ai_citation_rate_pct)
        add_delta("feature_presence_rate_pct", metrics_a.answer_features.feature_presence_rate_pct, metrics_b.answer_features.feature_presence_rate_pct)
        add_delta("average_visibility_score", metrics_a.average_visibility_score, metrics_b.average_visibility_score)

        return VisibilityPeriodComparison(
            period_a_label=period_a_label,
            period_b_label=period_b_label,
            period_a_metrics=metrics_a,
            period_b_metrics=metrics_b,
            deltas=deltas,
        )
