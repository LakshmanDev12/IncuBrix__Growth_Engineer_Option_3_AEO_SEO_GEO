"""Automated Observation Collector and Ingestion Pipeline.

Orchestrates querying search/AI providers, persisting raw evidence artifacts,
analyzing brand and competitor mentions, computing visibility heuristics,
and recording deduplicated observations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.collectors.base import BaseCollector
from app.database.models.observation import ObservationModel
from app.database.models.question import QuestionModel
from app.database.repositories.citation_repo import CitationRepository
from app.database.repositories.evidence_repo import EvidenceRepository
from app.database.repositories.observation_repo import ObservationRepository
from app.engine.mention_analyzer import MentionAnalysis, MentionAnalyzer
from app.engine.scoring import calculate_visibility_score
from app.logging_config import get_logger
from app.providers.base import BaseProvider, ProviderResult
from app.schemas.citation import CitationTargetCreate
from app.schemas.common import (
    ArtifactType,
    CitationStatus,
    CollectionStatus,
    MentionStatus,
)
from app.schemas.evidence import EvidenceArtifactCreate
from app.schemas.observations import ObservationCreate

logger = get_logger("incubrix.collector")


class AutomatedCollector(BaseCollector):
    """Automated observation collector executing queries against external providers."""

    collector_name: str = "automated_collector"

    def __init__(
        self,
        provider: BaseProvider,
        evidence_repo: EvidenceRepository,
        observation_repo: ObservationRepository,
        citation_repo: Optional[CitationRepository] = None,
        analyzer: Optional[MentionAnalyzer] = None,
    ) -> None:
        self.provider = provider
        self.evidence_repo = evidence_repo
        self.observation_repo = observation_repo
        self.citation_repo = citation_repo
        self.analyzer = analyzer or MentionAnalyzer()

    def collect(
        self,
        question: QuestionModel,
        market: Optional[str] = None,
        location: Optional[str] = None,
    ) -> ObservationModel:
        """Collect visibility data for a question using the configured provider."""
        target_market = market or question.target_market
        target_location = location or question.target_location

        logger.info(
            "Executing automated observation for question %s via %s (Market: %s)",
            question.id,
            self.provider.provider_type.value,
            target_market,
        )

        # 1. Execute query via provider
        result: ProviderResult = self.provider.execute_query(
            query=question.text,
            market=target_market,
            location=target_location,
        )

        # 2. Store raw evidence artifact with SHA-256 deduplication
        evidence_id: Optional[str] = None
        evidence_ids: List[str] = []

        if result.raw_payload:
            artifact_type = (
                ArtifactType.JSON_PAYLOAD
                if result.raw_payload.strip().startswith(("{", "["))
                else ArtifactType.RAW_TEXT
            )
            evidence_data = EvidenceArtifactCreate(
                artifact_type=artifact_type,
                question_id=question.id,
                content=result.raw_payload,
                source_url=result.source_url,
                collected_by=f"{self.provider.provider_type.value}_collector",
                metadata={
                    "provider": self.provider.provider_type.value,
                    "market": target_market,
                    "location": target_location,
                    "collection_status": result.collection_status.value,
                    **result.meta,
                },
            )
            evidence_entity, _ = self.evidence_repo.store_evidence(
                evidence_data, allow_existing=True
            )
            evidence_id = evidence_entity.id
            evidence_ids.append(evidence_id)

        # 3. Analyze mentions and citations if response contains text or links
        if result.collection_status == CollectionStatus.SUCCESS:
            analysis: MentionAnalysis = self.analyzer.analyze(
                raw_answer=result.raw_answer,
                quoted_domains=result.quoted_domains,
                has_link_tracking=bool(result.quoted_domains),
            )
            mention_status = analysis.incubrix_mentioned
            citation_status = analysis.incubrix_cited
            competitors = analysis.competitors_observed
            quoted_domains = analysis.quoted_domains
            opportunities = analysis.citation_opportunities
        else:
            # On failed or unavailable collections, strictly preserve explicit unknown/unavailable states
            mention_status = MentionStatus.UNKNOWN
            citation_status = CitationStatus.UNAVAILABLE
            competitors = []
            quoted_domains = result.quoted_domains
            opportunities = []

        # 4. Construct observation payload
        obs_create = ObservationCreate(
            question_id=question.id,
            market=target_market,
            location=target_location,
            provider=result.provider,
            observation_type=result.observation_type,
            raw_answer=result.raw_answer,
            artifact_id=evidence_id,
            incubrix_mentioned=mention_status,
            incubrix_cited=citation_status,
            competitors_observed=competitors,
            quoted_domains=quoted_domains,
            quoted_urls=result.quoted_urls,
            observed_features=result.observed_features,
            evidence_ids=evidence_ids,
            rank_position=result.rank_position,
            answer_box_present=result.answer_box_present,
            ai_model_version=result.ai_model_version,
            collection_status=result.collection_status,
            error_code=result.error_code,
            error_details=result.error_details,
            metadata=result.meta,
        )

        # 5. Calculate visibility score
        score = calculate_visibility_score(obs_create)

        # 6. Record observation with deterministic fingerprint deduplication
        observation, _ = self.observation_repo.record_observation(
            obs_create,
            visibility_score=score,
            allow_existing=True,
        )

        # 7. Record citation targets if gaps identified
        if self.citation_repo and opportunities:
            for opp in opportunities[:5]:  # Capture top 5 authority/competitor gaps
                target_create = CitationTargetCreate(
                    target_domain=opp["target_domain"],
                    question_id=question.id,
                    observation_id=observation.id,
                    competitor_domain=opp.get("competitor_domain"),
                    gap_type=opp["gap_type"],
                    notes=f"Identified via {self.provider.provider_type.value} observation.",
                )
                self.citation_repo.create_target(target_create)

        return observation

    def collect_batch(
        self,
        questions: List[QuestionModel],
        market: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[ObservationModel]:
        """Collect observations for multiple creator questions."""
        observations: List[ObservationModel] = []
        for q in questions:
            obs = self.collect(q, market=market, location=location)
            observations.append(obs)
        return observations
