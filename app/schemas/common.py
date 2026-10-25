"""Shared enums and value types for IncuBrix Visibility Engine schemas.

Explicit unknown and unavailable states are mandatory across all observation
and evidence evaluations so that missing evidence is never treated as a negative result.
"""

from enum import Enum


class MentionStatus(str, Enum):
    """Explicit mention status of IncuBrix in observed outputs."""
    MENTIONED = "mentioned"
    NOT_MENTIONED = "not_mentioned"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"


class CitationStatus(str, Enum):
    """Explicit citation/link status of IncuBrix in observed outputs."""
    CITED = "cited"
    NOT_CITED = "not_cited"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"


class ObservationType(str, Enum):
    """Channel/medium where the visibility observation was recorded."""
    SEARCH_ENGINE = "search_engine"
    AI_ASSISTANT = "ai_assistant"
    HYBRID_OVERVIEW = "hybrid_overview"
    UNKNOWN = "unknown"


class ProviderType(str, Enum):
    """Source platform/model of the observation."""
    GOOGLE_SEARCH = "google_search"
    GOOGLE_AI_OVERVIEW = "google_ai_overview"
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    PERPLEXITY = "perplexity"
    GEMINI = "gemini"
    BING_COPILOT = "bing_copilot"
    OTHER = "other"


class CollectionStatus(str, Enum):
    """Status of the automated or manual collection process."""
    PENDING = "pending"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class ArtifactType(str, Enum):
    """Format and nature of stored source evidence."""
    RAW_TEXT = "raw_text"
    JSON_PAYLOAD = "json_payload"
    HTML_SNAPSHOT = "html_snapshot"
    SCREENSHOT = "screenshot"
    URL_REFERENCE = "url_reference"


class AuditSeverity(str, Enum):
    """Severity level of technical SEO/AEO audit findings."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(str, Enum):
    """Outcome status of an audit test."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    UNKNOWN = "unknown"


class ValidationStatus(str, Enum):
    """Validation state of an audit finding remediation or patch."""
    UNVALIDATED = "unvalidated"
    VALIDATED = "validated"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class CitationGapType(str, Enum):
    """Nature of an identified citation target opportunity."""
    DIRECT_COMPETITOR = "direct_competitor"
    AUTHORITY_PUBLISHER = "authority_publisher"
    DIRECTORY_LISTING = "directory_listing"
    COMMUNITY_FORUM = "community_forum"
    UNKNOWN = "unknown"


class ReviewStatus(str, Enum):
    """Workflow curation status for creator questions."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class PipelineRunStatus(str, Enum):
    """Lifecycle status of a pipeline run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
