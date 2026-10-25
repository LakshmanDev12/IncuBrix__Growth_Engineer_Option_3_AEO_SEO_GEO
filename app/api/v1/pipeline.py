"""API routes for Pipeline Runs and Orchestration."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_pipeline_repository
from app.database.repositories.pipeline_repo import PipelineRunRepository
from app.pipeline.cost_tracker import RATE_CARDS, CostTracker
from app.pipeline.orchestrator import PipelineOrchestrator
from app.schemas.pipeline import (
    PipelineExecutionRequest,
    PipelineExecutionResponse,
    PipelineRunCreate,
    PipelineRunRead,
)

router = APIRouter(prefix="/pipeline", tags=["Pipeline Execution"])


@router.post(
    "/run",
    response_model=PipelineExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute end-to-end or custom pipeline run",
)
def execute_pipeline(
    request: PipelineExecutionRequest,
    db: Session = Depends(get_db),
) -> PipelineExecutionResponse:
    """Execute integrated visibility pipeline (ingestion, collection, scoring, audit, content, reporting)."""
    orchestrator = PipelineOrchestrator(
        db=db,
        cost_tracker=CostTracker(),
        max_retries=request.max_retries,
    )
    return orchestrator.run(request)


@router.post(
    "/refresh",
    response_model=PipelineExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute refresh measurement pipeline",
)
def execute_refresh_pipeline(
    market: str = Query(None, description="Optional target market filter"),
    provider: str = Query(None, description="Optional target provider filter"),
    db: Session = Depends(get_db),
) -> PipelineExecutionResponse:
    """Refresh measurements for existing approved questions and update visibility scores and reports."""
    request = PipelineExecutionRequest(
        mode="refresh",
        market=market,
        provider=provider,
        skip_audit=True,
        skip_content=True,
    )
    orchestrator = PipelineOrchestrator(
        db=db,
        cost_tracker=CostTracker(),
    )
    return orchestrator.run(request)


@router.get(
    "/cost-rates",
    summary="Get standard published API unit cost benchmarks",
)
def get_cost_rate_cards() -> Dict[str, Any]:
    """Retrieve rate card benchmarks used for estimated and actual API cost telemetry."""
    return RATE_CARDS


@router.post(
    "/runs",
    response_model=PipelineRunRead,
    status_code=status.HTTP_201_CREATED,
    summary="Start and track a new pipeline run",
)
def start_pipeline_run(
    data: PipelineRunCreate,
    repo: PipelineRunRepository = Depends(get_pipeline_repository),
) -> PipelineRunRead:
    """Record the initiation of an automated pipeline run."""
    return repo.start_run(data)


@router.get(
    "/runs",
    response_model=List[PipelineRunRead],
    summary="List pipeline runs",
)
def list_pipeline_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: PipelineRunRepository = Depends(get_pipeline_repository),
) -> List[PipelineRunRead]:
    """Retrieve history of pipeline runs."""
    return repo.list(skip=skip, limit=limit)


@router.get(
    "/runs/{run_id}",
    response_model=PipelineRunRead,
    summary="Get status of a pipeline run",
)
def get_pipeline_run(
    run_id: str,
    repo: PipelineRunRepository = Depends(get_pipeline_repository),
) -> PipelineRunRead:
    """Fetch status and progress telemetry for a pipeline run."""
    run = repo.get_by_id(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run with ID '{run_id}' not found.",
        )
    return run
