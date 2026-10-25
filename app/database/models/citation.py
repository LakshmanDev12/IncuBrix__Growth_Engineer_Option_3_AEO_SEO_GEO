"""SQLAlchemy ORM Model for Citation Targets and Opportunities."""

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CommonMixin


class CitationTargetModel(Base, CommonMixin):
    """Database table storing external domains/URLs identified for citation acquisition."""

    __tablename__ = "citation_targets"

    target_domain: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    target_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    question_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    observation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("observations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    competitor_domain: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    anchor_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gap_type: Mapped[str] = mapped_column(String(50), default="unknown", nullable=False)
    authority_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    outreach_status: Mapped[str] = mapped_column(String(50), default="identified", nullable=False)
    relevance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pitch_angle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    question = relationship("QuestionModel", back_populates="citation_targets")
    observation = relationship("ObservationModel", back_populates="citation_targets")
