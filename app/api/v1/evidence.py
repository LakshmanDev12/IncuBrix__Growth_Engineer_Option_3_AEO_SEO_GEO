"""API routes for Source Evidence Artifacts."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_evidence_repository
from app.database.repositories.evidence_repo import EvidenceRepository
from app.exceptions import DuplicateEntityError
from app.schemas.evidence import EvidenceArtifactCreate, EvidenceArtifactRead

router = APIRouter(prefix="/evidence", tags=["Source Evidence"])


@router.post(
    "",
    response_model=EvidenceArtifactRead,
    status_code=status.HTTP_201_CREATED,
    summary="Store a source evidence artifact",
)
def store_evidence(
    data: EvidenceArtifactCreate,
    repo: EvidenceRepository = Depends(get_evidence_repository),
) -> EvidenceArtifactRead:
    """Store raw response or artifact reference with SHA-256 deduplication."""
    try:
        entity, _ = repo.store_evidence(data, allow_existing=False)
        return entity
    except DuplicateEntityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        )


@router.get(
    "",
    response_model=List[EvidenceArtifactRead],
    summary="List stored evidence artifacts",
)
def list_evidence(
    question_id: Optional[str] = Query(None, description="Filter by question ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: EvidenceRepository = Depends(get_evidence_repository),
) -> List[EvidenceArtifactRead]:
    """Retrieve stored evidence artifacts."""
    if question_id:
        return repo.list_by_question(question_id)
    return repo.list(skip=skip, limit=limit)


@router.get(
    "/{evidence_id}",
    response_model=EvidenceArtifactRead,
    summary="Get evidence artifact by ID",
)
def get_evidence(
    evidence_id: str,
    repo: EvidenceRepository = Depends(get_evidence_repository),
) -> EvidenceArtifactRead:
    """Fetch an evidence artifact by ID."""
    entity = repo.get_by_id(evidence_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence artifact with ID '{evidence_id}' not found.",
        )
    return entity
