"""Schemas for Pipeline Execution Tracking and Orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PipelineRunStatus


def now_utc_naive() -> datetime:
    """Return timezone-naive UTC timestamp."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PipelineStageStatus(str, Enum):
    """Lifecycle status for an individual pipeline execution stage."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


class CostBreakdownItem(BaseModel):
    """Cost breakdown for a specific provider operation."""
    provider: str
    operation: str
    call_count: int = 0
    estimated_cost_usd: float = 0.0
    is_estimated: bool = True
    details: Dict[str, Any] = Field(default_factory=dict)


class PipelineCostSummary(BaseModel):
    """Summary of financial costs incurred during a pipeline execution."""
    total_cost_usd: float = 0.0
    total_calls: int = 0
    by_provider: Dict[str, float] = Field(default_factory=dict)
    by_stage: Dict[str, float] = Field(default_factory=dict)
    items: List[CostBreakdownItem] = Field(default_factory=list)


class PipelineStageResult(BaseModel):
    """Result and telemetry of an individual pipeline stage."""
    stage_name: str
    status: PipelineStageStatus = PipelineStageStatus.PENDING
    duration_ms: float = 0.0
    items_processed: int = 0
    items_succeeded: int = 0
    items_failed: int = 0
    cost_usd: float = 0.0
    error_message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class PipelineRunBase(BaseModel):
    """Core tracking properties for a pipeline run."""
    pipeline_type: str = Field(
        ...,
        max_length=100,
        description="Type of pipeline executed (e.g., complete, refresh, audit).",
    )
    status: PipelineRunStatus = Field(
        default=PipelineRunStatus.PENDING,
        description="Current lifecycle status of the pipeline run.",
    )
    total_items: int = Field(
        default=0,
        ge=0,
        description="Total items scheduled for processing.",
    )
    processed_items: int = Field(
        default=0,
        ge=0,
        description="Total items processed so far.",
    )
    successful_items: int = Field(
        default=0,
        ge=0,
        description="Total items completed successfully.",
    )
    failed_items: int = Field(
        default=0,
        ge=0,
        description="Total items that failed processing.",
    )
    error_summary: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Summary of errors if any occurred.",
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution input parameters, stage breakdown, and cost telemetry.",
    )


class PipelineRunCreate(PipelineRunBase):
    """Payload to initiate a pipeline run."""
    pass


class PipelineRunRead(PipelineRunBase):
    """Serialized pipeline run status."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    started_at: datetime = Field(default_factory=now_utc_naive)
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=now_utc_naive)
    updated_at: datetime = Field(default_factory=now_utc_naive)


class PipelineExecutionRequest(BaseModel):
    """Request payload to trigger a pipeline run via CLI or REST API."""
    mode: str = Field(
        default="complete",
        description="Pipeline mode: 'complete' (all stages) or 'refresh' (re-measure & score only).",
    )
    market: Optional[str] = Field(
        default=None,
        description="Target search/AEO market (e.g. US, UK).",
    )
    provider: Optional[str] = Field(
        default=None,
        description="Filter to specific observation provider (e.g. google_search, perplexity).",
    )
    input_file: Optional[str] = Field(
        default=None,
        description="Path to CSV input file containing new creator questions for ingestion.",
    )
    sample_input: bool = Field(
        default=False,
        description="Whether to run pipeline against the live review sample input set.",
    )
    target_audit_url: str = Field(
        default="https://incubrix.com",
        description="Target public page URL for the technical SEO/AEO audit stage.",
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum bounded retries for transient provider/network errors.",
    )
    content_limit: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Maximum content drafts to generate in complete mode.",
    )
    use_llm: bool = Field(
        default=False,
        description="Whether to attempt configurable LLM generation for content drafts (fallback is deterministic).",
    )
    skip_audit: bool = Field(
        default=False,
        description="Whether to skip the technical audit stage.",
    )
    skip_content: bool = Field(
        default=False,
        description="Whether to skip the content and citation generation stage.",
    )
    auto_approve_inputs: bool = Field(
        default=True,
        description="Whether newly ingested questions should be marked as 'approved' for immediate measurement.",
    )


class PipelineExecutionResponse(BaseModel):
    """Comprehensive execution telemetry and outcome returned after pipeline completes."""
    run_id: str
    pipeline_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    stages: List[PipelineStageResult] = Field(default_factory=list)
    cost_summary: PipelineCostSummary = Field(default_factory=PipelineCostSummary)
    total_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    error_summary: Optional[str] = None
    report_paths: Dict[str, str] = Field(default_factory=dict)
