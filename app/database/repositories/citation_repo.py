"""Repository for Citation Targets and Opportunities."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.citation import CitationTargetModel
from app.database.repositories.base import BaseRepository
from app.schemas.citation import CitationTargetCreate


class CitationRepository(BaseRepository[CitationTargetModel]):
    """Repository managing Citation Targets."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, CitationTargetModel)

    def create_target(self, data: CitationTargetCreate) -> CitationTargetModel:
        """Create and store a citation opportunity."""
        gap_type_val = (
            data.gap_type.value
            if hasattr(data.gap_type, "value")
            else str(data.gap_type)
        )
        entity = CitationTargetModel(
            target_domain=data.target_domain.lower().strip(),
            target_url=data.target_url,
            question_id=data.question_id,
            observation_id=data.observation_id,
            competitor_domain=data.competitor_domain,
            anchor_context=data.anchor_context,
            gap_type=gap_type_val,
            authority_score=data.authority_score,
            outreach_status=data.outreach_status,
            relevance=data.relevance,
            pitch_angle=data.pitch_angle,
            notes=data.notes,
        )
        return self.create(entity)

    def batch_create_targets(
        self, targets: List[CitationTargetCreate]
    ) -> List[CitationTargetModel]:
        """Insert a batch of citation targets, skipping existing identical target_urls."""
        entities: List[CitationTargetModel] = []
        for data in targets:
            # Check duplicate by target_url if present
            if data.target_url:
                stmt = select(CitationTargetModel).where(
                    CitationTargetModel.target_url == data.target_url
                )
                existing = self.db.execute(stmt).scalar_one_or_none()
                if existing:
                    entities.append(existing)
                    continue

            gap_type_val = (
                data.gap_type.value
                if hasattr(data.gap_type, "value")
                else str(data.gap_type)
            )
            entity = CitationTargetModel(
                target_domain=data.target_domain.lower().strip(),
                target_url=data.target_url,
                question_id=data.question_id,
                observation_id=data.observation_id,
                competitor_domain=data.competitor_domain,
                anchor_context=data.anchor_context,
                gap_type=gap_type_val,
                authority_score=data.authority_score,
                outreach_status=data.outreach_status,
                relevance=data.relevance,
                pitch_angle=data.pitch_angle,
                notes=data.notes,
            )
            self.db.add(entity)
            entities.append(entity)

        self.db.commit()
        for e in entities:
            self.db.refresh(e)
        return entities

    def list_by_domain(self, domain: str) -> List[CitationTargetModel]:
        """List citation records referencing a given domain."""
        stmt = (
            select(CitationTargetModel)
            .where(CitationTargetModel.target_domain == domain.lower().strip())
            .order_by(CitationTargetModel.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_targets(
        self,
        domain: Optional[str] = None,
        gap_type: Optional[str] = None,
        outreach_status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CitationTargetModel]:
        """Filter citation target opportunities with pagination."""
        stmt = select(CitationTargetModel)
        if domain:
            stmt = stmt.where(CitationTargetModel.target_domain == domain.lower().strip())
        if gap_type:
            stmt = stmt.where(CitationTargetModel.gap_type == gap_type)
        if outreach_status:
            stmt = stmt.where(CitationTargetModel.outreach_status == outreach_status)

        stmt = stmt.order_by(CitationTargetModel.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
