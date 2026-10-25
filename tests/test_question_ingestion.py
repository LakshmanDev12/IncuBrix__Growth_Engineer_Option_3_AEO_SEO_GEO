"""Unit and integration tests for Module 2: Question Ingestion.

Tests verify:
- Intent categorization heuristics.
- URL validation and source provenance preservation.
- Duplicate question handling (in-batch and DB deduplication).
- Invalid row detection and granular error reporting.
- Missing URL resilience (nullable states).
- CSV export formatting and filtering.
- Manual curation/review status workflow.
- API endpoints (multipart CSV upload and inline text import).
"""

import io
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.repositories.question_repo import QuestionRepository
from app.engine.question_ingestion import (
    QuestionIngestionService,
    classify_intent,
    validate_url,
)
from app.schemas.common import ReviewStatus
from app.schemas.questions import QuestionCreate


def test_intent_categorization():
    """Verify semantic and keyword-based search intent classification."""
    assert classify_intent("IncuBrix vs Runway for video b-roll") == "comparison"
    assert classify_intent("Best automated video b-roll software tools") == "commercial"
    assert classify_intent("Download IncuBrix b-roll generator trial") == "transactional"
    assert classify_intent("IncuBrix official login dashboard") == "navigational"
    assert classify_intent("How do creators sync voiceover to stock video?") == "informational"
    assert classify_intent("Why does video pacing matter in short form content?") == "informational"


def test_source_url_validation():
    """Verify URL validation handles valid URLs, invalid schemes, and missing URLs."""
    # Valid HTTP/HTTPS URLs
    clean, err = validate_url("https://reddit.com/r/creators/comments/123")
    assert clean == "https://reddit.com/r/creators/comments/123"
    assert err is None

    clean, err = validate_url("http://example.com/thread")
    assert clean == "http://example.com/thread"
    assert err is None

    # Missing / None / Empty URLs are permitted (nullable)
    clean, err = validate_url(None)
    assert clean is None and err is None

    clean, err = validate_url("   ")
    assert clean is None and err is None

    # Invalid URL schemes / malformed formats
    clean, err = validate_url("ftp://files.example.com/list")
    assert clean is None and "scheme" in err.lower()

    clean, err = validate_url("not-a-valid-url")
    assert clean is None and err is not None


def test_csv_import_valid_rows_and_provenance(db_session: Session):
    """Verify CSV import preserves real source URLs, platforms, timestamps, and tags."""
    csv_data = """text,target_market,target_location,source_url,source_platform,source_timestamp,tags
"How do solo creators produce 10 shorts a week?","US","Austin, TX","https://youtube.com/watch?v=abc12345","YouTube","2026-10-18T14:30:00Z","shorts;production;ai"
"Best automated b-roll tool for podcasters","UK","London","https://reddit.com/r/podcasts/comments/987","Reddit","2026-10-19","podcasts,b-roll,audio"
"""
    repo = QuestionRepository(db_session)
    service = QuestionIngestionService(repo)

    summary = service.import_from_csv(csv_data)

    assert summary.total_rows == 2
    assert summary.imported_count == 2
    assert summary.duplicates_count == 0
    assert summary.invalid_count == 0
    assert len(summary.imported_ids) == 2

    # Check database persistence and provenance
    q1 = repo.get_by_text("How do solo creators produce 10 shorts a week?")
    assert q1 is not None
    assert q1.target_market == "US"
    assert q1.target_location == "Austin, TX"
    assert q1.source_url == "https://youtube.com/watch?v=abc12345"
    assert q1.source_platform == "YouTube"
    assert q1.source_timestamp == datetime(2026, 10, 18, 14, 30, 0)
    assert "shorts" in q1.tags
    assert q1.intent == "informational"  # Auto-inferred
    assert q1.review_status == ReviewStatus.PENDING.value

    q2 = repo.get_by_text("Best automated b-roll tool for podcasters")
    assert q2 is not None
    assert q2.target_market == "UK"
    assert q2.source_platform == "Reddit"
    assert q2.intent == "commercial"  # Auto-inferred from 'Best ... tool'


def test_csv_import_duplicate_questions(db_session: Session):
    """Verify deduplication skips duplicate questions in-batch and against the database."""
    repo = QuestionRepository(db_session)

    # Pre-populate database with an existing question
    repo.create_strict(
        QuestionCreate(
            text="Existing database question that should be skipped?",
            target_market="US",
        )
    )

    csv_data = """text,market
"Existing database question that should be skipped?","US"
"Brand new unique question for ingestion?","US"
"Brand new unique question for ingestion?","US"
"""
    service = QuestionIngestionService(repo)
    summary = service.import_from_csv(csv_data)

    assert summary.total_rows == 3
    assert summary.imported_count == 1
    assert summary.duplicates_count == 2
    assert summary.invalid_count == 0

    assert repo.count() == 2


def test_csv_import_invalid_rows_and_error_reporting(db_session: Session):
    """Verify invalid rows are reported with row index, field name, and specific error reason."""
    csv_data = """text,source_url
"Why?","https://valid.com"
"","https://valid.com"
"Valid question with invalid URL scheme here?","ftp://invalid-scheme.com/file"
"Valid question with malformed url text?","just-plain-bad-url"
"Valid question that succeeds despite other invalid rows?","https://incubrix.com/blog"
"""
    repo = QuestionRepository(db_session)
    service = QuestionIngestionService(repo)

    summary = service.import_from_csv(csv_data)

    assert summary.total_rows == 5
    assert summary.imported_count == 1
    assert summary.invalid_count == 4
    assert len(summary.errors) == 4

    error_fields = [e.field for e in summary.errors]
    assert error_fields.count("text") == 2
    assert error_fields.count("source_url") == 2

    # Verify the 1 valid row was persisted
    valid_q = repo.get_by_text("Valid question that succeeds despite other invalid rows?")
    assert valid_q is not None


