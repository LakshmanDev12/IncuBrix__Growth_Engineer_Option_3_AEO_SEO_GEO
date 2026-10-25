"""Comprehensive tests for Module 7 — Content and Citation Engine.

Verifies:
- 10 publish-ready page drafts from approved creator questions.
- Direct answers in the first two sentences without fluff.
- Useful headings outline, title, meta description, internal links, and citations.
- Appropriate Schema.org JSON-LD structured data.
- Grounding in verified product information without hallucinations.
- 30 specific real third-party citation opportunities stored with relevance and pitch angles.
- Configurable LLM provider with robust deterministic fallback.
- Content validation and reporting.
- Draft labeling as 'unreviewed' until human curation.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.content.generator import ContentCitationEngine
from app.content.validator import ContentValidator
from app.content.verified_knowledge import (
    APPROVED_CREATOR_QUESTIONS,
    INCUBRIX_PRODUCT_INFO,
    THIRTY_REAL_CITATION_TARGETS,
)
from app.database.repositories.citation_repo import CitationRepository
from app.database.repositories.content_repo import ContentRepository
from app.schemas.content import (
    BatchGenerateRequest,
    GeneratedPageCreate,
    PageReviewUpdateRequest,
)


def test_ten_publish_ready_pages_generation(db_session: Session):
    """Requirement 1: Generate ten publish-ready page drafts from approved questions."""
    assert len(APPROVED_CREATOR_QUESTIONS) == 10

    results = ContentCitationEngine.generate_all_ten_drafts(session=db_session, use_llm=False, limit=10)
    assert len(results) == 10

    content_repo = ContentRepository(db_session)
    stored_pages = content_repo.list_pages(limit=20)
    assert len(stored_pages) == 10

    for brief, page, report in results:
        assert brief.id is not None
        assert page.id is not None
        assert page.brief_id == brief.id
        assert page.word_count >= 200
        assert report.is_publish_ready is True
        assert page.publication_status == "unreviewed"


def test_direct_answers_in_first_two_sentences(db_session: Session):
    """Requirement 2: Include direct answers in the first two sentences."""
    results = ContentCitationEngine.generate_all_ten_drafts(session=db_session, use_llm=False, limit=10)

    for _, page, _ in results:
        # Check first non-heading block
        paragraphs = [p.strip() for p in page.markdown_content.split("\n\n") if p.strip() and not p.strip().startswith("#")]
        assert len(paragraphs) > 0

        first_block = paragraphs[0]
        assert first_block.startswith("> **Quick Answer**:")

        # The answer must not contain fluff openings
        lower_block = first_block.lower()
        assert "in this blog post" not in lower_block
        assert "have you ever wondered" not in lower_block
        assert "today we will" not in lower_block

        # Check validator acknowledges direct answer
        val = ContentValidator._check_direct_answer(page.markdown_content, page.title)
        assert val.passed is True


def test_useful_headings_and_structure(db_session: Session):
    """Requirement 2: Ensure useful headings (H1, multiple H2s) and structured body sections."""
    results = ContentCitationEngine.generate_all_ten_drafts(session=db_session, use_llm=False, limit=10)

    for _, page, report in results:
        md = page.markdown_content
        # Exactly 1 H1
        h1_count = md.count("\n# ") + (1 if md.startswith("# ") else 0)
        assert h1_count == 1

        # At least 4 H2 headings for thorough topic coverage
        h2_count = md.count("\n## ")
        assert h2_count >= 4

        # Heading hierarchy check must pass in validation report
        h_check = next(c for c in report.checks if c.check_name == "heading_hierarchy")
        assert h_check.passed is True


def test_metadata_title_and_description_bounds(db_session: Session):
    """Requirement 2: Validate title (30-65 chars) and meta description (50-165 chars)."""
    results = ContentCitationEngine.generate_all_ten_drafts(session=db_session, use_llm=False, limit=10)

    for _, page, report in results:
        title_len = len(page.title)
        desc_len = len(page.meta_description)

        assert 30 <= title_len <= 65, f"Title length {title_len} out of bounds: {page.title}"
        assert 50 <= desc_len <= 165, f"Meta description length {desc_len} out of bounds: {page.meta_description}"

        t_check = next(c for c in report.checks if c.check_name == "title_length")
        assert t_check.passed is True
        d_check = next(c for c in report.checks if c.check_name == "meta_description_length")
        assert d_check.passed is True


def test_internal_link_suggestions_and_anchor_text(db_session: Session):
    """Requirement 2: Include internal-link suggestions with descriptive anchor texts."""
    results = ContentCitationEngine.generate_all_ten_drafts(session=db_session, use_llm=False, limit=10)

    for _, page, report in results:
        assert len(page.internal_links) >= 1
        for link in page.internal_links:
            assert link["url"].startswith("/")
            anchor = link["anchor"].lower()
            # Must NOT use generic non-descriptive anchor text
            assert anchor not in ("click here", "here", "read more", "link")

        # Internal link check in report
        il_check = next(c for c in report.checks if c.check_name == "internal_link_suggestions")
        assert il_check.passed is True


def test_sourced_citations_real_third_party(db_session: Session):
    """Requirement 2 & 3: Include real third-party citations without inventing sources."""
    results = ContentCitationEngine.generate_all_ten_drafts(session=db_session, use_llm=False, limit=10)

    allowed_authority_publishers = [
        "Google Search Central", "HubSpot", "arXiv", "Search Engine Land",
        "Perplexity AI", "OpenAI", "Wyzowl", "Vimeo", "Search Engine Journal",
        "TechCrunch", "VentureBeat", "Schema.org", "W3C", "Backlinko",
        "Ahrefs", "Anthropic",
    ]

    for _, page, report in results:
        assert len(page.citations) >= 1
        for cite in page.citations:
            assert cite["url"].startswith("https://")
            assert any(pub in cite["publisher"] for pub in allowed_authority_publishers)

        cite_check = next(c for c in report.checks if c.check_name == "sourced_citations")
        assert cite_check.passed is True


def test_appropriate_structured_data_json_ld(db_session: Session):
    """Requirement 2: Include appropriate Schema.org structured data."""
    results = ContentCitationEngine.generate_all_ten_drafts(session=db_session, use_llm=False, limit=10)

    for _, page, report in results:
        schema = page.schema_org_json
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] in ("TechArticle", "HowTo", "FAQPage")
        assert "headline" in schema or "name" in schema
        assert schema["publisher"]["name"] == "IncuBrix"

        schema_check = next(c for c in report.checks if c.check_name == "schema_org_json_ld")
        assert schema_check.passed is True


def test_thirty_real_third_party_citation_opportunities(db_session: Session):
    """Requirement 4: Research and store 30 specific real third-party citation opportunities.

    Captures URLs, related questions, relevance and legitimate potential angles.
    """
    assert len(THIRTY_REAL_CITATION_TARGETS) == 30

    seeded = ContentCitationEngine.seed_thirty_citation_opportunities(session=db_session)
    assert len(seeded) == 30

    cite_repo = CitationRepository(db_session)
    stored_targets = cite_repo.list_targets(limit=50)
    assert len(stored_targets) == 30

    for target in stored_targets:
        assert target.target_domain is not None
        assert target.target_url is not None
        assert target.target_url.startswith("https://")
        assert target.relevance is not None and len(target.relevance) > 10
        assert target.pitch_angle is not None and len(target.pitch_angle) > 10
        assert target.authority_score is not None and 70 <= target.authority_score <= 100
        assert target.outreach_status == "identified"
        assert target.competitor_domain is not None


def test_deterministic_template_fallback_when_llm_unconfigured():
    """Requirement 5: Use optional configurable LLM provider and deterministic template fallback."""
    bp = APPROVED_CREATOR_QUESTIONS[0]

    # When LLM is requested but not configured, it gracefully produces deterministic output
    page_draft = ContentCitationEngine.generate_page_draft(
        brief_id="test-brief-id",
        blueprint=bp,
        use_llm=True,  # Requested LLM
    )

    assert page_draft.brief_id == "test-brief-id"
    assert page_draft.title == bp["title"]
    assert page_draft.slug == bp["slug"]
    assert page_draft.word_count > 200
    assert page_draft.publication_status == "unreviewed"


def test_drafts_labeled_unreviewed_until_human_verification(db_session: Session):
    """Requirement 7: Label drafts as unreviewed until human verification."""
    results = ContentCitationEngine.generate_all_ten_drafts(session=db_session, use_llm=False, limit=2)
    _, page_model, _ = results[0]

    # Initial state is unreviewed
    assert page_model.publication_status == "unreviewed"

    content_repo = ContentRepository(db_session)
    # Human reviewer verification workflow
    updated = content_repo.update_page_status(
        page_id=page_model.id,
        publication_status="approved",
        notes="Verified factual accuracy, citations, and product capabilities.",
    )
    assert updated is not None
    assert updated.publication_status == "approved"
    assert updated.schema_org_json.get("review_notes") is not None


def test_content_validator_detects_defects():
    """Requirement 6: ContentValidator detects defects and marks publish_ready=False."""
    defective_page = GeneratedPageCreate(
        brief_id="test-id",
        title="Short Title Here",  # Defect: 16 chars (< 30 optimal)
        slug="defective-page",
        meta_description="This description is under fifty characters long.",  # Defect: 48 chars (< 50 optimal)
        markdown_content="In this blog post we will discuss video workflows for creators in great detail without an H1 heading.",  # Defect: fluff opening, missing H1, missing H2s
        schema_org_json={},  # Defect: empty schema
        publication_status="published",  # Defect: cannot be published without review
        internal_links=[],  # Defect: missing internal links
        citations=[],  # Defect: missing citations
    )

    report = ContentValidator.validate_page(defective_page)
    assert report.is_publish_ready is False
    assert len(report.recommendations) > 0
    assert any(c.check_name == "title_length" and not c.passed for c in report.checks)
    assert any(c.check_name == "direct_answer_first_two_sentences" and not c.passed for c in report.checks)
    assert any(c.check_name == "unreviewed_safety_status" and not c.passed for c in report.checks)


def test_content_and_citation_api_endpoints(client: TestClient, db_session: Session):
    """Verify HTTP API endpoints for batch page generation, validation, review, and citations."""
    # 1. Seed 30 citation targets via API
    seed_resp = client.post("/v1/citations/seed-catalog")
    assert seed_resp.status_code == 201
    seed_data = seed_resp.json()
    assert seed_data["total_seeded"] == 30
    assert len(seed_data["domains_seeded"]) > 10

    # 2. List citation targets with domain filter
    list_cite_resp = client.get("/v1/citations/targets?domain=searchengineland.com")
    assert list_cite_resp.status_code == 200
    targets = list_cite_resp.json()
    assert len(targets) >= 1
    assert targets[0]["target_domain"] == "searchengineland.com"
    assert targets[0]["pitch_angle"] is not None

    # 3. Batch generate 10 publish-ready page drafts
    batch_resp = client.post("/v1/content/generate-batch", json={"use_llm": False, "limit": 10})
    assert batch_resp.status_code == 201
    batch_data = batch_resp.json()
    assert batch_data["total_generated"] == 10
    assert len(batch_data["pages"]) == 10
    assert len(batch_data["validation_reports"]) == 10

    first_page = batch_data["pages"][0]
    assert first_page["publication_status"] == "unreviewed"
    page_id = first_page["id"]
    slug = first_page["slug"]

    # 4. Fetch page by slug
    slug_resp = client.get(f"/v1/content/pages/{slug}")
    assert slug_resp.status_code == 200
    assert slug_resp.json()["id"] == page_id

    # 5. Validate page draft via API
    val_resp = client.post(f"/v1/content/validate/{page_id}")
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["is_publish_ready"] is True
    assert val_data["direct_answer_verified"] is True

    # 6. Human review status curation via API
    review_resp = client.patch(
        f"/v1/content/pages/{page_id}/review",
        json={"publication_status": "approved", "reviewer_notes": "Senior editor verified facts."},
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["publication_status"] == "approved"

    # 7. List pages filtered by status
    unreviewed_resp = client.get("/v1/content/pages?status=unreviewed")
    assert unreviewed_resp.status_code == 200
    assert len(unreviewed_resp.json()) == 9  # 1 was approved
