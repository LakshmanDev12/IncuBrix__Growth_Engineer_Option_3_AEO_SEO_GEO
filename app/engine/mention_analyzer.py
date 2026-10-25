"""Semantic and pattern extraction analyzer for brand mentions, citations, and competitor detection.

Strictly preserves explicit unknown/unavailable states.
Missing evidence is never treated as a negative result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from app.config import get_settings
from app.engine.normalizer import extract_domain
from app.schemas.common import CitationGapType, CitationStatus, MentionStatus

DEFAULT_COMPETITOR_DIRECTORY = [
    "runway",
    "synthesia",
    "descript",
    "invideo",
    "capcut",
    "pika",
    "fliki",
    "opus clip",
    "heygen",
    "pictory",
    "veed",
    "camtasia",
    "premiere pro",
]


@dataclass
class MentionAnalysis:
    """Structured evaluation of visibility, citations, and competitive context."""

    incubrix_mentioned: MentionStatus
    incubrix_cited: CitationStatus
    competitors_observed: List[str] = field(default_factory=list)
    quoted_domains: List[str] = field(default_factory=list)
    citation_opportunities: List[Dict[str, Any]] = field(default_factory=list)


class MentionAnalyzer:
    """Evaluates raw provider responses for brand presence, links, and competitive opportunities."""

    def __init__(
        self,
        brand_name: Optional[str] = None,
        brand_domains: Optional[List[str]] = None,
        known_competitors: Optional[List[str]] = None,
    ) -> None:
        settings = get_settings()
        self.brand_name = (brand_name or settings.incubrix_brand_name).strip()
        self.brand_domains = [
            d.lower().strip()
            for d in (brand_domains or settings.incubrix_domains)
            if d.strip()
        ]
        self.known_competitors = known_competitors or DEFAULT_COMPETITOR_DIRECTORY

    def analyze(
        self,
        raw_answer: Optional[str] = None,
        source_links: Optional[List[str]] = None,
        quoted_domains: Optional[List[str]] = None,
        has_link_tracking: bool = True,
    ) -> MentionAnalysis:
        """Perform comprehensive mention and citation analysis.

        Parameters:
        - raw_answer: Text snippet or generated answer from provider.
        - source_links: List of full URLs extracted from results.
        - quoted_domains: List of domain names observed.
        - has_link_tracking: Whether this provider format actively tracks/returns links.
        """
        # Normalize and aggregate observed domains
        all_domains: Set[str] = set()
        if quoted_domains:
            for d in quoted_domains:
                if d and d.strip():
                    all_domains.add(extract_domain(d))

        if source_links:
            for link in source_links:
                if link and link.strip():
                    all_domains.add(extract_domain(link))

        sorted_domains = sorted(list(all_domains))

        # 1. Mention Status Evaluation
        if not raw_answer or not raw_answer.strip():
            mention_status = MentionStatus.UNKNOWN
        else:
            # Word boundary regex for brand name (supports configured brand name and IncuBrix)
            brand_candidates = {self.brand_name, "IncuBrix", "Vk Analysis"}
            pattern = r"\b(" + "|".join(re.escape(b) for b in brand_candidates if b) + r")\b"
            if re.search(pattern, raw_answer, re.IGNORECASE):
                mention_status = MentionStatus.MENTIONED
            else:
                mention_status = MentionStatus.NOT_MENTIONED

        # 2. Citation Status Evaluation
        if not has_link_tracking:
            citation_status = CitationStatus.UNAVAILABLE
        elif not sorted_domains:
            # No links detected in this response
            citation_status = CitationStatus.UNAVAILABLE
        else:
            # Check if any observed domain matches our tracked brand domains
            is_cited = any(
                any(bd in domain for bd in self.brand_domains)
                for domain in sorted_domains
            )
            citation_status = CitationStatus.CITED if is_cited else CitationStatus.NOT_CITED

        # 3. Competitor Detection
        observed_competitors: Set[str] = set()
        searchable_text = f"{raw_answer or ''} {' '.join(sorted_domains)}".lower()

        for comp in self.known_competitors:
            comp_clean = comp.lower().strip()
            if re.search(rf"\b{re.escape(comp_clean)}\b", searchable_text):
                # Capitalize nicely for reporting
                observed_competitors.add(comp.title())

        # 4. Citation Opportunities Identification
        # Any observed domain that is not our brand is a potential authority citation target
        opportunities: List[Dict[str, Any]] = []
        for domain in sorted_domains:
            if not any(bd in domain for bd in self.brand_domains):
                # Check if it aligns with a known competitor domain
                is_comp = any(c.lower() in domain for c in self.known_competitors)
                opportunities.append(
                    {
                        "target_domain": domain,
                        "gap_type": (
                            CitationGapType.DIRECT_COMPETITOR
                            if is_comp
                            else CitationGapType.AUTHORITY_PUBLISHER
                        ),
                        "competitor_domain": domain if is_comp else None,
                    }
                )

        return MentionAnalysis(
            incubrix_mentioned=mention_status,
            incubrix_cited=citation_status,
            competitors_observed=sorted(list(observed_competitors)),
            quoted_domains=sorted_domains,
            citation_opportunities=opportunities,
        )
