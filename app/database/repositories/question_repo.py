"""Question repository for database queries and duplicate prevention."""

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database.base import utc_now
from app.database.models.question import QuestionModel
from app.database.repositories.base import BaseRepository
from app.exceptions import DuplicateEntityError
from app.schemas.common import ReviewStatus
from app.schemas.questions import QuestionCreate, QuestionUpdate


class QuestionRepository(BaseRepository[QuestionModel]):
    """Repository managing Creator Questions."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, QuestionModel)

    def get_by_text(self, text: str) -> Optional[QuestionModel]:
        """Look up a question by exact normalized text."""
        stmt = select(QuestionModel).where(QuestionModel.text == text.strip())
        return self.db.execute(stmt).scalar_one_or_none()

    def create_strict(self, data: QuestionCreate) -> QuestionModel:
        """Create a new question or raise DuplicateEntityError if text already exists."""
        clean_text = data.text.strip()
        existing = self.get_by_text(clean_text)
        if existing:
            raise DuplicateEntityError("Question", "text", clean_text)

        review_status = (
            data.review_status.value
            if hasattr(data.review_status, "value")
            else str(data.review_status)
        )
        entity = QuestionModel(
            text=clean_text,
            target_market=data.target_market,
            target_location=data.target_location,
            language=data.language,
            intent=data.intent,
            persona=data.persona,
            tags=data.tags,
            is_active=data.is_active,
            review_status=review_status,
            source_url=data.source_url,
            source_platform=data.source_platform,
            source_timestamp=data.source_timestamp,
            meta=data.meta,
        )
        return self.create(entity)

    def get_or_create(self, data: QuestionCreate) -> Tuple[QuestionModel, bool]:
        """Idempotent creation: returns (entity, created_boolean)."""
        clean_text = data.text.strip()
        existing = self.get_by_text(clean_text)
        if existing:
            return existing, False

        review_status = (
            data.review_status.value
            if hasattr(data.review_status, "value")
            else str(data.review_status)
        )
        entity = QuestionModel(
            text=clean_text,
            target_market=data.target_market,
            target_location=data.target_location,
            language=data.language,
            intent=data.intent,
            persona=data.persona,
            tags=data.tags,
            is_active=data.is_active,
            review_status=review_status,
            source_url=data.source_url,
            source_platform=data.source_platform,
            source_timestamp=data.source_timestamp,
            meta=data.meta,
        )
        return self.create(entity), True

    def update_question(self, question_id: str, data: QuestionUpdate) -> Optional[QuestionModel]:
        """Update existing question attributes."""
        question = self.get_by_id(question_id)
        if not question:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        if "text" in update_dict and update_dict["text"] is not None:
            clean_text = update_dict["text"].strip()
            existing = self.get_by_text(clean_text)
            if existing and existing.id != question_id:
                raise DuplicateEntityError("Question", "text", clean_text)
            update_dict["text"] = clean_text

        for key, val in update_dict.items():
            if key == "review_status" and hasattr(val, "value"):
                val = val.value
            setattr(question, key, val)

        return self.update(question)

    def update_review_status(
        self,
        question_id: str,
        review_status: ReviewStatus,
        notes: Optional[str] = None,
    ) -> Optional[QuestionModel]:
        """Update curation review status and append notes to metadata."""
        question = self.get_by_id(question_id)
        if not question:
            return None

        question.review_status = (
            review_status.value
            if hasattr(review_status, "value")
            else str(review_status)
        )
        if notes:
            meta = dict(question.meta or {})
            notes_history = list(meta.get("review_notes", []))
            notes_history.append({
                "status": question.review_status,
                "notes": notes,
                "timestamp": utc_now().isoformat(),
            })
            meta["review_notes"] = notes_history
            question.meta = meta
            flag_modified(question, "meta")

        return self.update(question)

    def filter_questions(
        self,
        market: Optional[str] = None,
        intent: Optional[str] = None,
        review_status: Optional[str] = None,
        platform: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[QuestionModel]:
        """Filter questions by market, intent, review status, platform, and active status."""
        stmt = select(QuestionModel)
        if market:
            stmt = stmt.where(QuestionModel.target_market == market)
        if intent:
            stmt = stmt.where(QuestionModel.intent == intent)
        if review_status:
            stmt = stmt.where(QuestionModel.review_status == review_status)
        if platform:
            stmt = stmt.where(QuestionModel.source_platform == platform)
        if is_active is not None:
            stmt = stmt.where(QuestionModel.is_active == is_active)
        stmt = stmt.order_by(QuestionModel.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
