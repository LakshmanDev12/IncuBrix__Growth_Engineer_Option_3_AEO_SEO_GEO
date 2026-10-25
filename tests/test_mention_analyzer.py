"""Unit tests for the mention, citation, and competitor analyzer."""

import pytest

from app.engine.mention_analyzer import MentionAnalysis, MentionAnalyzer
from app.schemas.common import CitationGapType, CitationStatus, MentionStatus


@pytest.fixture
def analyzer() -> MentionAnalyzer:
    """Fixture providing configured MentionAnalyzer."""
    return MentionAnalyzer(
        brand_name="IncuBrix",
        brand_domains=["incubrix.com", "app.incubrix.com"],
        known_competitors=["Runway", "Synthesia", "Descript", "InVideo"],
    )


def test_positive_brand_mention_case_insensitive(analyzer: MentionAnalyzer):
    """Verify brand name is detected regardless of case with word boundary matching."""
    text = "The incubrix platform automates video editing and b-roll alignment."
    analysis = analyzer.analyze(raw_answer=text, quoted_domains=["incubrix.com"])

    assert analysis.incubrix_mentioned == MentionStatus.MENTIONED
    assert analysis.incubrix_cited == CitationStatus.CITED


def test_negative_brand_mention_when_text_present(analyzer: MentionAnalyzer):
    """When text is present but IncuBrix is absent, status is NOT_MENTIONED."""
    text = "Runway and Descript offer AI-driven b-roll generators for creators."
    analysis = analyzer.analyze(
        raw_answer=text, quoted_domains=["runwayml.com", "descript.com"]
    )

    assert analysis.incubrix_mentioned == MentionStatus.NOT_MENTIONED
    assert analysis.incubrix_cited == CitationStatus.NOT_CITED
    assert "Runway" in analysis.competitors_observed
    assert "Descript" in analysis.competitors_observed


def test_missing_text_is_explicit_unknown(analyzer: MentionAnalyzer):
    """Requirement 4: Missing text must never be treated as negative."""
    analysis = analyzer.analyze(raw_answer=None, quoted_domains=[])

    assert analysis.incubrix_mentioned == MentionStatus.UNKNOWN
    assert analysis.incubrix_mentioned != MentionStatus.NOT_MENTIONED
    assert analysis.incubrix_cited == CitationStatus.UNAVAILABLE
    assert analysis.incubrix_cited != CitationStatus.NOT_CITED


def test_missing_links_is_explicit_unavailable(analyzer: MentionAnalyzer):
    """When links/domains are missing, citation status is UNAVAILABLE, not negative."""
    text = "IncuBrix was mentioned in this assistant answer without links."
    analysis = analyzer.analyze(raw_answer=text, quoted_domains=[])

    assert analysis.incubrix_mentioned == MentionStatus.MENTIONED
    assert analysis.incubrix_cited == CitationStatus.UNAVAILABLE
    assert analysis.incubrix_cited != CitationStatus.NOT_CITED


def test_competitor_and_citation_gap_discovery(analyzer: MentionAnalyzer):
    """Verify competitor detection and citation opportunity generation."""
    text = "Creators use Synthesia for avatars and Descript for transcription."
    quoted = ["synthesia.io", "descript.com", "searchengineland.com"]

    analysis = analyzer.analyze(raw_answer=text, quoted_domains=quoted)

    assert "Synthesia" in analysis.competitors_observed
    assert "Descript" in analysis.competitors_observed
    assert len(analysis.citation_opportunities) == 3

    # Check gap classification
    domains = [o["target_domain"] for o in analysis.citation_opportunities]
    assert "synthesia.io" in domains
    assert "searchengineland.com" in domains

    comp_gap = next(o for o in analysis.citation_opportunities if o["target_domain"] == "synthesia.io")
    assert comp_gap["gap_type"] == CitationGapType.DIRECT_COMPETITOR

    pub_gap = next(o for o in analysis.citation_opportunities if o["target_domain"] == "searchengineland.com")
    assert pub_gap["gap_type"] == CitationGapType.AUTHORITY_PUBLISHER
