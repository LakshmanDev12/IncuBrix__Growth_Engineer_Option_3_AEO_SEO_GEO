"""Question Ingestion, CSV Import/Export, and Intent Categorization Engine.

Provides:
- Semantic and keyword-based search intent classification.
- Robust CSV import with schema validation and row-level error reporting.
- Source URL validation and provenance preservation (platform, timestamp, metadata).
- Deduplication against existing repository records.
- Standardized CSV export supporting filtering and metadata.
"""

from __future__ import annotations

import csv
import io
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.database.models.question import QuestionModel
from app.database.repositories.question_repo import QuestionRepository
from app.logging_config import get_logger
from app.schemas.common import ReviewStatus
from app.schemas.questions import (
    IngestionRowError,
    QuestionCreate,
    QuestionIngestionSummary,
)

logger = get_logger("incubrix.question_ingestion")

# Regex heuristics for search & creator intent categorization
INTENT_PATTERNS = {
    "comparison": re.compile(r"\b(vs|versus|compare|comparison|difference between|or)\b", re.IGNORECASE),
    "commercial": re.compile(
        r"\b(best|top|tool|tools|software|platform|alternatives?|review|reviews|pricing|cost|cheapest|paid|free)\b",
        re.IGNORECASE,
    ),
    "transactional": re.compile(
        r"\b(download|buy|purchase|coupon|discount|sign up|subscribe|install|get access)\b",
        re.IGNORECASE,
    ),
    "navigational": re.compile(
        r"\b(login|sign in|website|official|dashboard|portal|app\.incubrix)\b",
        re.IGNORECASE,
    ),
    "informational": re.compile(
        r"\b(how|what|why|when|where|who|guide|tutorial|tips|workflow|can i|is it|learn|explain|steps)\b",
        re.IGNORECASE,
    ),
}


def classify_intent(text: str) -> str:
    """Classify user intent based on semantic structure and keywords.

    Order of evaluation:
    1. Comparison (e.g. 'Tool A vs Tool B')
    2. Transactional (e.g. 'download IncuBrix engine')
    3. Commercial (e.g. 'best AI b-roll tools')
    4. Navigational (e.g. 'login to dashboard')
    5. Informational (default for educational creator queries)
    """
    cleaned = text.strip()
    if INTENT_PATTERNS["comparison"].search(cleaned):
        return "comparison"
    if INTENT_PATTERNS["transactional"].search(cleaned):
        return "transactional"
    if INTENT_PATTERNS["commercial"].search(cleaned):
        return "commercial"
    if INTENT_PATTERNS["navigational"].search(cleaned):
        return "navigational"
    return "informational"


def parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    """Parse various source date/time representations safely."""
    if not value or not str(value).strip():
        return None

    cleaned = str(value).strip()
    # Try ISO formats
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

    # Try fromisoformat
    try:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        pass

    return None


