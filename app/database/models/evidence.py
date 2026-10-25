"""SQLAlchemy ORM Model for Source Evidence Artifacts."""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CommonMixin, utc_now


class EvidenceArtifactModel(Base, CommonMixin):
    """Database table storing raw evidence artifacts, responses, and screenshots."""

    __tablename__ = "evidence_artifacts"

    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    question_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    collected_by: Mapped[str] = mapped_column(String(100), default="manual_operator", nullable=False)
    meta: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    # Relationships
    observations = relationship(
        "ObservationModel",
        back_populates="artifact",
        foreign_keys="[ObservationModel.artifact_id]",
    )
