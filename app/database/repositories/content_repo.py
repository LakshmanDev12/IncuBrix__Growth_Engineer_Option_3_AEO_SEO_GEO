"""Repository for Content Briefs and Generated Pages."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.content import ContentBriefModel, GeneratedPageModel
from app.database.repositories.base import BaseRepository
from app.exceptions import DuplicateEntityError
from app.schemas.content import ContentBriefCreate, GeneratedPageCreate


class ContentRepository:
    """Repository managing Content Briefs and Generated Pages."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.brief_repo = BaseRepository[ContentBriefModel](db, ContentBriefModel)
        self.page_repo = BaseRepository[GeneratedPageModel](db, GeneratedPageModel)

    # Content Briefs
    def create_brief(self, data: ContentBriefCreate) -> ContentBriefModel:
        """Create and store a new content brief."""
        entity = ContentBriefModel(
            question_id=data.question_id,
            target_topic=data.target_topic,
            target_query=data.target_query,
            primary_intent=data.primary_intent,
            target_entities=data.target_entities,
            required_sections=data.required_sections,
            recommended_faqs=data.recommended_faqs,
            target_word_count=data.target_word_count,
            tone=data.tone,
            schema_type=data.schema_type,
        )
        return self.brief_repo.create(entity)

    def get_brief(self, brief_id: str) -> Optional[ContentBriefModel]:
        """Fetch content brief by ID."""
        return self.brief_repo.get_by_id(brief_id)

    def list_briefs(self, skip: int = 0, limit: int = 100) -> List[ContentBriefModel]:
        """List content briefs."""
        return self.brief_repo.list(skip=skip, limit=limit)

    # Generated Pages
    def create_page(self, data: GeneratedPageCreate) -> GeneratedPageModel:
        """Create and store a generated page, preventing duplicate slugs."""
        stmt = select(GeneratedPageModel).where(GeneratedPageModel.slug == data.slug)
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing:
            raise DuplicateEntityError("GeneratedPage", "slug", data.slug)

        entity = GeneratedPageModel(
            brief_id=data.brief_id,
            title=data.title,
            slug=data.slug,
            meta_description=data.meta_description,
            markdown_content=data.markdown_content,
            schema_org_json=data.schema_org_json,
            publication_status=data.publication_status,
            internal_links=data.internal_links,
            citations=data.citations,
            word_count=data.word_count,
        )
        return self.page_repo.create(entity)

    def get_page_by_slug(self, slug: str) -> Optional[GeneratedPageModel]:
        """Fetch generated page by unique URL slug."""
        stmt = select(GeneratedPageModel).where(GeneratedPageModel.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_page(self, page_id: str) -> Optional[GeneratedPageModel]:
        """Fetch generated page by ID."""
        return self.page_repo.get_by_id(page_id)

    def update_page_status(
        self,
        page_id: str,
        publication_status: str,
        notes: Optional[str] = None,
    ) -> Optional[GeneratedPageModel]:
        """Update publication review status for a generated page."""
        page = self.get_page(page_id)
        if not page:
            return None
        page.publication_status = publication_status
        if notes:
            schema = dict(page.schema_org_json) if page.schema_org_json else {}
            schema["review_notes"] = notes
            page.schema_org_json = schema
        self.db.commit()
        self.db.refresh(page)
        return page

    def list_pages(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[GeneratedPageModel]:
        """List generated pages with optional status filtering."""
        stmt = select(GeneratedPageModel)
        if status:
            stmt = stmt.where(GeneratedPageModel.publication_status == status)
        stmt = stmt.order_by(GeneratedPageModel.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