def test_csv_import_missing_urls_handling(db_session: Session):
    """Verify rows with missing or blank URLs are cleanly ingested with source_url=None."""
    csv_data = """text,source_url,source_platform
"Question with completely omitted URL column data?","","Manual"
"Another question without source URL specified?",,"Community"
"""
    repo = QuestionRepository(db_session)
    service = QuestionIngestionService(repo)

    summary = service.import_from_csv(csv_data)

    assert summary.total_rows == 2
    assert summary.imported_count == 2
    assert summary.invalid_count == 0

    q1 = repo.get_by_text("Question with completely omitted URL column data?")
    assert q1 is not None
    assert q1.source_url is None
    assert q1.source_platform == "Manual"


def test_csv_export_formatting_and_filtering(db_session: Session):
    """Verify RFC 4180 CSV export with headers, formatted tags, timestamps, and filters."""
    repo = QuestionRepository(db_session)
    repo.create_strict(
        QuestionCreate(
            text="How to edit b-roll for corporate videos?",
            target_market="US",
            intent="informational",
            review_status=ReviewStatus.APPROVED,
            source_url="https://youtube.com/watch?v=111",
            source_platform="YouTube",
            source_timestamp=datetime(2026, 10, 20, 12, 0, 0),
            tags=["corporate", "editing"],
        )
    )
    repo.create_strict(
        QuestionCreate(
            text="Best b-roll libraries for travel vloggers?",
            target_market="UK",
            intent="commercial",
            review_status=ReviewStatus.PENDING,
            tags=["travel", "vlogging"],
        )
    )

    service = QuestionIngestionService(repo)

    # Export all
    all_questions = repo.list()
    csv_out = service.export_to_csv(all_questions)

    assert "id,text,target_market,target_location,language,intent,persona,tags,review_status,source_url,source_platform,source_timestamp,is_active,created_at" in csv_out
    assert "How to edit b-roll for corporate videos?" in csv_out
    assert "Best b-roll libraries for travel vloggers?" in csv_out
    assert "corporate;editing" in csv_out
    assert "https://youtube.com/watch?v=111" in csv_out

    # Filter export by market
    uk_questions = repo.filter_questions(market="UK")
    uk_csv = service.export_to_csv(uk_questions)
    assert "Best b-roll libraries for travel vloggers?" in uk_csv
    assert "How to edit b-roll for corporate videos?" not in uk_csv


def test_manual_review_status_workflow(db_session: Session):
    """Verify manual review status curation and reviewer notes audit trail."""
    repo = QuestionRepository(db_session)
    q = repo.create_strict(
        QuestionCreate(
            text="How can creators turn scripts into engaging YouTube videos?",
            review_status=ReviewStatus.PENDING,
        )
    )
    assert q.review_status == ReviewStatus.PENDING.value

    # Approve question with curator note
    approved = repo.update_review_status(
        question_id=q.id,
        review_status=ReviewStatus.APPROVED,
        notes="High search demand verified on Google Trends.",
    )
    assert approved is not None
    assert approved.review_status == ReviewStatus.APPROVED.value
    assert "review_notes" in approved.meta
    assert approved.meta["review_notes"][0]["notes"] == "High search demand verified on Google Trends."

    # Reject question
    rejected = repo.update_review_status(
        question_id=q.id,
        review_status=ReviewStatus.REJECTED,
        notes="Out of scope for video b-roll engine.",
    )
    assert rejected.review_status == ReviewStatus.REJECTED.value
    assert len(rejected.meta["review_notes"]) == 2


def test_api_import_and_export_endpoints(client: TestClient):
    """Verify API endpoints for CSV file upload, inline text import, review update, and CSV export."""
    # 1. Inline text import
    csv_text = """text,target_market,source_url,source_platform
"How do creators cut b-roll footage in minutes?","US","https://reddit.com/r/video","Reddit"
"Best tools to sync audio and video automatically?","US","https://youtube.com/watch?v=999","YouTube"
"""
    resp = client.post("/v1/questions/import-text", json={"csv_content": csv_text})
    assert resp.status_code == 201
    summary = resp.json()
    assert summary["imported_count"] == 2
    q_id = summary["imported_ids"][0]

    # 2. File upload import via multipart
    file_csv = b"""text,target_market\n"Can AI automate stock b-roll selection?","US"\n"""
    file_resp = client.post(
        "/v1/questions/import-csv",
        files={"file": ("questions.csv", io.BytesIO(file_csv), "text/csv")},
    )
    assert file_resp.status_code == 201
    assert file_resp.json()["imported_count"] == 1

    # 3. Review status curation endpoint
    rev_resp = client.patch(
        f"/v1/questions/{q_id}/review",
        json={"review_status": "approved", "notes": "Approved for pipeline execution."},
    )
    assert rev_resp.status_code == 200
    assert rev_resp.json()["review_status"] == "approved"

    # 4. CSV export endpoint
    export_resp = client.get("/v1/questions/export.csv")
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"].startswith("text/csv")
    assert "How do creators cut b-roll footage in minutes?" in export_resp.text
    assert "Can AI automate stock b-roll selection?" in export_resp.text
