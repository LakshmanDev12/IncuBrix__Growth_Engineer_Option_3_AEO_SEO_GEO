"""API routes for GEO (Generative Engine Optimization) collection."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    get_citation_repository,
    get_evidence_repository,
    get_observation_repository,
    get_question_repository,
)
from app.collectors.geo_collector import GEOCollector
from app.database.repositories.citation_repo import CitationRepository
from app.database.repositories.evidence_repo import EvidenceRepository
from app.database.repositories.observation_repo import ObservationRepository
from app.database.repositories.question_repo import QuestionRepository
from app.exceptions import DuplicateEntityError, EntityNotFoundError
from app.providers.ai_provider import get_ai_adapter
from app.schemas.common import ProviderType
from app.schemas.observations import GEOManualImportRequest, ObservationRead

router = APIRouter(prefix="/geo", tags=["GEO Collection"])


@router.get(
    "/assistants",
    response_model=List[Dict[str, Any]],
    summary="List supported AI assistant engines and their configuration status",
)
def list_supported_assistants() -> List[Dict[str, Any]]:
    """Retrieve capabilities and live configuration status for permitted AI assistant engines."""
    assistants = [
        ProviderType.PERPLEXITY,
        ProviderType.CHATGPT,
        ProviderType.GEMINI,
        ProviderType.CLAUDE,
        ProviderType.GOOGLE_AI_OVERVIEW,
        ProviderType.BING_COPILOT,
    ]
    results = []
    for ast in assistants:
        adapter = get_ai_adapter(provider_type=ast)
        results.append(adapter.get_capabilities())
    return results


@router.post(
    "/harvest/{question_id}",
    response_model=ObservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger automated GEO collection for a question across an AI assistant",
)
def harvest_geo_observation(
    question_id: str,
    assistant: ProviderType = Query(
        ProviderType.PERPLEXITY,
        description="Target AI assistant (perplexity, chatgpt, gemini, claude, google_ai_overview)",
    ),
    market: Optional[str] = Query(None, description="Target search/observation market override"),
    location: Optional[str] = Query(None, description="Geographic location setting override"),
    q_repo: QuestionRepository = Depends(get_question_repository),
    obs_repo: ObservationRepository = Depends(get_observation_repository),
    ev_repo: EvidenceRepository = Depends(get_evidence_repository),
    cite_repo: CitationRepository = Depends(get_citation_repository),
) -> ObservationRead:
    """Execute live query against a configured AI assistant adapter for a creator question.

    If the assistant is unconfigured or unsupported, returns an explicit UNAVAILABLE status
    without fabricating results or falsely claiming external queries occurred.
    """
    question = q_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID '{question_id}' not found.",
        )

    collector = GEOCollector(
        question_repo=q_repo,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
        citation_repo=cite_repo,
    )
    return collector.collect(
        question=question,
        assistant=assistant,
        market=market,
        location=location,
    )


@router.post(
    "/manual-import",
    response_model=ObservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import manual AI assistant transcript for assistants without accessible APIs",
)
def import_manual_geo_evidence(
    data: GEOManualImportRequest,
    q_repo: QuestionRepository = Depends(get_question_repository),
    obs_repo: ObservationRepository = Depends(get_observation_repository),
    ev_repo: EvidenceRepository = Depends(get_evidence_repository),
    cite_repo: CitationRepository = Depends(get_citation_repository),
) -> ObservationRead:
    """Ingest human-evaluated assistant responses (ChatGPT web, Claude chat, Copilot web).

    Preserves raw evidence, model versions, and extracted citation URLs with SHA-256 deduplication,
    evaluating brand mentions and citations without conflating them.
    """
    collector = GEOCollector(
        question_repo=q_repo,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
        citation_repo=cite_repo,
    )
    try:
        return collector.import_manual_evidence(data, allow_existing=False)
    except EntityNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        )
    except DuplicateEntityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        )
