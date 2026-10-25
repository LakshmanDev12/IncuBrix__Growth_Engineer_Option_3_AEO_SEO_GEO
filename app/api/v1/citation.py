"""API routes for Citation Targets and Opportunity Intelligence."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_citation_repository, get_db
from app.content.generator import ContentCitationEngine
from app.database.repositories.citation_repo import CitationRepository
from app.schemas.citation import (
    CitationTargetCreate,
    CitationTargetRead,
    SeedCitationsResponse,
)

router = APIRouter(prefix="/citations", tags=["Citation Intelligence Engine"])


@router.post(
    "/seed-catalog",
    response_model=SeedCitationsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Seed 30 real third-party citation opportunities",
)
def seed_citations_catalog(
    db: Session = Depends(get_db),
) -> SeedCitationsResponse:
    """Populate the database with 30 specific, real-world citation opportunities.

    Captures authority domains, verified target URLs, creator question associations,
    domain authority scores, and legitimate potential outreach angles.
    """
    seeded = ContentCitationEngine.seed_thirty_citation_opportunities(db)
    domains = sorted(list({t.target_domain for t in seeded}))
    return SeedCitationsResponse(
        total_seeded=len(seeded),
        domains_seeded=domains,
        message=f"Successfully persisted {len(seeded)} real third-party citation opportunities across {len(domains)} unique authority domains.",
    )


@router.get(
    "/targets",
    response_model=List[CitationTargetRead],
    summary="List and filter citation target opportunities",
)
def list_citation_targets(
    domain: Optional[str] = Query(None, description="Filter by target domain (e.g. searchengineland.com)"),
    gap_type: Optional[str] = Query(None, description="Filter by gap type (e.g. authority_publisher, direct_competitor)"),
    outreach_status: Optional[str] = Query(None, description="Filter by outreach status (e.g. identified, pitched)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: CitationRepository = Depends(get_citation_repository),
) -> List[CitationTargetRead]:
    """Retrieve citation target opportunities with multi-attribute filtering."""
    entities = repo.list_targets(
        domain=domain,
        gap_type=gap_type,
        outreach_status=outreach_status,
        skip=skip,
        limit=limit,
    )
    return [CitationTargetRead.model_validate(e) for e in entities]


@router.post(
    "/targets",
    response_model=CitationTargetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a citation target opportunity",
)
def create_citation_target(
    data: CitationTargetCreate,
    repo: CitationRepository = Depends(get_citation_repository),
) -> CitationTargetRead:
    """Store an identified citation acquisition target."""
    return repo.create_target(data)


@router.get(
    "/targets/{target_id}",
    response_model=CitationTargetRead,
    summary="Get single citation target by ID",
)
def get_citation_target(
    target_id: str,
    repo: CitationRepository = Depends(get_citation_repository),
) -> CitationTargetRead:
    """Fetch single citation target by ID."""
    target = repo.get_by_id(target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Citation target '{target_id}' not found.",
        )
    return CitationTargetRead.model_validate(target)
