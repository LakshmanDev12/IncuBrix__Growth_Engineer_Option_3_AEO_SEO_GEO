"""SQLAlchemy ORM Model for Creator Questions."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CommonMixin


class QuestionModel(Base, CommonMixin):
    """Database table storing creator questions."""

    __tablename__ = "questions"

    text: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    target_market: Mapped[str] = mapped_column(String(50), default="US", nullable=False)
    target_location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String(50), default="informational", nullable=True)
    persona: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Ingestion Provenance & Curation Status
    review_status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_platform: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    meta: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    observations = relationship(
        "ObservationModel",
        back_populates="question",
        cascade="all, delete-orphan",
    )
    content_briefs = relationship(
        "ContentBriefModel",
        back_populates="question",
        cascade="all, delete-orphan",
    )
    citation_targets = relationship(
        "CitationTargetModel",
        back_populates="question",
        cascade="all, delete-orphan",
    )
