"""Observation repository managing visibility records, fingerprint deduplication, and metrics."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models.observation import ObservationModel
from app.database.repositories.base import BaseRepository
from app.exceptions import DuplicateEntityError
from app.schemas.common import CitationStatus, MentionStatus
from app.schemas.observations import ObservationCreate


class ObservationRepository(BaseRepository[ObservationModel]):
    """Repository managing Visibility Observations."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, ObservationModel)

    def get_by_fingerprint(self, fingerprint: str) -> Optional[ObservationModel]:
        """Look up observation by unique daily deterministic fingerprint."""
        stmt = select(ObservationModel).where(ObservationModel.fingerprint == fingerprint)
        return self.db.execute(stmt).scalar_one_or_none()

    def record_observation(
        self,
        data: ObservationCreate,
        visibility_score: Optional[int] = None,
        allow_existing: bool = True,
    ) -> Tuple[ObservationModel, bool]:
        """Record a visibility observation with deduplication and integrity checks."""
        fingerprint = data.compute_fingerprint()
        existing = self.get_by_fingerprint(fingerprint)
        if existing:
            if not allow_existing:
                raise DuplicateEntityError("Observation", "fingerprint", fingerprint)
            # If existing record was a failed/unavailable placeholder and incoming is a successful observation, upgrade it
            status_val = (
                data.collection_status.value
                if hasattr(data.collection_status, "value")
                else str(data.collection_status)
            )
            if existing.collection_status in ("unavailable", "failed") and status_val == "success":
                existing.raw_answer = data.raw_answer
                existing.artifact_id = data.artifact_id
                existing.incubrix_mentioned = (
                    data.incubrix_mentioned.value
                    if hasattr(data.incubrix_mentioned, "value")
                    else str(data.incubrix_mentioned)
                )
                existing.incubrix_cited = (
                    data.incubrix_cited.value
                    if hasattr(data.incubrix_cited, "value")
                    else str(data.incubrix_cited)
                )
                existing.competitors_observed = data.competitors_observed
                existing.quoted_domains = data.quoted_domains
                existing.quoted_urls = data.quoted_urls
                existing.observed_features = data.observed_features
                existing.evidence_ids = data.evidence_ids
                existing.rank_position = data.rank_position
                existing.answer_box_present = data.answer_box_present
                existing.ai_model_version = data.ai_model_version
                existing.collection_status = status_val
                existing.error_code = data.error_code
                existing.error_details = data.error_details
                existing.meta = data.meta
                existing.visibility_score = visibility_score
                self.db.commit()
                self.db.refresh(existing)
                return existing, True
            return existing, False

        entity = ObservationModel(
            question_id=data.question_id,
            market=data.market,
            location=data.location,
            measured_at=data.measured_at,
            provider=data.provider.value,
            observation_type=data.observation_type.value,
            raw_answer=data.raw_answer,
            artifact_id=data.artifact_id,
            incubrix_mentioned=data.incubrix_mentioned.value,
            incubrix_cited=data.incubrix_cited.value,
            competitors_observed=data.competitors_observed,
            quoted_domains=data.quoted_domains,
            quoted_urls=data.quoted_urls,
            observed_features=data.observed_features,
            evidence_ids=data.evidence_ids,
            rank_position=data.rank_position,
            answer_box_present=data.answer_box_present,
            ai_model_version=data.ai_model_version,
            collection_status=data.collection_status.value,
            error_code=data.error_code,
            error_details=data.error_details,
            meta=data.meta,
            visibility_score=visibility_score,
            fingerprint=fingerprint,
        )
        return self.create(entity), True

    def list_by_question(
        self, question_id: str, skip: int = 0, limit: int = 100
    ) -> List[ObservationModel]:
        """Return all observations for a specific question."""
        stmt = (
            select(ObservationModel)
            .where(ObservationModel.question_id == question_id)
            .order_by(ObservationModel.measured_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def filter_observations(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        market: Optional[str] = None,
        provider: Optional[str] = None,
        question_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 10000,
    ) -> List[ObservationModel]:
        """Query observations applying optional multi-attribute filters."""
        stmt = select(ObservationModel)
        if question_id:
            stmt = stmt.where(ObservationModel.question_id == question_id)
        if market:
            stmt = stmt.where(ObservationModel.market == market.upper())
        if provider:
            stmt = stmt.where(ObservationModel.provider == provider.lower())
        if status:
            stmt = stmt.where(ObservationModel.collection_status == status.lower())
        if start_date:
            stmt = stmt.where(ObservationModel.measured_at >= start_date)
        if end_date:
            stmt = stmt.where(ObservationModel.measured_at <= end_date)

        stmt = stmt.order_by(ObservationModel.measured_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def get_summary_metrics(
        self,
        market: Optional[str] = None,
        provider: Optional[str] = None,
        question_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        deduplicate: bool = True,
    ) -> Dict[str, Any]:
        """Compute aggregated visibility metrics honoring explicit unknown states.

        Never treats missing evidence or unknown state as negative.
        """
        from app.engine.visibility_metrics import VisibilityMetricsCalculator

        obs_list = self.filter_observations(
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
        }

        report = VisibilityMetricsCalculator.calculate_metrics(
            obs_list,
            deduplicate=deduplicate,
            filter_context=filter_ctx,
        )

        return {
            "total_observations": report.total_raw_observations,
            "deduplicated_observations": report.deduplicated_observations,
            "valid_evaluated_observations": report.valid_evaluated_observations,
            "scored_observations": report.scored_observations_count,
            "average_visibility_score": report.average_visibility_score,
            "score_distribution": report.score_distribution,
            "mention_stats": {
                "mentioned": report.geo_metrics.mentioned_count,
                "not_mentioned": report.geo_metrics.not_mentioned_count,
                "unknown_or_unavailable": report.geo_metrics.unknown_mention_count,
                "positive_mention_rate_pct": report.geo_metrics.ai_mention_rate_pct,
            },
            "citation_stats": {
                "cited": report.geo_metrics.cited_count,
                "not_cited": report.geo_metrics.not_cited_count,
                "unknown_or_unavailable": report.geo_metrics.unavailable_or_unknown_citation_count,
                "positive_citation_rate_pct": report.geo_metrics.ai_citation_rate_pct,
            },
            "seo_metrics": report.seo_metrics.model_dump(),
            "geo_metrics": report.geo_metrics.model_dump(),
            "answer_features": report.answer_features.model_dump(),
            "excluded_observations": report.excluded_observations.model_dump(),
            "filter_context": report.filter_context,
            "methodology_note": "Evaluations isolate confirmed observations from missing/unknown evidence without false negatives.",
        }
