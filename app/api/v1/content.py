"""API routes for Content Briefs, Generated Pages, and Content Validation."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_content_repository,
    get_db,
    get_question_repository,
)
from app.content.brief_generator import ContentBriefGenerator
from app.content.generator import ContentCitationEngine
from app.content.validator import ContentValidator
from app.database.repositories.content_repo import ContentRepository
from app.database.repositories.question_repo import QuestionRepository
from app.exceptions import DuplicateEntityError
from app.schemas.content import (
    BatchGenerateRequest,
    BatchGenerateResponse,
    ContentBriefCreate,
    ContentBriefRead,
    ContentValidationReport,
    GeneratedPageCreate,
    GeneratedPageRead,
    PageReviewUpdateRequest,
)

router = APIRouter(prefix="/content", tags=["AEO Content Engine"])


@router.post(
    "/generate-batch",
    response_model=BatchGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Batch generate 10 publish-ready page drafts from approved questions",
)
def batch_generate_pages(
    request: BatchGenerateRequest = BatchGenerateRequest(),
    db: Session = Depends(get_db),
) -> BatchGenerateResponse:
    """Generate up to 10 publish-ready AEO/GEO page drafts from approved creator questions.

    Ensures direct answers in the first two sentences, useful headings, title and meta description,
    internal link suggestions, sourced citations, and Schema.org structured data.
    Drafts are strictly labeled as 'unreviewed' until human verification.
    """
    results = ContentCitationEngine.generate_all_ten_drafts(
        session=db,
        use_llm=request.use_llm,
        limit=request.limit,
    )

    page_reads = [GeneratedPageRead.model_validate(p) for _, p, _ in results]
    validation_reports = [r for _, _, r in results]

    return BatchGenerateResponse(
        total_generated=len(results),
        pages=page_reads,
        validation_reports=validation_reports,
    )


@router.post(
    "/validate/{page_id}",
    response_model=ContentValidationReport,
    summary="Validate an existing generated page draft against AEO standards",
)
def validate_page_draft(
    page_id: str,
    repo: ContentRepository = Depends(get_content_repository),
) -> ContentValidationReport:
    """Run full content quality, direct-answer, and structural compliance checks on a draft."""
    page = repo.get_page(page_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page with ID '{page_id}' not found.",
        )

    create_view = GeneratedPageCreate(
        brief_id=page.brief_id,
        title=page.title,
        slug=page.slug,
        meta_description=page.meta_description,
        markdown_content=page.markdown_content,
        schema_org_json=page.schema_org_json,
        publication_status=page.publication_status,
        internal_links=page.internal_links,
        citations=page.citations,
        word_count=page.word_count,
    )
    return ContentValidator.validate_page(create_view)


@router.patch(
    "/pages/{page_id}/review",
    response_model=GeneratedPageRead,
    summary="Review and curate page publication status",
)
def review_page_status(
    page_id: str,
    request: PageReviewUpdateRequest,
    repo: ContentRepository = Depends(get_content_repository),
) -> GeneratedPageRead:
    """Update publication status (e.g. from 'unreviewed' to 'approved' or 'published')."""
    valid_statuses = ("unreviewed", "reviewed", "approved", "published", "rejected")
    if request.publication_status.lower() not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid publication_status '{request.publication_status}'. Must be one of {valid_statuses}.",
        )

    updated = repo.update_page_status(
        page_id=page_id,
        publication_status=request.publication_status.lower(),
        notes=request.reviewer_notes,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page with ID '{page_id}' not found.",
        )
    return GeneratedPageRead.model_validate(updated)


@router.post(
    "/briefs",
    response_model=ContentBriefRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a content brief",
)
def create_brief(
    data: ContentBriefCreate,
    repo: ContentRepository = Depends(get_content_repository),
) -> ContentBriefRead:
    """Store an AEO content brief."""
    return repo.create_brief(data)


@router.get(
    "/briefs",
    response_model=List[ContentBriefRead],
    summary="List content briefs",
)
def list_briefs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: ContentRepository = Depends(get_content_repository),
) -> List[ContentBriefRead]:
    """Retrieve content briefs."""
    return repo.list_briefs(skip=skip, limit=limit)


@router.post(
    "/briefs/from-question/{question_id}",
    response_model=ContentBriefRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate an AEO brief from a creator question",
)
def generate_brief_from_question(
    question_id: str,
    q_repo: QuestionRepository = Depends(get_question_repository),
    content_repo: ContentRepository = Depends(get_content_repository),
) -> ContentBriefRead:
    """Generate and store an AEO brief targeted at a creator question."""
    question = q_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID '{question_id}' not found.",
        )

    brief_data = ContentBriefGenerator.generate_brief_from_question(question)
    return content_repo.create_brief(brief_data)


@router.post(
    "/pages",
    response_model=GeneratedPageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a generated content page",
)
def create_page(
    data: GeneratedPageCreate,
    repo: ContentRepository = Depends(get_content_repository),
) -> GeneratedPageRead:
    """Store a generated content page."""
    try:
        return repo.create_page(data)
    except DuplicateEntityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        )


@router.get(
    "/pages",
    response_model=List[GeneratedPageRead],
    summary="List generated content pages with optional status filter",
)
def list_pages(
    status_val: Optional[str] = Query(None, alias="status", description="Filter by publication status (e.g. unreviewed, approved)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: ContentRepository = Depends(get_content_repository),
) -> List[GeneratedPageRead]:
    """Retrieve generated pages."""
    entities = repo.list_pages(skip=skip, limit=limit, status=status_val)
    return [GeneratedPageRead.model_validate(e) for e in entities]


@router.get(
    "/pages/{slug}",
    response_model=GeneratedPageRead,
    summary="Get generated page by URL slug",
)
def get_page_by_slug(
    slug: str,
    repo: ContentRepository = Depends(get_content_repository),
) -> GeneratedPageRead:
    """Retrieve a page by its URL slug."""
    page = repo.get_page_by_slug(slug)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page with slug '{slug}' not found.",
        )
    return GeneratedPageRead.model_validate(page)
