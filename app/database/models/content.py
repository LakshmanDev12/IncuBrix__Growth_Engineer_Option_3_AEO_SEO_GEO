"""SQLAlchemy ORM Models for Content Briefs and Generated Pages."""

from typing import Any, Dict, List, Optional

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, CommonMixin


class ContentBriefModel(Base, CommonMixin):
    """Database table storing AEO content generation briefs."""

    __tablename__ = "content_briefs"

    question_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_topic: Mapped[str] = mapped_column(String(200), nullable=False)
    target_query: Mapped[str] = mapped_column(Text, nullable=False)
    primary_intent: Mapped[str] = mapped_column(String(50), default="informational", nullable=False)
    target_entities: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    required_sections: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    recommended_faqs: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    target_word_count: Mapped[int] = mapped_column(Integer, default=1200, nullable=False)
    tone: Mapped[str] = mapped_column(String(100), default="authoritative and actionable", nullable=False)
    schema_type: Mapped[str] = mapped_column(String(50), default="TechArticle", nullable=False)

    # Relationships
    question = relationship("QuestionModel", back_populates="content_briefs")
    pages = relationship(
        "GeneratedPageModel",
        back_populates="brief",
        cascade="all, delete-orphan",
    )


class GeneratedPageModel(Base, CommonMixin):
    """Database table storing generated and optimized pages."""

    __tablename__ = "generated_pages"

    brief_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content_briefs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    meta_description: Mapped[str] = mapped_column(Text, nullable=False)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    schema_org_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    publication_status: Mapped[str] = mapped_column(String(50), default="unreviewed", nullable=False, index=True)
    internal_links: Mapped[List[Dict[str, str]]] = mapped_column(JSON, default=list, nullable=False)
    citations: Mapped[List[Dict[str, str]]] = mapped_column(JSON, default=list, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    brief = relationship("ContentBriefModel", back_populates="pages")
