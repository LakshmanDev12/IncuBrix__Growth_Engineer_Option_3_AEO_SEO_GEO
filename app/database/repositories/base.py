"""Generic Base Repository defining standard CRUD operations."""

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository implementation for SQLAlchemy models."""

    def __init__(self, db: Session, model: Type[ModelType]) -> None:
        self.db = db
        self.model = model

    def get_by_id(self, entity_id: str) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        stmt = select(self.model).where(self.model.id == entity_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by_desc: bool = True,
    ) -> List[ModelType]:
        """Return a paginated list of records."""
        stmt = select(self.model)
        if hasattr(self.model, "created_at") and order_by_desc:
            stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self) -> int:
        """Return total count of records in table."""
        stmt = select(func.count()).select_from(self.model)
        return self.db.execute(stmt).scalar() or 0

    def create(self, entity: ModelType) -> ModelType:
        """Persist a new entity to the database."""
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, entity: ModelType) -> ModelType:
        """Commit updates to an existing attached entity."""
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity_id: str) -> bool:
        """Delete an entity by primary key."""
        entity = self.get_by_id(entity_id)
        if not entity:
            return False
        self.db.delete(entity)
        self.db.commit()
        return True
