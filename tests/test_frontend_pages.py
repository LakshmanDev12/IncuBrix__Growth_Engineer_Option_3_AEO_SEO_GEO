"""Tests for Streamlit Frontend Architecture, Pages, and Components."""

import ast
from pathlib import Path
from app.frontend.ui_components import get_provenance_badge_markdown
from app.frontend.template_renderer import (
    render_overview_view,
    render_seo_aeo_view,
    render_geo_view,
    render_questions_view,
    render_audit_view,
    render_content_view,
    render_citations_view,
    render_scans_view,
    render_settings_view,
)


def test_provenance_badge_mapping():
    """Verify provenance classification badges."""
    live_obs = {"collection_status": "success", "provider": "google_search"}
    assert ":green-badge[REAL LIVE]" in get_provenance_badge_markdown(live_obs)

    manual_obs = {"collection_status": "success", "provider": "manual_review", "meta": {"is_manual_evidence": True}}
    assert ":blue-badge[MANUAL IMPORT]" in get_provenance_badge_markdown(manual_obs)

    mocked_obs = {"collection_status": "success", "meta": {"is_synthetic_test_fixture": True}}
    assert ":orange-badge[MOCKED FIXTURE]" in get_provenance_badge_markdown(mocked_obs)

    unavail_obs = {"collection_status": "unavailable"}
    assert ":gray-badge[UNAVAILABLE]" in get_provenance_badge_markdown(unavail_obs)


def test_frontend_page_modules_exist():
    """Ensure all 9 required pages exist in app/frontend/app_pages/ and have valid syntax."""
    frontend_dir = Path(__file__).parent.parent / "app" / "frontend"
    pages_dir = frontend_dir / "app_pages"
    
    expected_pages = [
        "overview.py",
        "seo_aeo.py",
        "geo.py",
        "questions.py",
        "audit.py",
        "content.py",
        "citations.py",
        "scans.py",
        "settings.py",
    ]
    
    assert pages_dir.exists(), "app_pages directory must exist"
    
    for page_name in expected_pages:
        page_path = pages_dir / page_name
        assert page_path.exists(), f"Page {page_name} must exist"
        
        # Verify valid Python syntax
        content = page_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(page_path))
        assert tree is not None


def test_theme_config_exists():
    """Ensure .streamlit/config.toml exists with enterprise dark theme tokens."""
    config_path = Path(__file__).parent.parent / ".streamlit" / "config.toml"
    assert config_path.exists(), ".streamlit/config.toml must exist"
    
    content = config_path.read_text(encoding="utf-8")
    assert "primaryColor" in content
    assert "backgroundColor" in content
    assert "Inter" in content


def test_template_renderer_views():
    """Verify that all template renderer views generate valid HTML with design elements."""
    dummy_data = {
        "score": 87,
        "avg_rank": "#2.0",
        "direct_links": 1,
        "evals": 2,
        "top10_rate": 100.0,
        "mention_rate": 100.0,
        "cite_rate": 100.0,
        "questions_count": 15,
        "questions": [{"id": "q1", "text": "Test question?", "intent": "informational", "review_status": "approved"}],
        "observations": [{"id": "o1", "provider": "google_search", "rank_position": 2, "answer_box_present": True}],
        "findings": [{"id": "f1", "severity": "critical", "issue_code": "ROBOTS_TXT_DISALLOW", "audit_category": "robots_txt", "validation_status": "validated"}],
        "pages": [{"id": "p1", "title": "Test Page", "slug": "test-page", "word_count": 800, "publication_status": "unreviewed", "markdown_content": "# Title\n\nDirect answer here."}],
        "targets": [{"id": "t1", "target_domain": "forbes.com", "authority_score": 92, "pitch_angle": "Pitch here", "gap_type": "competitor_gap"}],
        "runs": [{"id": "r1", "mode": "e2e", "status": "completed", "duration_seconds": 134.2, "processed_questions_count": 15}],
    }

    overview_html = render_overview_view(dummy_data)
    assert "Visibility score" in overview_html
    assert "band" in overview_html
    assert "kpis" in overview_html
    assert "Vk Analysis" in overview_html or "IncuBrix" in overview_html

    seo_html = render_seo_aeo_view(dummy_data)
    assert "SEO & AEO" in seo_html

    geo_html = render_geo_view(dummy_data)
    assert "GEO" in geo_html

    q_html = render_questions_view(dummy_data)
    assert "Question" in q_html

    audit_html = render_audit_view(dummy_data)
    assert "Technical SEO" in audit_html

    content_html = render_content_view(dummy_data)
    assert "Content" in content_html

    cite_html = render_citations_view(dummy_data)
    assert "Citation" in cite_html

    scans_html = render_scans_view(dummy_data)
    assert "Scan History" in scans_html

    settings_html = render_settings_view(dummy_data)
    assert "Settings" in settings_html
