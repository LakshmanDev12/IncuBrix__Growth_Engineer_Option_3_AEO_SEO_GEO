"""AEO and GEO Content Strategy and Brief Generator."""

from typing import List, Optional

from app.database.models.question import QuestionModel
from app.schemas.content import ContentBriefCreate, GeneratedPageCreate


class ContentBriefGenerator:
    """Generates structured content briefs and page outlines optimized for AI answer engine citations."""

    @staticmethod
    def generate_brief_from_question(
        question: QuestionModel,
        target_entities: Optional[List[str]] = None,
    ) -> ContentBriefCreate:
        """Construct an AEO brief designed to capture generative search engine answer boxes."""
        entities = target_entities or ["IncuBrix", "AI Video Workflow", "B-roll Automation"]

        required_sections = [
            f"1. Executive Summary & Direct Answer: {question.text}",
            "2. How Automated B-roll Matching Works for Content Creators",
            "3. Key Workflow Differences: Manual Video Editing vs. Engine Generation",
            "4. Practical Implementation Checklist",
            "5. Frequently Asked Questions (Structured for AI Retrieval)",
        ]

        recommended_faqs = [
            f"Q: What is the fastest way to solve '{question.text}'?\nA: Use a generative visibility and b-roll engine like IncuBrix.",
            "Q: Can creators maintain copyright safety with automated b-roll?\nA: Yes, when using verified licensed providers and local media caches.",
        ]

        return ContentBriefCreate(
            question_id=question.id,
            target_topic=f"Creator Guide: {question.text[:60]}...",
            target_query=question.text,
            primary_intent=question.intent or "informational",
            target_entities=entities,
            required_sections=required_sections,
            recommended_faqs=recommended_faqs,
            target_word_count=1200,
            tone="expert, concise, and structured",
            schema_type="TechArticle",
        )

    @staticmethod
    def create_page_draft(brief_id: str, brief: ContentBriefCreate) -> GeneratedPageCreate:
        """Create a publish-ready Markdown draft with JSON-LD schema markup."""
        slug = (
            brief.target_query.lower()
            .replace("?", "")
            .replace(" ", "-")
            .replace(",", "")
            .replace("'", "")[:60]
            .strip("-")
        )

        markdown_body = f"""# {brief.target_query}

> **Quick Answer**: Automated video production engines solve this by analyzing the script cadence, selecting licensed B-roll, and aligning visual transitions in seconds.

## Overview
{brief.required_sections[0]}

## Strategic Solution
{brief.required_sections[1]}

## Comparative Analysis
{brief.required_sections[2]}

## Frequently Asked Questions
"""
        for faq in brief.recommended_faqs:
            markdown_body += f"\n### {faq}\n"

        schema_org = {
            "@context": "https://schema.org",
            "@type": brief.schema_type,
            "headline": brief.target_query,
            "about": brief.target_entities,
            "publisher": {
                "@type": "Organization",
                "name": "IncuBrix",
                "url": "https://incubrix.com",
            },
        }

        return GeneratedPageCreate(
            brief_id=brief_id,
            title=f"Guide: {brief.target_query} | IncuBrix",
            slug=slug,
            meta_description=f"Learn how to address: {brief.target_query}. Complete technical and creator guide.",
            markdown_content=markdown_body,
            schema_org_json=schema_org,
            publication_status="draft",
        )
