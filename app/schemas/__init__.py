"""Public schema interface for IncuBrix Visibility Engine."""

from app.schemas.audit import (
    AuditFindingBase,
    AuditFindingCreate,
    AuditFindingRead,
    AuditReport,
    FixValidationRequest,
    FixValidationResponse,
    PageAuditRequest,
)
from app.schemas.citation import (
    CitationTargetBase,
    CitationTargetCreate,
    CitationTargetRead,
    SeedCitationsResponse,
)
from app.schemas.common import (
    ArtifactType,
    AuditSeverity,
    AuditStatus,
    CitationGapType,
    CitationStatus,
    CollectionStatus,
    MentionStatus,
    ObservationType,
    PipelineRunStatus,
    ProviderType,
    ReviewStatus,
    ValidationStatus,
)
from app.schemas.content import (
    BatchGenerateRequest,
    BatchGenerateResponse,
    ContentBriefBase,
    ContentBriefCreate,
    ContentBriefRead,
    ContentValidationCheck,
    ContentValidationReport,
    GeneratedPageBase,
    GeneratedPageCreate,
    GeneratedPageRead,
    PageReviewUpdateRequest,
)
from app.schemas.evidence import (
    EvidenceArtifactBase,
    EvidenceArtifactCreate,
    EvidenceArtifactRead,
)
from app.schemas.observations import (
    GEOManualImportRequest,
    ManualEvidenceImportRequest,
    ObservationBase,
    ObservationCreate,
    ObservationRead,
)
from app.schemas.pipeline import (
    CostBreakdownItem,
    PipelineCostSummary,
    PipelineExecutionRequest,
    PipelineExecutionResponse,
    PipelineRunBase,
    PipelineRunCreate,
    PipelineRunRead,
    PipelineStageResult,
    PipelineStageStatus,
)
from app.schemas.questions import (
    IngestionRowError,
    QuestionBase,
    QuestionCreate,
    QuestionIngestionSummary,
    QuestionRead,
    QuestionReviewUpdate,
    QuestionUpdate,
)
from app.schemas.reports import (
    ProvenanceBreakdown,
    WeeklyReportResponse,
)
from app.schemas.scoring import (
    AnswerFeatureMetrics,
    ExcludedObservationsSummary,
    GEOMetrics,
    MetricPeriodDelta,
    SEOMetrics,
    VisibilityMetricsReport,
    VisibilityPeriodComparison,
)

__all__ = [
    # Common Enums
    "MentionStatus",
    "CitationStatus",
    "ObservationType",
    "ProviderType",
    "CollectionStatus",
    "ArtifactType",
    "AuditSeverity",
    "AuditStatus",
    "CitationGapType",
    "PipelineRunStatus",
    "ReviewStatus",
    "ValidationStatus",
    # Question
    "QuestionBase",
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionReviewUpdate",
    "QuestionRead",
    "IngestionRowError",
    "QuestionIngestionSummary",
    # Evidence
    "EvidenceArtifactBase",
    "EvidenceArtifactCreate",
    "EvidenceArtifactRead",
    # Observation
    "ObservationBase",
    "ObservationCreate",
    "ObservationRead",
    "ManualEvidenceImportRequest",
    "GEOManualImportRequest",
    # Audit
    "AuditFindingBase",
    "AuditFindingCreate",
    "AuditFindingRead",
    "PageAuditRequest",
    "AuditReport",
    "FixValidationRequest",
    "FixValidationResponse",
    # Content
    "ContentBriefBase",
    "ContentBriefCreate",
    "ContentBriefRead",
    "GeneratedPageBase",
    "GeneratedPageCreate",
    "GeneratedPageRead",
    "ContentValidationCheck",
    "ContentValidationReport",
    "BatchGenerateRequest",
    "BatchGenerateResponse",
    "PageReviewUpdateRequest",
    # Citation
    "CitationTargetBase",
    "CitationTargetCreate",
    "CitationTargetRead",
    "SeedCitationsResponse",
    # Pipeline
    "PipelineRunBase",
    "PipelineRunCreate",
    "PipelineRunRead",
    "PipelineStageStatus",
    "PipelineStageResult",
    "CostBreakdownItem",
    "PipelineCostSummary",
    "PipelineExecutionRequest",
    "PipelineExecutionResponse",
    # Scoring & Metrics
    "SEOMetrics",
    "GEOMetrics",
    "AnswerFeatureMetrics",
    "ExcludedObservationsSummary",
    "VisibilityMetricsReport",
    "MetricPeriodDelta",
    "VisibilityPeriodComparison",
    # Reports
    "ProvenanceBreakdown",
    "WeeklyReportResponse",
]
