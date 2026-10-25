"""GEO (Generative Engine Optimization) Collector.

Coordinates:
- Querying configured, permitted AI assistant adapters (Perplexity, ChatGPT, Claude, Gemini, Google AI Overview).
- Ingesting manual evidence transcripts for assistants without an accessible public API.
- Separate extraction of textual brand mentions vs direct website citations without conflation.
- Provenance preservation of raw responses, model versions, and citation URLs with SHA-256 deduplication.
- Safe handling of unsupported assistants without falsely claiming queries were executed.
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
from app.providers.ai_provider import BaseAIProvider, get_ai_adapter
from app.providers.base import ProviderResult
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
from app.schemas.observations import GEOManualImportRequest, ObservationCreate

logger = get_logger("incubrix.geo_collector")


class GEOCollector(BaseCollector):
    """Generative Engine Optimization (GEO) observation collector."""

    collector_name: str = "geo_collector"

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

    def collect(
        self,
        question: QuestionModel,
        assistant: ProviderType = ProviderType.PERPLEXITY,
        market: Optional[str] = None,
        location: Optional[str] = None,
        custom_adapter: Optional[BaseAIProvider] = None,
    ) -> ObservationModel:
        """Query configured generative AI assistant for creator question visibility."""
        target_market = market or question.target_market
        target_location = location or question.target_location

        adapter = custom_adapter or get_ai_adapter(provider_type=assistant)

        logger.info(
            "Executing GEO observation for question %s via %s (Model: %s, Market: %s)",
            question.id,
            adapter.provider_type.value,
            adapter.model,
            target_market,
        )

        # 1. Execute query via independent adapter
        result: ProviderResult = adapter.execute_query(
            query=question.text,
            market=target_market,
            location=target_location,
        )

        # 2. Store raw evidence artifact if payload returned
        evidence_id: Optional[str] = None
        evidence_ids: List[str] = []

        if result.raw_payload:
            payload_str = result.raw_payload.strip()
            artifact_type = (
                ArtifactType.JSON_PAYLOAD
                if payload_str.startswith(("{", "["))
                else ArtifactType.RAW_TEXT
            )
            evidence_data = EvidenceArtifactCreate(
                artifact_type=artifact_type,
                question_id=question.id,
                content=result.raw_payload,
                source_url=result.source_url,
                collected_by=f"{adapter.provider_type.value}_geo_collector",
                metadata={
                    "assistant": adapter.provider_type.value,
                    "model": result.ai_model_version or adapter.model,
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

        # 3. Analyze mentions and direct citations without conflation
        if result.collection_status == CollectionStatus.SUCCESS:
            analysis: MentionAnalysis = self.analyzer.analyze(
                raw_answer=result.raw_answer,
                quoted_domains=result.quoted_domains,
                has_link_tracking=bool(result.quoted_urls or result.quoted_domains),
            )
            mention_status = analysis.incubrix_mentioned
            citation_status = analysis.incubrix_cited
            competitors = analysis.competitors_observed
            quoted_domains = analysis.quoted_domains
            opportunities = analysis.citation_opportunities
        else:
            # Explicit unknown / unavailable states on unconfigured or failed queries
            mention_status = MentionStatus.UNKNOWN
            citation_status = CitationStatus.UNAVAILABLE
            competitors = []
            quoted_domains = result.quoted_domains
            opportunities = []

        # 4. Construct ObservationCreate
        obs_create = ObservationCreate(
            question_id=question.id,
            market=target_market,
            location=target_location,
            measured_at=datetime.now(timezone.utc),
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
            ai_model_version=result.ai_model_version or adapter.model,
            collection_status=result.collection_status,
            error_code=result.error_code,
            error_details=result.error_details,
            metadata={
                "assistant": adapter.provider_type.value,
                "model": result.ai_model_version or adapter.model,
                **result.meta,
            },
        )

        # 5. Calculate visibility score (None if unconfigured / failed)
        score = (
            calculate_visibility_score(obs_create)
            if result.collection_status == CollectionStatus.SUCCESS
            else None
        )

        # 6. Record observation with deterministic daily fingerprint
        observation, _ = self.observation_repo.record_observation(
            obs_create,
            visibility_score=score,
            allow_existing=True,
        )

        # 7. Record citation target gaps
        if self.citation_repo and opportunities:
            for opp in opportunities[:5]:
                target_create = CitationTargetCreate(
                    target_domain=opp["target_domain"],
                    question_id=question.id,
                    observation_id=observation.id,
                    competitor_domain=opp.get("competitor_domain"),
                    gap_type=opp["gap_type"],
                    notes=f"Identified via {adapter.provider_type.value} GEO observation.",
                )
                self.citation_repo.create_target(target_create)

        return observation

    def import_manual_evidence(
        self,
        request: GEOManualImportRequest,
        allow_existing: bool = True,
    ) -> ObservationModel:
        """Import manual assistant transcript for platforms without an accessible public API."""
        # 1. Validate question exists
        question = self.question_repo.get_by_id(request.question_id)
        if not question:
            raise EntityNotFoundError("Question", request.question_id)

        # 2. Validate citation URLs
        clean_citation_urls: List[str] = []
        for raw_url in request.citation_urls:
            clean_url, err = validate_url(raw_url)
            if err:
                raise ValueError(f"Invalid citation URL '{raw_url}': {err}")
            if clean_url:
                clean_citation_urls.append(clean_url)

        # 3. Determine artifact type
        content_stripped = request.raw_response.strip()
        if content_stripped.startswith(("{", "[")):
            artifact_type = ArtifactType.JSON_PAYLOAD
        elif any(tag in content_stripped.lower() for tag in ("<html", "<!doctype html", "<div", "<body", "<p>")):
            artifact_type = ArtifactType.HTML_SNAPSHOT
        else:
            artifact_type = ArtifactType.RAW_TEXT

        # 4. Store raw evidence with SHA-256 deduplication
        target_market = request.market or question.target_market
        target_location = request.location or question.target_location

        evidence_create = EvidenceArtifactCreate(
            artifact_type=artifact_type,
            question_id=question.id,
            content=request.raw_response,
            source_url=request.source_url,
            collected_by=request.operator_id,
            metadata={
                "assistant": request.assistant.value,
                "model": request.ai_model_version,
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
        quoted_domains = [extract_domain(u) for u in clean_citation_urls if extract_domain(u)]
        quoted_domains = sorted(list(set(quoted_domains)))

        # 6. Analyze brand mentions vs direct citations without conflation
        raw_answer_text = request.raw_response if artifact_type == ArtifactType.RAW_TEXT else None
        analysis: MentionAnalysis = self.analyzer.analyze(
            raw_answer=raw_answer_text,
            quoted_domains=quoted_domains,
            has_link_tracking=bool(clean_citation_urls),
        )

        observed_features = ["generative_synthesis"]
        if clean_citation_urls:
            observed_features.append("citations")
        if raw_answer_text:
            observed_features.append("direct_answer")

        # 7. Construct ObservationCreate
        obs_create = ObservationCreate(
            question_id=question.id,
            market=target_market,
            location=target_location,
            measured_at=request.measured_at or datetime.now(timezone.utc),
            provider=request.assistant,
            observation_type=(
                ObservationType.HYBRID_OVERVIEW
                if request.assistant == ProviderType.GOOGLE_AI_OVERVIEW
                else ObservationType.AI_ASSISTANT
            ),
            raw_answer=raw_answer_text,
            artifact_id=evidence_entity.id,
            incubrix_mentioned=analysis.incubrix_mentioned,
            incubrix_cited=analysis.incubrix_cited,
            competitors_observed=analysis.competitors_observed,
            quoted_domains=quoted_domains,
            quoted_urls=clean_citation_urls,
            observed_features=observed_features,
            evidence_ids=[evidence_entity.id],
            rank_position=None,
            answer_box_present=None,
            ai_model_version=request.ai_model_version,
            collection_status=CollectionStatus.SUCCESS,
            meta={
                "operator_id": request.operator_id,
                "collector_notes": request.collector_notes,
                "model": request.ai_model_version,
                **request.meta,
            },
        )

        # 8. Compute visibility score
        score = calculate_visibility_score(obs_create)

        # 9. Record observation with deterministic daily fingerprint
        observation, _ = self.observation_repo.record_observation(
            obs_create,
            visibility_score=score,
            allow_existing=allow_existing,
        )

        # 10. Record citation target gaps
        if self.citation_repo and analysis.citation_opportunities:
            for opp in analysis.citation_opportunities[:5]:
                target_create = CitationTargetCreate(
                    target_domain=opp["target_domain"],
                    question_id=question.id,
                    observation_id=observation.id,
                    competitor_domain=opp.get("competitor_domain"),
                    gap_type=opp["gap_type"],
                    notes=f"Identified via manual GEO import ({request.assistant.value}).",
                )
                self.citation_repo.create_target(target_create)

        return observation
