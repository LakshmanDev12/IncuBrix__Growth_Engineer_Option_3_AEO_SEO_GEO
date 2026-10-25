"""API routes for Visibility Observations."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    get_ai_provider,
    get_citation_repository,
    get_evidence_repository,
    get_observation_repository,
    get_question_repository,
    get_search_provider,
)
from app.collectors.automated_collector import AutomatedCollector
from app.collectors.manual_collector import ManualEvidenceAdapter
from app.database.repositories.citation_repo import CitationRepository
from app.database.repositories.evidence_repo import EvidenceRepository
from app.database.repositories.observation_repo import ObservationRepository
from app.database.repositories.question_repo import QuestionRepository
from app.engine.scoring import calculate_visibility_score
from app.exceptions import DuplicateEntityError, EntityNotFoundError
from app.providers.ai_provider import AIProvider
from app.providers.search_provider import SearchProvider
from app.schemas.common import ProviderType
from app.schemas.observations import (
    ManualEvidenceImportRequest,
    ObservationCreate,
    ObservationRead,
)

router = APIRouter(tags=["Visibility Observations"])


@router.post(
    "/observations/manual-import",
    response_model=ObservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import manual search or AI assistant visibility evidence",
)
def import_manual_evidence(
    data: ManualEvidenceImportRequest,
    q_repo: QuestionRepository = Depends(get_question_repository),
    ev_repo: EvidenceRepository = Depends(get_evidence_repository),
    obs_repo: ObservationRepository = Depends(get_observation_repository),
    cite_repo: CitationRepository = Depends(get_citation_repository),
) -> ObservationRead:
    """Import and process operator-collected visibility evidence.

    Stores raw text/HTML/JSON evidence artifacts, parses mentions and citations,
    scores visibility, and records observations linked to creator questions.
    """
    adapter = ManualEvidenceAdapter(
        question_repo=q_repo,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
        citation_repo=cite_repo,
    )
    try:
        observation = adapter.import_evidence(data, allow_existing=False)
        return observation
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


@router.post(
    "/observations",
    response_model=ObservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a visibility observation",
)
def create_observation(
    data: ObservationCreate,
    obs_repo: ObservationRepository = Depends(get_observation_repository),
    q_repo: QuestionRepository = Depends(get_question_repository),
) -> ObservationRead:
    """Record an operator or automated search/AI visibility observation."""
    # Verify foreign key question exists
    question = q_repo.get_by_id(data.question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID '{data.question_id}' does not exist.",
        )

    # Compute transparent heuristic score
    score = calculate_visibility_score(data)

    try:
        entity, created = obs_repo.record_observation(
            data, visibility_score=score, allow_existing=False
        )
        return entity
    except DuplicateEntityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        )


@router.get(
    "/observations",
    response_model=List[ObservationRead],
    summary="List visibility observations",
)
def list_observations(
    question_id: Optional[str] = Query(None, description="Filter by question ID"),
    market: Optional[str] = Query(None, description="Filter by target market (e.g. US, UK)"),
    provider: Optional[str] = Query(None, description="Filter by provider (e.g. google_search, chatgpt)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: ObservationRepository = Depends(get_observation_repository),
) -> List[ObservationRead]:
    """Retrieve observations with pagination and optional multi-attribute filters."""
    if market or provider or question_id:
        return repo.filter_observations(
            question_id=question_id,
            market=market,
            provider=provider,
            skip=skip,
            limit=limit,
        )
    return repo.list(skip=skip, limit=limit)


@router.get(
    "/observations/{observation_id}",
    response_model=ObservationRead,
    summary="Get observation by ID",
)
def get_observation(
    observation_id: str,
    repo: ObservationRepository = Depends(get_observation_repository),
) -> ObservationRead:
    """Fetch a single visibility observation by ID."""
    obs = repo.get_by_id(observation_id)
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation with ID '{observation_id}' not found.",
        )
    return obs


@router.get(
    "/summary",
    response_model=Dict[str, Any],
    summary="Get aggregated visibility summary metrics",
)
def get_visibility_summary(
    market: Optional[str] = Query(None, description="Filter by target market"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    repo: ObservationRepository = Depends(get_observation_repository),
) -> Dict[str, Any]:
    """Descriptive aggregate metrics isolating known results from unknown/unavailable states."""
    return repo.get_summary_metrics(market=market, provider=provider)


@router.post(
    "/observations/harvest/{question_id}",
    response_model=ObservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger automated visibility observation harvest for a question",
)
def harvest_observation(
    question_id: str,
    provider_type: ProviderType = Query(
        ProviderType.GOOGLE_SEARCH,
        description="Search engine or AI platform provider to query",
    ),
    market: Optional[str] = Query(None, description="Override target search market"),
    location: Optional[str] = Query(None, description="Override geographic location"),
    q_repo: QuestionRepository = Depends(get_question_repository),
    obs_repo: ObservationRepository = Depends(get_observation_repository),
    ev_repo: EvidenceRepository = Depends(get_evidence_repository),
    cite_repo: CitationRepository = Depends(get_citation_repository),
    search_provider: SearchProvider = Depends(get_search_provider),
    ai_provider: AIProvider = Depends(get_ai_provider),
) -> ObservationRead:
    """Harvest an observation from a search engine or AI platform.

    Preserves raw evidence, parses mentions/citations, scores visibility,
    and deduplicates results by daily fingerprint.
    """
    question = q_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID '{question_id}' not found.",
        )

    provider = search_provider if provider_type == ProviderType.GOOGLE_SEARCH else ai_provider
    collector = AutomatedCollector(
        provider=provider,
        evidence_repo=ev_repo,
        observation_repo=obs_repo,
        citation_repo=cite_repo,
    )
    return collector.collect(question=question, market=market, location=location)
