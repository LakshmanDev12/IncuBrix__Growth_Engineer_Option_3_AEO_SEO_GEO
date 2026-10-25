"""Schemas for Source Evidence artifacts."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.schemas.common import ArtifactType


class EvidenceArtifactBase(BaseModel):
    """Shared fields for source evidence artifacts."""
    artifact_type: ArtifactType = Field(
        default=ArtifactType.RAW_TEXT,
        description="Format of the stored evidence artifact.",
    )
    question_id: Optional[str] = Field(
        default=None,
        description="Associated creator question ID, if tied directly to a specific query.",
    )
    source_url: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Original public URL where the result was observed or captured.",
    )
    collected_by: str = Field(
        default="manual_operator",
        max_length=100,
        description="Agent or operator responsible for collecting this evidence artifact.",
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("meta", "metadata"),
        serialization_alias="metadata",
        description="Structured contextual metadata (headers, engine flags, tokens).",
    )

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class EvidenceArtifactCreate(EvidenceArtifactBase):
    """Payload to create and store evidence."""
    content: Optional[str] = Field(
        default=None,
        description="Raw text or JSON dump content. If provided, content_hash is automatically generated.",
    )
    storage_path: Optional[str] = Field(
        default=None,
        description="Optional relative filesystem path if the artifact is stored externally on disk.",
    )
    content_hash: Optional[str] = Field(
        default=None,
        description="Optional precomputed SHA-256 checksum. Computed automatically if content is supplied.",
    )

    def compute_hash(self) -> str:
        """Compute SHA-256 checksum of payload content for deduplication."""
        payload = (self.content or self.storage_path or "").encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


class EvidenceArtifactRead(EvidenceArtifactBase):
    """Serialized stored evidence artifact."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: Optional[str] = None
    storage_path: Optional[str] = None
    content_hash: str
    captured_at: datetime = Field(default_factory=datetime.utcnow)
