"""SQLAlchemy ORM Model for Technical SEO/AEO Audit Findings."""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CommonMixin, utc_now


class AuditFindingModel(Base, CommonMixin):
    """Database table storing automated or manual technical audit findings."""

    __tablename__ = "audit_findings"

    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    audit_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    issue_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    patch: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    validation_status: Mapped[str] = mapped_column(
        String(50), default="unvalidated", nullable=False, index=True
    )
    raw_metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False, index=True
    )