def validate_url(url: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Validate source URL format.

    Returns:
    (clean_url, error_message)
    """
    if url is None:
        return None, None
    cleaned = str(url).strip()
    if not cleaned:
        return None, None

    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https"):
        return None, f"Invalid URL scheme '{parsed.scheme}'. Must be http or https."
    if not parsed.netloc:
        return None, "Invalid URL host/domain."
    return cleaned, None


class QuestionIngestionService:
    """Service handling batch CSV ingestion and structured CSV export."""

    def __init__(self, repo: QuestionRepository) -> None:
        self.repo = repo

    def import_from_csv(
        self,
        csv_content: str | bytes | io.StringIO,
        default_market: str = "US",
        skip_duplicates: bool = True,
        auto_categorize_intent: bool = True,
        default_review_status: ReviewStatus = ReviewStatus.PENDING,
    ) -> QuestionIngestionSummary:
        """Parse, validate, deduplicate, and persist creator questions from CSV."""
        if isinstance(csv_content, bytes):
            # Decode with utf-8-sig to handle Windows Excel BOM
            csv_text = csv_content.decode("utf-8-sig", errors="replace")
        elif isinstance(csv_content, io.StringIO):
            csv_text = csv_content.getvalue()
        else:
            csv_text = str(csv_content)

        reader = csv.DictReader(io.StringIO(csv_text))
        if not reader.fieldnames:
            return QuestionIngestionSummary(
                total_rows=0,
                imported_count=0,
                duplicates_count=0,
                invalid_count=1,
                errors=[
                    IngestionRowError(
                        row_number=1,
                        field="header",
                        reason="CSV header row is empty or malformed.",
                    )
                ],
            )

        # Normalize header keys to lowercase stripped
        normalized_headers = {h.strip().lower(): h for h in reader.fieldnames if h}

        # Field resolution helper
        def get_val(row: Dict[str, Any], *aliases: str) -> Optional[str]:
            for alias in aliases:
                orig_key = normalized_headers.get(alias.lower())
                if orig_key and row.get(orig_key) is not None:
                    v = str(row[orig_key]).strip()
                    if v:
                        return v
            return None

        total_rows = 0
        imported_ids: List[str] = []
        duplicates_count = 0
        invalid_count = 0
        errors: List[IngestionRowError] = []

        seen_in_batch: set = set()

        for idx, row in enumerate(reader, start=2):  # Row 1 is header
            total_rows += 1

            # 1. Question Text (Required, >= 5 chars)
            text_val = get_val(row, "text", "question", "query", "prompt")
            if not text_val or len(text_val) < 5:
                invalid_count += 1
                errors.append(
                    IngestionRowError(
                        row_number=idx,
                        field="text",
                        reason="Question text is missing or shorter than 5 characters.",
                        raw_value=text_val,
                    )
                )
                continue

            normalized_text = text_val.strip()

            # 2. Check in-batch deduplication
            if normalized_text.lower() in seen_in_batch:
                duplicates_count += 1
                continue
            seen_in_batch.add(normalized_text.lower())

            # 3. Check database deduplication
            existing = self.repo.get_by_text(normalized_text)
            if existing:
                duplicates_count += 1
                continue

            # 4. Source URL validation (nullable, but must be valid if supplied)
            raw_url = get_val(row, "source_url", "url", "link", "source")
            clean_url, url_err = validate_url(raw_url)
            if url_err:
                invalid_count += 1
                errors.append(
                    IngestionRowError(
                        row_number=idx,
                        field="source_url",
                        reason=url_err,
                        raw_value=raw_url,
                    )
                )
                continue

            # 5. Intent resolution
            raw_intent = get_val(row, "intent", "category")
            if raw_intent:
                intent = raw_intent.lower()
            elif auto_categorize_intent:
                intent = classify_intent(normalized_text)
            else:
                intent = "informational"

            # 6. Parse other metadata
            market = get_val(row, "target_market", "market", "country") or default_market
            location = get_val(row, "target_location", "location", "geo", "city")
            language = get_val(row, "language", "lang") or "en"
            persona = get_val(row, "persona", "audience", "target_audience")

            # Tags (semicolon or comma separated)
            raw_tags = get_val(row, "tags", "categories", "keywords")
            tags = []
            if raw_tags:
                delimiter = ";" if ";" in raw_tags else ","
                tags = [t.strip() for t in raw_tags.split(delimiter) if t.strip()]

            # Review status
            raw_status = get_val(row, "review_status", "status")
            review_status = default_review_status
            if raw_status:
                try:
                    review_status = ReviewStatus(raw_status.lower())
                except ValueError:
                    review_status = default_review_status

            # Source provenance
            source_platform = get_val(row, "source_platform", "platform", "channel")
            raw_timestamp = get_val(row, "source_timestamp", "timestamp", "date", "created_date")
            source_timestamp = parse_timestamp(raw_timestamp)

            # Metadata extraction for extra columns
            extra_meta: Dict[str, Any] = {}
            for k, orig_col in normalized_headers.items():
                if k not in (
                    "text", "question", "query", "prompt",
                    "target_market", "market", "country",
                    "target_location", "location", "geo", "city",
                    "language", "lang",
                    "intent", "category",
                    "persona", "audience",
                    "tags", "categories", "keywords",
                    "source_url", "url", "link", "source",
                    "source_platform", "platform", "channel",
                    "source_timestamp", "timestamp", "date",
                    "review_status", "status",
                    "is_active",
                ):
                    val = row.get(orig_col)
                    if val is not None and str(val).strip():
                        extra_meta[k] = str(val).strip()

            # Active flag
            raw_active = get_val(row, "is_active", "active")
            is_active = True
            if raw_active is not None and raw_active.lower() in ("false", "0", "no"):
                is_active = False

            # Create question
            q_create = QuestionCreate(
                text=normalized_text,
                target_market=market,
                target_location=location,
                language=language,
                intent=intent,
                persona=persona,
                tags=tags,
                is_active=is_active,
                review_status=review_status,
                source_url=clean_url,
                source_platform=source_platform,
                source_timestamp=source_timestamp,
                meta=extra_meta,
            )

            created = self.repo.create_strict(q_create)
            imported_ids.append(created.id)

        return QuestionIngestionSummary(
            total_rows=total_rows,
            imported_count=len(imported_ids),
            duplicates_count=duplicates_count,
            invalid_count=invalid_count,
            imported_ids=imported_ids,
            errors=errors,
        )

    def export_to_csv(self, questions: List[QuestionModel]) -> str:
        """Export a list of questions to standardized CSV format."""
        output = io.StringIO()
        fieldnames = [
            "id",
            "text",
            "target_market",
            "target_location",
            "language",
            "intent",
            "persona",
            "tags",
            "review_status",
            "source_url",
            "source_platform",
            "source_timestamp",
            "is_active",
            "created_at",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()

        for q in questions:
            writer.writerow(
                {
                    "id": q.id,
                    "text": q.text,
                    "target_market": q.target_market,
                    "target_location": q.target_location or "",
                    "language": q.language,
                    "intent": q.intent or "",
                    "persona": q.persona or "",
                    "tags": ";".join(q.tags) if q.tags else "",
                    "review_status": q.review_status,
                    "source_url": q.source_url or "",
                    "source_platform": q.source_platform or "",
                    "source_timestamp": q.source_timestamp.isoformat() if q.source_timestamp else "",
                    "is_active": str(q.is_active).lower(),
                    "created_at": q.created_at.isoformat() if q.created_at else "",
                }
            )

        return output.getvalue()


# Alias for backward and architectural compatibility
QuestionIngestionEngine = QuestionIngestionService

