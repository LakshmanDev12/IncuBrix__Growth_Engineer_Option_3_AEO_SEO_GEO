"""Evidence repository managing raw artifacts and hash deduplication."""

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.evidence import EvidenceArtifactModel
from app.database.repositories.base import BaseRepository
from app.exceptions import DuplicateEntityError
from app.schemas.evidence import EvidenceArtifactCreate


class EvidenceRepository(BaseRepository[EvidenceArtifactModel]):
    """Repository managing stored source evidence artifacts."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, EvidenceArtifactModel)

    def get_by_hash(self, content_hash: str) -> Optional[EvidenceArtifactModel]:
        """Look up evidence artifact by its SHA-256 content checksum."""
        stmt = select(EvidenceArtifactModel).where(
            EvidenceArtifactModel.content_hash == content_hash
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def store_evidence(
        self, data: EvidenceArtifactCreate, allow_existing: bool = True
    ) -> Tuple[EvidenceArtifactModel, bool]:
        """Persist evidence artifact with automatic SHA-256 hashing and deduplication."""
        content_hash = data.content_hash or data.compute_hash()

        existing = self.get_by_hash(content_hash)
        if existing:
            if not allow_existing:
                raise DuplicateEntityError("EvidenceArtifact", "content_hash", content_hash)
            return existing, False

        entity = EvidenceArtifactModel(
            artifact_type=data.artifact_type.value,
            question_id=data.question_id,
            content=data.content,
            storage_path=data.storage_path,
            content_hash=content_hash,
            source_url=data.source_url,
            collected_by=data.collected_by,
            meta=data.meta,
        )
        return self.create(entity), True

    def list_by_question(self, question_id: str) -> List[EvidenceArtifactModel]:
        """List all evidence artifacts linked to a specific question."""
        stmt = (
            select(EvidenceArtifactModel)
            .where(EvidenceArtifactModel.question_id == question_id)
            .order_by(EvidenceArtifactModel.captured_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
