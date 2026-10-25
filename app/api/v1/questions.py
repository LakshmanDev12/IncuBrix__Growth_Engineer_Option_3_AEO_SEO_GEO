"""API routes for Creator Questions, CSV Ingestion, and Curation Review."""

from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field

from app.api.dependencies import get_question_repository
from app.database.repositories.question_repo import QuestionRepository
from app.engine.question_ingestion import QuestionIngestionService
from app.exceptions import DuplicateEntityError
from app.schemas.questions import (
    QuestionCreate,
    QuestionIngestionSummary,
    QuestionRead,
    QuestionReviewUpdate,
    QuestionUpdate,
)

router = APIRouter(prefix="/questions", tags=["Creator Questions"])


class CSVTextImportPayload(BaseModel):
    """Payload to import questions from inline CSV text."""
    csv_content: str = Field(..., description="Raw CSV string including header row")
    default_market: str = Field("US", description="Default market if not in row")
    skip_duplicates: bool = Field(True, description="Whether to skip duplicate question text")
    auto_categorize_intent: bool = Field(True, description="Auto-classify intent if empty")


@router.post(
    "",
    response_model=QuestionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new creator question",
)
def create_question(
    data: QuestionCreate,
    repo: QuestionRepository = Depends(get_question_repository),
) -> QuestionRead:
    """Create a new creator question with duplicate check."""
    try:
        return repo.create_strict(data)
    except DuplicateEntityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        )


@router.post(
    "/import-csv",
    response_model=QuestionIngestionSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Import creator questions from a CSV file upload",
)
async def import_questions_from_file(
    file: UploadFile = File(..., description="CSV file with questions"),
    default_market: str = Query("US", description="Fallback market if missing in CSV"),
    skip_duplicates: bool = Query(True, description="Skip duplicate questions"),
    auto_categorize_intent: bool = Query(True, description="Infer intent if blank"),
    repo: QuestionRepository = Depends(get_question_repository),
) -> QuestionIngestionSummary:
    """Import creator questions in batch from a CSV file.

    Validates URL provenance, auto-categorizes intent, skips duplicates,
    and returns a row-by-row ingestion telemetry summary.
    """
    content = await file.read()
    service = QuestionIngestionService(repo)
    return service.import_from_csv(
        csv_content=content,
        default_market=default_market,
        skip_duplicates=skip_duplicates,
        auto_categorize_intent=auto_categorize_intent,
    )


@router.post(
    "/import-text",
    response_model=QuestionIngestionSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Import creator questions from inline CSV text",
)
def import_questions_from_text(
    payload: CSVTextImportPayload,
    repo: QuestionRepository = Depends(get_question_repository),
) -> QuestionIngestionSummary:
    """Batch ingest questions directly from raw CSV text."""
    service = QuestionIngestionService(repo)
    return service.import_from_csv(
        csv_content=payload.csv_content,
        default_market=payload.default_market,
        skip_duplicates=payload.skip_duplicates,
        auto_categorize_intent=payload.auto_categorize_intent,
    )


@router.get(
    "/export.csv",
    summary="Export creator questions to CSV file",
)
def export_questions_to_csv(
    market: Optional[str] = Query(None, description="Filter by market code"),
    intent: Optional[str] = Query(None, description="Filter by search intent"),
    review_status: Optional[str] = Query(None, description="Filter by curation review status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    repo: QuestionRepository = Depends(get_question_repository),
) -> Response:
    """Export stored creator questions to RFC 4180 compliant CSV."""
    questions = repo.filter_questions(
        market=market,
        intent=intent,
        review_status=review_status,
        is_active=is_active,
        skip=0,
        limit=10000,
    )
    service = QuestionIngestionService(repo)
    csv_data = service.export_to_csv(questions)
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="creator_questions.csv"'},
    )


@router.get(
    "",
    response_model=List[QuestionRead],
    summary="List questions with optional filtering",
)
def list_questions(
    market: Optional[str] = Query(None, description="Filter by market code (e.g. US)"),
    intent: Optional[str] = Query(None, description="Filter by search intent"),
    review_status: Optional[str] = Query(None, description="Filter by review status (pending, approved, rejected, flagged)"),
    platform: Optional[str] = Query(None, description="Filter by source platform"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: QuestionRepository = Depends(get_question_repository),
) -> List[QuestionRead]:
    """Retrieve creator questions with pagination and filters."""
    return repo.filter_questions(
        market=market,
        intent=intent,
        review_status=review_status,
        platform=platform,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{question_id}",
    response_model=QuestionRead,
    summary="Get question by ID",
)
def get_question(
    question_id: str,
    repo: QuestionRepository = Depends(get_question_repository),
) -> QuestionRead:
    """Fetch a single question by its UUID."""
    question = repo.get_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID '{question_id}' not found.",
        )
    return question


@router.patch(
    "/{question_id}",
    response_model=QuestionRead,
    summary="Update question attributes",
)
def update_question(
    question_id: str,
    data: QuestionUpdate,
    repo: QuestionRepository = Depends(get_question_repository),
) -> QuestionRead:
    """Update question attributes."""
    try:
        updated = repo.update_question(question_id, data)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with ID '{question_id}' not found.",
            )
        return updated
    except DuplicateEntityError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(err),
        )


@router.patch(
    "/{question_id}/review",
    response_model=QuestionRead,
    summary="Update question curation/review status",
)
def review_question(
    question_id: str,
    data: QuestionReviewUpdate,
    repo: QuestionRepository = Depends(get_question_repository),
) -> QuestionRead:
    """Curate question review status (approved, rejected, flagged) with audit notes."""
    updated = repo.update_review_status(
        question_id=question_id,
        review_status=data.review_status,
        notes=data.notes,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID '{question_id}' not found.",
        )
    return updated


@router.delete(
    "/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a question",
)
def delete_question(
    question_id: str,
    repo: QuestionRepository = Depends(get_question_repository),
) -> None:
    """Delete a question and cascading observations."""
    success = repo.delete(question_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID '{question_id}' not found.",
        )
