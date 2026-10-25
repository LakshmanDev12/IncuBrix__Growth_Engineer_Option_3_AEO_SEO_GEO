"""Manual Evidence-Import Adapter and Observation Collector.

Provides:
- Ingestion of operator-submitted search and AI visibility evidence.
- Validation of creator question associations and quoted source URLs.
- Raw evidence artifact preservation with SHA-256 hash deduplication.
- Extraction of quoted domains and observed answer features.
- Brand mention and citation analysis with operator override support.
- Scoring, fingerprint deduplication, and citation opportunity discovery.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.collectors.base import BaseCollector
from app.database.models.observation import ObservationModel
from app.database.models.question import QuestionModel
from app.database.repositories.citation_repo import CitationRepository
from app.database.repositories.evidence_repo import EvidenceRepository
from app.database.repositories.observation_repo import ObservationRepository
from app.database.repositories.question_repo import QuestionRepository
from app.engine.mention_analyzer import MentionAnalysis, MentionAnalyzer
from app.engine.normalizer import extract_domain
from app.engine.question_ingestion import validate_url
from app.engine.scoring import calculate_visibility_score
from app.exceptions import EntityNotFoundError
from app.logging_config import get_logger
from app.schemas.citation import CitationTargetCreate
from app.schemas.common import (
    ArtifactType,
    CitationStatus,
    CollectionStatus,
    MentionStatus,
    ObservationType,
    ProviderType,
)
from app.schemas.evidence import EvidenceArtifactCreate
from app.schemas.observations import (
    ManualEvidenceImportRequest,
    ObservationCreate,
)

logger = get_logger("incubrix.manual_collector")


class ManualEvidenceAdapter(BaseCollector):
    """Adapter for importing and processing operator-submitted manual evidence."""

    collector_name: str = "manual_evidence_adapter"

    def __init__(
        self,
        question_repo: QuestionRepository,
        evidence_repo: EvidenceRepository,
        observation_repo: ObservationRepository,
        citation_repo: Optional[CitationRepository] = None,
        analyzer: Optional[MentionAnalyzer] = None,
    ) -> None:
        self.question_repo = question_repo
        self.evidence_repo = evidence_repo
        self.observation_repo = observation_repo
        self.citation_repo = citation_repo
        self.analyzer = analyzer or MentionAnalyzer()

    def import_evidence(
        self,
        request: ManualEvidenceImportRequest,
        allow_existing: bool = True,
    ) -> ObservationModel:
        """Process manual evidence submission with validation, provenance, and scoring."""
        # 1. Validate question exists
        question = self.question_repo.get_by_id(request.question_id)
        if not question:
            raise EntityNotFoundError("Question", request.question_id)

        # 2. Validate quoted source URLs
        clean_quoted_urls: List[str] = []
        for raw_url in request.quoted_source_urls:
            clean_url, err = validate_url(raw_url)
            if err:
                raise ValueError(f"Invalid quoted source URL '{raw_url}': {err}")
            if clean_url:
                clean_quoted_urls.append(clean_url)

        # Validate source_url if provided
        clean_source_url = None
        if request.source_url:
            clean_source_url, err = validate_url(request.source_url)
            if err:
                raise ValueError(f"Invalid source URL '{request.source_url}': {err}")

        # 3. Determine artifact type
        content_stripped = request.raw_evidence.strip()
        if content_stripped.startswith(("{", "[")):
            artifact_type = ArtifactType.JSON_PAYLOAD
        elif any(tag in content_stripped.lower() for tag in ("<html", "<!doctype html", "<div", "<body", "<p>")):
            artifact_type = ArtifactType.HTML_SNAPSHOT
        else:
            artifact_type = ArtifactType.RAW_TEXT

        # 4. Store raw evidence artifact with SHA-256 deduplication
        target_market = request.market or question.target_market
        target_location = request.location or question.target_location

        evidence_create = EvidenceArtifactCreate(
            artifact_type=artifact_type,
            question_id=question.id,
            content=request.raw_evidence,
            source_url=clean_source_url,
            collected_by=request.operator_id or "manual_operator",
            metadata={
                "provider": request.provider.value,
                "observation_type": request.observation_type.value,
                "market": target_market,
                "location": target_location,
                "collector_notes": request.collector_notes,
                "operator_id": request.operator_id,
                **request.meta,
            },
        )
        evidence_entity, _ = self.evidence_repo.store_evidence(
            evidence_create, allow_existing=True
        )

        # 5. Extract quoted domains
        quoted_domains = [extract_domain(u) for u in clean_quoted_urls if extract_domain(u)]
        quoted_domains = sorted(list(set(quoted_domains)))

        # 6. Analyze or apply explicit overrides for mentions and citations
        raw_answer_text = request.raw_answer or (
            request.raw_evidence if artifact_type == ArtifactType.RAW_TEXT else None
        )

        analysis: MentionAnalysis = self.analyzer.analyze(
            raw_answer=raw_answer_text,
            quoted_domains=quoted_domains,
            has_link_tracking=bool(quoted_domains),
        )

        # Explicit operator overrides take precedence over automated extraction
        mention_status = (
            request.incubrix_mentioned
            if request.incubrix_mentioned is not None
            else analysis.incubrix_mentioned
        )
        citation_status = (
            request.incubrix_cited
            if request.incubrix_cited is not None
            else analysis.incubrix_cited
        )
        competitors = (
            request.competitors_observed
            if request.competitors_observed is not None
            else analysis.competitors_observed
        )
        opportunities = analysis.citation_opportunities

        # Determine answer box presence from observed features
        answer_box_present = None
        if request.observed_features:
            answer_box_present = any(
                f in request.observed_features for f in ("answer_box", "featured_snippet")
            )

        # 7. Construct ObservationCreate
        obs_create = ObservationCreate(
            question_id=question.id,
            market=target_market,
            location=target_location,
            measured_at=request.measured_at or datetime.now(timezone.utc),
            provider=request.provider,
            observation_type=request.observation_type,
            raw_answer=raw_answer_text,
            artifact_id=evidence_entity.id,
            incubrix_mentioned=mention_status,
            incubrix_cited=citation_status,
            competitors_observed=competitors,
            quoted_domains=quoted_domains,
            quoted_urls=clean_quoted_urls,
            observed_features=request.observed_features,
            evidence_ids=[evidence_entity.id],
            rank_position=request.rank_position,
            answer_box_present=answer_box_present,
            collection_status=CollectionStatus.SUCCESS,
            meta={
                "operator_id": request.operator_id,
                "collector_notes": request.collector_notes,
                **request.meta,
            },
        )

        # 8. Compute visibility score
        score = calculate_visibility_score(obs_create)

        # 9. Record observation with deterministic daily fingerprint deduplication
        observation, _ = self.observation_repo.record_observation(
            obs_create,
            visibility_score=score,
            allow_existing=allow_existing,
        )

        # 10. Record citation targets if gaps identified
        if self.citation_repo and opportunities:
            for opp in opportunities[:5]:
                target_create = CitationTargetCreate(
                    target_domain=opp["target_domain"],
                    question_id=question.id,
                    observation_id=observation.id,
                    competitor_domain=opp.get("competitor_domain"),
                    gap_type=opp["gap_type"],
                    notes=f"Identified via manual evidence import ({request.provider.value}).",
                )
                self.citation_repo.create_target(target_create)

        return observation

    def collect(
        self,
        question: QuestionModel,
        market: Optional[str] = None,
        location: Optional[str] = None,
    ) -> ObservationCreate:
        """Create a pending manual observation payload ready for operator input."""
        return ObservationCreate(
            question_id=question.id,
            market=market or question.target_market,
            location=location or question.target_location,
            collection_status=CollectionStatus.PENDING,
            error_details="Awaiting manual operator observation entry.",
        )


# Backward compatibility alias
ManualCollector = ManualEvidenceAdapter
