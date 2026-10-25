"""SQLAlchemy ORM Model for Visibility Observations."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CommonMixin, utc_now


class ObservationModel(Base, CommonMixin):
    """Database table storing search engine and AI assistant visibility observations."""

    __tablename__ = "observations"

    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    market: Mapped[str] = mapped_column(String(50), default="US", nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    measured_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    observation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Content & Stored Artifact Reference
    raw_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    artifact_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("evidence_artifacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Visibility status: tri-state / unknown values (defaults to 'unknown')
    incubrix_mentioned: Mapped[str] = mapped_column(
        String(30), default="unknown", nullable=False, index=True
    )
    incubrix_cited: Mapped[str] = mapped_column(
        String(30), default="unknown", nullable=False, index=True
    )

    # Competitor & Evidence references
    competitors_observed: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    quoted_domains: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    quoted_urls: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    observed_features: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    evidence_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Search & AI specific attributes (nullable for explicit unavailable state)
    rank_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    answer_box_present: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    ai_model_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Collection status & errors
    collection_status: Mapped[str] = mapped_column(
        String(30), default="success", nullable=False, index=True
    )
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Scoring & Deduplication Fingerprint
    visibility_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fingerprint: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )

    # Relationships
    question = relationship("QuestionModel", back_populates="observations")
    artifact = relationship(
        "EvidenceArtifactModel",
        back_populates="observations",
        foreign_keys=[artifact_id],
    )
    citation_targets = relationship(
        "CitationTargetModel",
        back_populates="observation",
        cascade="all, delete-orphan",
    )
