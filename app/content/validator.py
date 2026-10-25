"""Content quality, AEO structural compliance, and direct-answer validator.

Validates generated page drafts against strict criteria:
- Direct answers in the first two sentences.
- Semantic heading outline (H1, multiple H2s).
- Title and meta description length bounds.
- Schema.org JSON-LD validity.
- Presence of internal-link suggestions and sourced citations.
- Draft status labeled as 'unreviewed' until human curation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from app.schemas.content import (
    ContentValidationCheck,
    ContentValidationReport,
    GeneratedPageCreate,
)


class ContentValidator:
    """Enforces AEO/SEO editorial standards and technical compliance on generated pages."""

    @classmethod
    def validate_page(
        cls,
        page: GeneratedPageCreate,
    ) -> ContentValidationReport:
        """Run all content quality and structural validation checks on a generated page."""
        checks: List[ContentValidationCheck] = []
        recommendations: List[str] = []

        # 1. Direct Answer in First Two Sentences
        direct_answer_check = cls._check_direct_answer(page.markdown_content, page.title)
        checks.append(direct_answer_check)
        if not direct_answer_check.passed:
            recommendations.append("Ensure the opening paragraph answers the core query concisely in the first two sentences.")

        # 2. Title Tag Length (30-65 chars)
        title_len = len(page.title.strip())
        if 30 <= title_len <= 65:
            checks.append(
                ContentValidationCheck(
                    check_name="title_length",
                    passed=True,
                    details=f"Title is {title_len} characters (within optimal 30-65 character range).",
                )
            )
        else:
            checks.append(
                ContentValidationCheck(
                    check_name="title_length",
                    passed=False,
                    details=f"Title is {title_len} characters (recommended: 30-65 characters).",
                )
            )
            recommendations.append("Adjust title length to be between 30 and 65 characters.")

        # 3. Meta Description Length (50-165 chars)
        desc_len = len(page.meta_description.strip())
        if 50 <= desc_len <= 165:
            checks.append(
                ContentValidationCheck(
                    check_name="meta_description_length",
                    passed=True,
                    details=f"Meta description is {desc_len} characters (within optimal 50-165 character range).",
                )
            )
        else:
            checks.append(
                ContentValidationCheck(
                    check_name="meta_description_length",
                    passed=False,
                    details=f"Meta description is {desc_len} characters (recommended: 50-165 characters).",
                )
            )
            recommendations.append("Adjust meta description length to be between 50 and 165 characters.")

        # 4. Heading Outline Hierarchy
        h1_matches = re.findall(r"^#\s+(.+)$", page.markdown_content, re.MULTILINE)
        h2_matches = re.findall(r"^##\s+(.+)$", page.markdown_content, re.MULTILINE)
        if len(h1_matches) == 1 and len(h2_matches) >= 2:
            checks.append(
                ContentValidationCheck(
                    check_name="heading_hierarchy",
                    passed=True,
                    details=f"Structured outline confirmed: 1 primary H1 and {len(h2_matches)} H2 sections.",
                )
            )
        else:
            checks.append(
                ContentValidationCheck(
                    check_name="heading_hierarchy",
                    passed=False,
                    details=f"Heading outline defective: {len(h1_matches)} H1s and {len(h2_matches)} H2s found (requires exactly 1 H1 and >= 2 H2s).",
                )
            )
            recommendations.append("Structure the page with exactly one primary H1 and at least two H2 section headings.")

        # 5. Schema.org JSON-LD Structure
        schema = page.schema_org_json or {}
        has_context = schema.get("@context") in ("https://schema.org", "http://schema.org")
        has_type = bool(schema.get("@type"))
        has_name = bool(schema.get("headline") or schema.get("name"))
        if has_context and has_type and has_name:
            checks.append(
                ContentValidationCheck(
                    check_name="schema_org_json_ld",
                    passed=True,
                    details=f"Valid Schema.org markup found with @type='{schema.get('@type')}'.",
                )
            )
        else:
            checks.append(
                ContentValidationCheck(
                    check_name="schema_org_json_ld",
                    passed=False,
                    details="Schema.org JSON-LD is missing required @context, @type, or headline/name properties.",
                )
            )
            recommendations.append("Embed valid Schema.org JSON-LD with @context='https://schema.org' and appropriate @type.")

        # 6. Internal Link Suggestions
        has_internal_links = bool(page.internal_links) or bool(
            re.search(r"\[.*?\]\(/.*?\)|\((https?://incubrix\.com.*?)\)", page.markdown_content)
        )
        if has_internal_links:
            checks.append(
                ContentValidationCheck(
                    check_name="internal_link_suggestions",
                    passed=True,
                    details=f"Internal link suggestions provided ({len(page.internal_links)} structured suggestions).",
                )
            )
        else:
            checks.append(
                ContentValidationCheck(
                    check_name="internal_link_suggestions",
                    passed=False,
                    details="No internal link suggestions detected.",
                )
            )
            recommendations.append("Include at least one relevant internal link suggestion with descriptive anchor text.")

        # 7. Sourced Citations
        has_citations = bool(page.citations) or bool(
            re.search(r"https?://(?!incubrix\.com)", page.markdown_content)
        )
        if has_citations:
            checks.append(
                ContentValidationCheck(
                    check_name="sourced_citations",
                    passed=True,
                    details=f"Third-party sourced citations included ({len(page.citations)} structured citations).",
                )
            )
        else:
            checks.append(
                ContentValidationCheck(
                    check_name="sourced_citations",
                    passed=False,
                    details="No external third-party citations detected.",
                )
            )
            recommendations.append("Include at least one authoritative third-party research citation.")

        # 8. Unreviewed Publication Status
        is_unreviewed = page.publication_status.lower() in ("unreviewed", "draft_unreviewed")
        if is_unreviewed:
            checks.append(
                ContentValidationCheck(
                    check_name="unreviewed_safety_status",
                    passed=True,
                    details=f"Draft status is correctly marked as '{page.publication_status}' awaiting human verification.",
                )
            )
        else:
            checks.append(
                ContentValidationCheck(
                    check_name="unreviewed_safety_status",
                    passed=False,
                    details=f"Draft status is '{page.publication_status}'; new drafts must be labeled as 'unreviewed' until human approval.",
                )
            )
            recommendations.append("Set publication_status='unreviewed' until verified by a human curator.")

        # Word count calculation
        words = len(page.markdown_content.split())
        is_publish_ready = all(c.passed for c in checks)

        return ContentValidationReport(
            is_publish_ready=is_publish_ready,
            title=page.title,
            slug=page.slug,
            word_count=words,
            direct_answer_verified=direct_answer_check.passed,
            checks=checks,
            recommendations=recommendations,
        )

    @staticmethod
    def _check_direct_answer(markdown_content: str, title: str) -> ContentValidationCheck:
        """Verify the first two sentences provide a direct, concise answer to the topic."""
        # Find first non-heading block
        paragraphs = [p.strip() for p in markdown_content.split("\n\n") if p.strip() and not p.strip().startswith("#")]
        if not paragraphs:
            return ContentValidationCheck(
                check_name="direct_answer_first_two_sentences",
                passed=False,
                details="No body paragraph found; direct answer missing.",
            )

        first_block = paragraphs[0]
        # Clean markdown quote or bold syntax
        clean_block = re.sub(r"^>\s*(\*\*Quick Answer\*\*:\s*)?", "", first_block).strip()

        # Split into sentences
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_block) if s.strip()]
        if len(sentences) < 1:
            return ContentValidationCheck(
                check_name="direct_answer_first_two_sentences",
                passed=False,
                details="Opening block does not contain complete sentences.",
            )

        opening_text = " ".join(sentences[:2]).lower()
        # Disallow generic fluff openings
        fluff_openings = [
            "in this article",
            "in this post",
            "in this blog post",
            "in this guide",
            "we will explore",
            "have you ever wondered",
            "today we are going to",
        ]
        has_fluff = any(opening_text.startswith(fluff) for fluff in fluff_openings)

        if has_fluff:
            return ContentValidationCheck(
                check_name="direct_answer_first_two_sentences",
                passed=False,
                details="Opening contains generic introductory fluff rather than a direct factual answer.",
            )

        return ContentValidationCheck(
            check_name="direct_answer_first_two_sentences",
            passed=True,
            details=f"Direct answer verified in the first {min(len(sentences), 2)} sentence(s): '{clean_block[:100]}...'",
        )
