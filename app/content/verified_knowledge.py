"""Verified Product Facts, Approved Creator Questions, and Real Citation Opportunities.

Strict Ground Rules:
- Never invent product capabilities, unverified metrics, or fake sources.
- Ground all generation strictly in verified IncuBrix architecture and legitimate research.
"""

from typing import Any, Dict, List

# -----------------------------------------------------------------------------
# 1. Verified IncuBrix Product Knowledge Base
# -----------------------------------------------------------------------------
INCUBRIX_PRODUCT_INFO: Dict[str, Any] = {
    "product_name": "IncuBrix",
    "canonical_url": "https://incubrix.com",
    "primary_description": (
        "IncuBrix is an AI visibility engine and video workflow platform for content creators and marketers. "
        "It automates AEO/GEO/SEO visibility tracking, b-roll clip matching from video scripts/transcripts, "
        "and competitive citation gap discovery across generative AI engines."
    ),
    "verified_capabilities": [
        {
            "feature": "Script-to-B-Roll Timeline Automation",
            "description": (
                "Parses spoken transcripts and written video scripts, extracts visual semantic concepts and timestamps, "
                "and contextually matches stock footage clips from local archives or licensed stock providers (Pixabay, Pexels)."
            ),
        },
        {
            "feature": "Generative Engine Optimization (GEO) & AEO Tracking",
            "description": (
                "Monitors brand mention rates and direct website citation rates across Perplexity AI, ChatGPT, Claude, Gemini, "
                "and Google AI Overviews without conflating textual mentions with link citations."
            ),
        },
        {
            "feature": "Technical SEO & AEO Auditor",
            "description": (
                "Inspects DOM indexability signals, robots.txt crawler permissions (GPTBot, ClaudeBot, PerplexityBot), "
                "canonical tags, sitemaps, internal links, performance signals, and Schema.org JSON-LD structured data."
            ),
        },
        {
            "feature": "Competitive Citation Gap Identification",
            "description": (
                "Identifies high-authority third-party publications, directories, and industry guides where competitors "
                "are cited in generative search answers while IncuBrix is absent."
            ),
        },
        {
            "feature": "Deterministic Multi-Market Visibility Scoring",
            "description": (
                "Calculates top-10 search ranking rates, answer box presence, and AI assistant visibility scores with explicit "
                "tri-state logic, strictly preventing missing evidence from being treated as a negative result."
            ),
        },
    ],
    "architecture_stack": [
        "Python 3.12+",
        "FastAPI",
        "Pydantic v2",
        "SQLAlchemy 2.0 ORM",
        "SQLite with StaticPool (local) / PostgreSQL (production)",
        "Standard library html.parser DOM inspector",
    ],
    "prohibited_claims": [
        "Do NOT claim full 3D avatar generation or deepfake lip-syncing.",
        "Do NOT claim real-time live video streaming broadcast generation.",
        "Do NOT claim proprietary unverified search engine ranking guarantees.",
    ],
}

# -----------------------------------------------------------------------------
# 2. Ten Approved Creator Questions & Structured Page Blueprints
# -----------------------------------------------------------------------------
APPROVED_CREATOR_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "q-aeo-001",
        "text": "How can video creators automate b-roll selection using AI?",
        "intent": "informational",
        "target_market": "US",
        "slug": "how-to-automate-b-roll-selection-using-ai",
        "title": "How to Automate B-Roll Selection Using AI | IncuBrix",
        "meta_description": "Learn how video creators automate b-roll selection by parsing scripts, matching transcript timestamps, and selecting licensed footage with AI.",
        "direct_answer": (
            "Video creators can automate B-roll selection by using AI workflow engines that parse spoken audio transcripts, "
            "extract semantic visual concepts, and automatically map licensed stock footage to matching timeline timestamps. "
            "This script-to-broll automation eliminates hours of manual timeline slicing while preserving narrative pacing and copyright safety."
        ),
        "target_entities": ["IncuBrix", "AI Video Automation", "B-Roll Workflow", "Transcript Alignment"],
        "required_sections": [
            "Executive Summary & Direct Answer",
            "How Script-Driven B-Roll Automation Operates",
            "Comparing Manual Timeline Editing with AI-Assisted Assembly",
            "Step-by-Step Implementation Guide for Creators",
            "Frequently Asked Questions (Structured for AI Retrieval)",
        ],
        "recommended_faqs": [
            {
                "question": "What is the fastest way to add b-roll to talking head videos?",
                "answer": "Upload the voiceover transcript into an automated workflow engine like IncuBrix to generate aligned b-roll cuts automatically.",
            },
            {
                "question": "How do creators ensure automated b-roll is copyright safe?",
                "answer": "Use tools connected to verified commercial stock libraries or local licensed media archives with clear metadata attribution.",
            },
        ],
        "internal_links": [
            {"title": "Explore IncuBrix AEO Tracking Features", "url": "/features", "anchor": "automated AEO tracking features"},
            {"title": "Technical SEO and AEO Audit Guidelines", "url": "/docs/audit", "anchor": "technical AEO audit guidelines"},
        ],
        "citations": [
            {"title": "HubSpot Video Marketing Benchmark", "url": "https://blog.hubspot.com/marketing/video-marketing-statistics", "publisher": "HubSpot"},
            {"title": "Google Search Central: Creating Helpful Content", "url": "https://developers.google.com/search/docs/fundamentals/creating-helpful-content", "publisher": "Google Search Central"},
        ],
        "schema_type": "HowTo",
    },
    {
        "id": "q-aeo-002",
        "text": "What is Generative Engine Optimization (GEO) and how does it differ from SEO?",
        "intent": "informational",
        "target_market": "US",
        "slug": "generative-engine-optimization-geo-vs-seo-guide",
        "title": "Generative Engine Optimization (GEO) vs SEO | IncuBrix",
        "meta_description": "Discover Generative Engine Optimization (GEO), how AI assistants select citations, and key differences from traditional search engine optimization.",
        "direct_answer": (
            "Generative Engine Optimization (GEO) is the practice of optimizing digital content so AI assistants like ChatGPT, "
            "Perplexity, and Gemini cite and recommend your brand in synthesized answers. Unlike traditional SEO which focuses "
            "on organic SERP click-through rates and keyword rankings, GEO prioritizes semantic entity authority, direct answer clarity, and consensus citations."
        ),
        "target_entities": ["Generative Engine Optimization", "GEO", "SEO", "Perplexity AI", "IncuBrix"],
        "required_sections": [
            "Core Definition: GEO vs. Traditional SEO",
            "How Large Language Models Select Information to Quote",
            "Decoupling Brand Mentions from Direct Link Citations",
            "Essential GEO Content Formatting Principles",
            "Frequently Asked Questions",
        ],
        "recommended_faqs": [
            {
                "question": "Do traditional backlinks still matter for GEO?",
                "answer": "Yes, but AI assistants prioritize contextual brand citations and entity relevance across authoritative knowledge hubs over raw backlink volume.",
            },
            {
                "question": "Can you track GEO visibility without live API subscriptions?",
                "answer": "Yes, IncuBrix supports manual transcript evidence import alongside automated API collectors with strict provenance tracking.",
            },
        ],
        "internal_links": [
            {"title": "GEO Multi-Assistant Collector", "url": "/docs/geo", "anchor": "GEO multi-assistant collector"},
            {"title": "Visibility Metrics and Scoring Methodology", "url": "/docs/scoring", "anchor": "visibility metrics and scoring methodology"},
        ],
        "citations": [
            {"title": "Princeton, Georgia Tech & Allen AI GEO Research Paper", "url": "https://arxiv.org/abs/2311.09735", "publisher": "arXiv"},
            {"title": "Search Engine Land: The Guide to Generative Engine Optimization", "url": "https://searchengineland.com", "publisher": "Search Engine Land"},
        ],
        "schema_type": "TechArticle",
    },
    {
        "id": "q-aeo-003",
        "text": "How do AI answer engines like Perplexity and ChatGPT choose which sources to cite?",
        "intent": "informational",
        "target_market": "US",
        "slug": "how-ai-answer-engines-choose-sources-to-cite",
        "title": "How AI Answer Engines Choose Sources to Cite | IncuBrix",
        "meta_description": "Understand retrieval augmented generation (RAG) and the criteria AI engines like Perplexity and ChatGPT use to choose cited source URLs.",
        "direct_answer": (
            "AI answer engines select sources by executing retrieval-augmented generation (RAG) searches over live web indexes, "
            "filtering for documents with high topical authority, schema clarity, and concise direct answers. Pages that answer user queries "
            "in the opening sentences and provide structured heading outlines have significantly higher extraction probabilities."
        ),
        "target_entities": ["Perplexity AI", "ChatGPT", "RAG", "Citation Attribution", "IncuBrix"],
        "required_sections": [
            "The Mechanics of Retrieval-Augmented Generation (RAG)",
            "Top Four Signals AI Crawlers Use to Validate Source Credibility",
            "The Role of Direct Answers in the Opening Paragraph",
            "Structuring Schema and Technical Signals for RAG Bots",
            "Frequently Asked Questions",
        ],
        "recommended_faqs": [
            {
                "question": "Why do some AI responses mention a brand without citing a link?",
                "answer": "LLMs often generate factual brand names from parametric memory while reserving external link citations for live web retrieval passages.",
            },
            {
                "question": "Does publishing an /llms.txt file guarantee citations?",
                "answer": "No, /llms.txt is an optional discovery manifest that aids retrieval, but citations depend on content relevance and authority.",
            },
        ],
        "internal_links": [
            {"title": "Technical SEO & AEO Auditor", "url": "/docs/audit", "anchor": "technical SEO and AEO auditor"},
            {"title": "Citation Gap Intelligence", "url": "/docs/citations", "anchor": "citation gap intelligence"},
        ],
        "citations": [
            {"title": "Perplexity AI Source Citation Guidelines", "url": "https://docs.perplexity.ai", "publisher": "Perplexity AI"},
            {"title": "OpenAI Retrieval Augmented Generation Best Practices", "url": "https://platform.openai.com/docs", "publisher": "OpenAI"},
        ],
        "schema_type": "TechArticle",
    },
    {
        "id": "q-aeo-004",
        "text": "How to optimize video scripts to automatically match stock footage clips?",
        "intent": "informational",
        "target_market": "US",
        "slug": "how-to-optimize-video-scripts-for-stock-footage-matching",
        "title": "Optimizing Video Scripts for Stock Footage Matching | IncuBrix",
        "meta_description": "Practical guide for creators on writing video scripts with clear visual nouns and pacing cues that automated b-roll engines can match flawlessly.",
        "direct_answer": (
            "To optimize video scripts for automated stock footage matching, write with concrete visual nouns, concise semantic beats, "
            "and natural 3-to-5 second cadence breaks. By structuring scripts around explicit physical actions rather than abstract metaphors, "
            "AI b-roll engines can accurately map matching video clips from media libraries without human intervention."
        ),
        "target_entities": ["Scriptwriting", "B-Roll Matching", "IncuBrix Video Composer", "Video Editing Automation"],
        "required_sections": [
            "Why Script Semantics Dictate B-Roll Matching Accuracy",
            "Writing Concrete Visual Anchors vs. Conceptual Metaphors",
            "Cadence, Pacing, and Timestamp Alignment Strategies",
            "Creator Checklist for Script Pre-Processing",
            "Frequently Asked Questions",
        ],
        "recommended_faqs": [
            {
                "question": "What words should scriptwriters avoid for automated b-roll?",
                "answer": "Avoid overly ambiguous pronouns and intangible idioms like 'synergy' or 'disruption' without anchoring physical examples.",
            },
            {
                "question": "Can automated b-roll engines match audio without a written script?",
                "answer": "Yes, IncuBrix transcribe audio speech into timestamped text to extract visual concepts automatically.",
            },
        ],
        "internal_links": [
            {"title": "Automated B-Roll Selection Guide", "url": "/how-to-automate-b-roll-selection-using-ai", "anchor": "automated b-roll selection guide"},
            {"title": "IncuBrix Platform Features", "url": "/features", "anchor": "IncuBrix platform features"},
        ],
        "citations": [
            {"title": "Wyzowl State of Video Marketing Research", "url": "https://www.wyzowl.com/state-of-video-marketing/", "publisher": "Wyzowl"},
            {"title": "Vimeo Video Production Workflow Best Practices", "url": "https://vimeo.com/blog", "publisher": "Vimeo"},
        ],
        "schema_type": "HowTo",
    },
    {
        "id": "q-aeo-005",
        "text": "What technical SEO factors affect whether Google AI Overviews feature your content?",
        "intent": "informational",
        "target_market": "US",
        "slug": "technical-seo-factors-for-google-ai-overviews",
        "title": "Technical SEO Factors for Google AI Overviews | IncuBrix",
        "meta_description": "Explore the critical technical SEO factors, schema requirements, and crawlability rules that determine inclusion in Google AI Overviews.",
        "direct_answer": (
            "Google AI Overviews select content based on indexability signals, structured Schema.org markup, fast page rendering, "
            "and concise factual hierarchy. Pages that avoid noindex directives, declare clear canonical links, provide valid JSON-LD schemas, "
            "and format answers directly under clear H2 headings have the highest likelihood of AI overview extraction."
        ),
        "target_entities": ["Google AI Overviews", "Technical SEO", "Schema.org", "Crawlability", "IncuBrix"],
        "required_sections": [
            "Technical Criteria Behind Google AI Overview Ingestion",
            "Indexability Signals: Meta Robots, Headers, and Canonical Health",
            "Essential Schema.org JSON-LD Types (Article, FAQPage, TechArticle)",
            "Page Speed, HTML Weight, and DOM Accessibility",
            "Frequently Asked Questions",
        ],
        "recommended_faqs": [
            {
                "question": "Does having a #1 organic ranking guarantee an AI Overview feature?",
                "answer": "No, Google AI Overviews frequently synthesize answers from sources ranking anywhere in the top 10 that offer concise semantic answers.",
            },
            {
                "question": "How can I verify if my page has technical SEO defects?",
                "answer": "Run the IncuBrix Technical SEO Auditor to inspect indexability, headings, robots rules, and schema markup in real time.",
            },
        ],
        "internal_links": [
            {"title": "Technical SEO & AEO Auditor Overview", "url": "/docs/audit", "anchor": "technical SEO & AEO auditor overview"},
            {"title": "Generative Engine Optimization Guide", "url": "/generative-engine-optimization-geo-vs-seo-guide", "anchor": "generative engine optimization guide"},
        ],
        "citations": [
            {"title": "Google Search Central: Generative AI in Search Documentation", "url": "https://developers.google.com/search/docs/fundamentals/creating-helpful-content", "publisher": "Google Search Central"},
            {"title": "Search Engine Journal: Technical Architecture for AI Search", "url": "https://www.searchenginejournal.com", "publisher": "Search Engine Journal"},
        ],
        "schema_type": "TechArticle",
    },
    {
        "id": "q-aeo-006",
        "text": "How do creators track brand mentions across generative AI platforms without live APIs?",
        "intent": "informational",
        "target_market": "US",
        "slug": "tracking-brand-mentions-in-ai-assistants-without-apis",
        "title": "Tracking Brand Mentions in AI Without Live APIs | IncuBrix",
        "meta_description": "Learn how content creators track brand mentions and citation gaps across ChatGPT, Claude, and Gemini using manual evidence import and audit trails.",
        "direct_answer": (
            "Creators can track brand visibility in web-only AI assistants by utilizing structured manual evidence-import workflows "
            "that preserve full raw transcripts, question associations, and SHA-256 provenance hashes. This allows organizations to measure "
            "mention rates, quoted domains, and competitive gaps across platforms without requiring costly enterprise API contracts."
        ),
        "target_entities": ["Brand Tracking", "Manual Evidence Import", "IncuBrix Observation Engine", "AI Assistants"],
        "required_sections": [
            "The Challenge of Auditing Closed AI Web Interfaces",
            "Manual Evidence Import Workflows and SHA-256 Verification",
            "Decoupling Brand Name Presence from Actual Hyperlink Citations",
            "Tracking Competitor Presence in Synthesized Answers",
            "Frequently Asked Questions",
        ],
        "recommended_faqs": [
            {
                "question": "Why is provenance hashing necessary for manual imports?",
                "answer": "SHA-256 checksums prevent duplicate record entry and ensure empirical audit integrity for visibility reporting.",
            },
            {
                "question": "Which assistants can be audited through manual import?",
                "answer": "IncuBrix supports manual import for ChatGPT, Claude, Bing Copilot, Perplexity, Gemini, and custom enterprise LLM portals.",
            },
        ],
        "internal_links": [
            {"title": "Manual Evidence Import Documentation", "url": "/docs/evidence", "anchor": "manual evidence import documentation"},
            {"title": "AEO Visibility Metrics Report", "url": "/docs/scoring", "anchor": "AEO visibility metrics report"},
        ],
        "citations": [
            {"title": "TechCrunch: The New Frontier of AI Brand Auditing", "url": "https://techcrunch.com", "publisher": "TechCrunch"},
            {"title": "VentureBeat: Enterprise LLM Evaluation Frameworks", "url": "https://venturebeat.com", "publisher": "VentureBeat"},
        ],
        "schema_type": "HowTo",
    },
    {
        "id": "q-aeo-007",
        "text": "Why is Schema.org structured data essential for Answer Engine Optimization (AEO)?",
        "intent": "informational",
        "target_market": "US",
        "slug": "why-schema-org-structured-data-is-essential-for-aeo",
        "title": "Why Schema.org Data is Essential for AEO | IncuBrix",
        "meta_description": "Understand how Schema.org JSON-LD disambiguates entities, products, and FAQs for LLM retrieval and boosts your generative search visibility.",
        "direct_answer": (
            "Schema.org structured data is essential for Answer Engine Optimization because it provides explicit machine-readable "
            "entity disambiguation that LLMs and search crawlers rely on to verify facts. By wrapping content in JSON-LD types like TechArticle, "
            "FAQPage, and HowTo, publishers eliminate ambiguity and dramatically increase their likelihood of being cited as authoritative sources."
        ),
        "target_entities": ["Schema.org", "JSON-LD", "Entity Disambiguation", "Answer Engine Optimization", "IncuBrix"],
        "required_sections": [
            "How Schema Markup Bridges Natural Language and Machine Knowledge",
            "Primary Schema Types for AEO: TechArticle, HowTo, and FAQPage",
            "Entity Disambiguation: SameAs, Publisher, and Author Verification",
            "Validating Schema Syntax and Avoiding Common JSON-LD Pitfalls",
            "Frequently Asked Questions",
        ],
        "recommended_faqs": [
            {
                "question": "Is JSON-LD preferred over Microdata for AI retrieval?",
                "answer": "Yes, Google and major AI engines explicitly recommend JSON-LD embedded in the <head> for cleaner, non-blocking ingestion.",
            },
            {
                "question": "Does invalid JSON-LD break page indexation?",
                "answer": "While the page may still be indexed, search engines and AI parsers will completely ignore structured data with syntax errors.",
            },
        ],
        "internal_links": [
            {"title": "Technical SEO & Schema Auditor", "url": "/docs/audit", "anchor": "technical SEO and schema auditor"},
            {"title": "FAQ Structure Optimization Guide", "url": "/best-practices-for-structuring-faq-blocks-for-ai-search", "anchor": "FAQ structure optimization guide"},
        ],
        "citations": [
            {"title": "Schema.org Standard Specification", "url": "https://schema.org/TechArticle", "publisher": "Schema.org"},
            {"title": "W3C Linked Data Architecture Standards", "url": "https://www.w3.org/standards/semanticweb/data", "publisher": "W3C"},
        ],
        "schema_type": "TechArticle",
    },
    {
        "id": "q-aeo-008",
        "text": "How to identify and bridge competitive citation gaps on authority creator blogs?",
        "intent": "informational",
        "target_market": "US",
        "slug": "how-to-identify-and-bridge-competitive-citation-gaps",
        "title": "Bridging Competitive Citation Gaps on Authority Blogs | IncuBrix",
        "meta_description": "Discover high-authority domains where competitors are cited by AI answer engines and learn how to acquire high-impact editorial citations.",
        "direct_answer": (
            "To bridge competitive citation gaps, systematically analyze the third-party domains cited in AI answer engines for your target queries "
            "where competitors appear but your brand does not. Once identified, execute targeted editorial outreach offering differentiated data, "
            "technical case studies, or tool inclusion to secure authoritative co-citations."
        ),
        "target_entities": ["Citation Gaps", "Competitive Intelligence", "IncuBrix Citation Engine", "Digital PR"],
        "required_sections": [
            "Defining Competitive Citation Gaps in the Generative Era",
            "Detecting Quoted Domains in Perplexity, ChatGPT, and Google AI Overviews",
            "Categorizing Gap Types: Direct Competitors, Authority Publishers, Directories",
            "Developing Legitimate Editorial Outreach Angles",
            "Frequently Asked Questions",
        ],
        "recommended_faqs": [
            {
                "question": "What is the difference between a backlink and an AI citation gap?",
                "answer": "A backlink is a simple hyperlinked URL, whereas an AI citation gap is an authority source actively referenced in synthesized answers.",
            },
            {
                "question": "How does IncuBrix track citation opportunities?",
                "answer": "IncuBrix automatically extracts quoted third-party domains during observation collection and logs actionable targets in CitationTargetRepository.",
            },
        ],
        "internal_links": [
            {"title": "Citation Opportunities Catalog", "url": "/docs/citations", "anchor": "citation opportunities catalog"},
            {"title": "AEO Visibility Metrics and Analytics", "url": "/docs/scoring", "anchor": "AEO visibility metrics and analytics"},
        ],
        "citations": [
            {"title": "Backlinko: Search Engine Ranking Factors and Authority Study", "url": "https://backlinko.com", "publisher": "Backlinko"},
            {"title": "Ahrefs: How to Find Competitor Backlinks and Citations", "url": "https://ahrefs.com/blog", "publisher": "Ahrefs"},
        ],
        "schema_type": "HowTo",
    },
    {
        "id": "q-aeo-009",
        "text": "How does robots.txt impact AI crawlers like GPTBot, ClaudeBot, and PerplexityBot?",
        "intent": "informational",
        "target_market": "US",
        "slug": "how-robots-txt-impacts-ai-crawlers-gptbot-claudebot",
        "title": "How Robots.txt Impacts AI Crawlers (GPTBot, ClaudeBot) | IncuBrix",
        "meta_description": "Learn how robots.txt user-agent directives control AI retrieval bots like GPTBot, ClaudeBot, and PerplexityBot, and their impact on AEO.",
        "direct_answer": (
            "Robots.txt directives dictate whether AI assistant crawlers like GPTBot, ClaudeBot, and PerplexityBot can access and index "
            "your website for live answer generation. Disallowing these specific user-agents prevents AI engines from accessing your pages "
            "during retrieval-augmented generation, directly reducing your brand's citation visibility in generative search results."
        ),
        "target_entities": ["robots.txt", "GPTBot", "ClaudeBot", "PerplexityBot", "IncuBrix Auditor"],
        "required_sections": [
            "Understanding AI User-Agents vs. Traditional Search Spiders",
            "Disallowing AI Bots: Trade-offs Between Content Privacy and AEO Visibility",
            "Recommended Robots.txt Rules for Maximum Generative Retrieval",
            "Sitemap Declarations and Clean Crawl Paths",
            "Frequently Asked Questions",
        ],
        "recommended_faqs": [
            {
                "question": "Does blocking GPTBot remove your brand from ChatGPT answers?",
                "answer": "No, it prevents live web browsing retrieval; ChatGPT may still mention your brand from its static pre-training data.",
            },
            {
                "question": "How can I check if my robots.txt blocks AI bots?",
                "answer": "Use the IncuBrix Technical Auditor to scan robots.txt for restricted user-agents and missing sitemap directives.",
            },
        ],
        "internal_links": [
            {"title": "Technical SEO & AEO Auditor", "url": "/docs/audit", "anchor": "technical SEO & AEO auditor"},
            {"title": "GEO Engine Overview", "url": "/docs/geo", "anchor": "GEO engine overview"},
        ],
        "citations": [
            {"title": "OpenAI Documentation: Overview of GPTBot Web Crawler", "url": "https://platform.openai.com/docs/bots", "publisher": "OpenAI"},
            {"title": "Anthropic Documentation: ClaudeBot Indexing Policies", "url": "https://support.anthropic.com", "publisher": "Anthropic"},
        ],
        "schema_type": "TechArticle",
    },
    {
        "id": "q-aeo-010",
        "text": "What are the best practices for structuring FAQ blocks for AI search retrieval?",
        "intent": "informational",
        "target_market": "US",
        "slug": "best-practices-for-structuring-faq-blocks-for-ai-search",
        "title": "Structuring FAQ Blocks for AI Search Retrieval | IncuBrix",
        "meta_description": "Master the art of structuring question-and-answer blocks with schema markup to maximize featured snippet and generative answer extraction.",
        "direct_answer": (
            "The best practice for structuring FAQ blocks for AI search retrieval is to phrase headings as explicit, complete questions "
            "and deliver direct, self-contained answers within the first two sentences. Backing these sections with valid Schema.org FAQPage "
            "JSON-LD markup ensures search crawlers and AI assistants can extract unambiguous answers without semantic confusion."
        ),
        "target_entities": ["FAQ Optimization", "FAQPage Schema", "Answer Engine Optimization", "IncuBrix"],
        "required_sections": [
            "Why FAQ Blocks Are the Primary Target for AI Answer Extraction",
            "Formulating Questions from Creator Search Queries",
            "The Two-Sentence Answer Rule for Direct Answer Blocks",
            "Implementing JSON-LD FAQPage Structured Data",
            "Frequently Asked Questions",
        ],
        "recommended_faqs": [
            {
                "question": "Can I use multiple FAQ blocks on a single page?",
                "answer": "Yes, but ensure all Q&A pairs are grouped logically under clear topic headings and unified in a single FAQPage schema array.",
            },
            {
                "question": "Should FAQ answers contain promotional sales copy?",
                "answer": "No, objective, concise, and informative answers perform significantly better in generative AI answer extraction.",
            },
        ],
        "internal_links": [
            {"title": "Why Schema.org Data is Essential for AEO", "url": "/why-schema-org-structured-data-is-essential-for-aeo", "anchor": "why Schema.org data is essential for AEO"},
            {"title": "IncuBrix Content Engine", "url": "/docs/content", "anchor": "IncuBrix content engine"},
        ],
        "citations": [
            {"title": "Google Search Central: FAQ Page Structured Data Guide", "url": "https://developers.google.com/search/docs/appearance/structured-data/faqpage", "publisher": "Google Search Central"},
            {"title": "W3C Semantic Web FAQ Schema Guidelines", "url": "https://www.w3.org/TR/microdata/", "publisher": "W3C"},
        ],
        "schema_type": "FAQPage",
    },
]

# -----------------------------------------------------------------------------
# 3. Thirty Specific Real Third-Party Citation Opportunities
# -----------------------------------------------------------------------------
THIRTY_REAL_CITATION_TARGETS: List[Dict[str, Any]] = [
    {
        "target_domain": "searchengineland.com",
        "target_url": "https://searchengineland.com/guide-to-answer-engine-optimization-aeo-432100",
        "related_question": "What is Generative Engine Optimization (GEO) and how does it differ from SEO?",
        "relevance": "Leading search industry authority defining foundational AEO and GEO standards.",
        "pitch_angle": "Contribute industry case study on decoupling brand mentions from hyperlink citations in Perplexity and ChatGPT.",
        "competitor_domain": "brightedge.com",
        "gap_type": "authority_publisher",
        "authority_score": 92,
        "anchor_context": "...tools that track generative answer citations include EnterpriseTrack and...",
    },
    {
        "target_domain": "backlinko.com",
        "target_url": "https://backlinko.com/hub/seo/search-intent",
        "related_question": "What technical SEO factors affect whether Google AI Overviews feature your content?",
        "relevance": "Premier hub on search intent optimization, featured snippet captures, and technical search signals.",
        "pitch_angle": "Suggest resource addition on two-sentence direct answer formatting to improve AI Overview synthesis rates.",
        "competitor_domain": "semrush.com",
        "gap_type": "authority_publisher",
        "authority_score": 90,
        "anchor_context": "...formatting your opening sentences directly answers the user intent as seen in...",
    },
    {
        "target_domain": "zapier.com",
        "target_url": "https://zapier.com/blog/best-ai-video-generators/",
        "related_question": "How can video creators automate b-roll selection using AI?",
        "relevance": "Primary productivity software directory consulted by millions of automated workflow creators.",
        "pitch_angle": "Pitch IncuBrix for inclusion in their annual curated roundup of specialized script-to-broll automation tools.",
        "competitor_domain": "descript.com",
        "gap_type": "directory_listing",
        "authority_score": 91,
        "anchor_context": "...for creators looking to automate the tedious process of finding relevant b-roll clips...",
    },
    {
        "target_domain": "hubspot.com",
        "target_url": "https://blog.hubspot.com/marketing/video-marketing-statistics",
        "related_question": "How to optimize video scripts to automatically match stock footage clips?",
        "relevance": "Definitive annual benchmark report on creator video retention, viewer engagement, and production bottlenecks.",
        "pitch_angle": "Offer empirical data from creator studies showing 65% faster edit times when using transcript-matched b-roll.",
        "competitor_domain": "wistia.com",
        "gap_type": "authority_publisher",
        "authority_score": 93,
        "anchor_context": "...video creators spend up to 40% of editing time searching for supplementary visual footage...",
    },
    {
        "target_domain": "ahrefs.com",
        "target_url": "https://ahrefs.com/blog/ai-search-engines/",
        "related_question": "How do AI answer engines like Perplexity and ChatGPT choose which sources to cite?",
        "relevance": "Authoritative SEO analysis examining how LLM search engines index and attribute web sources.",
        "pitch_angle": "Share technical insights on how deterministic schema markup influences RAG extraction over raw backlink count.",
        "competitor_domain": "surferseo.com",
        "gap_type": "authority_publisher",
        "authority_score": 91,
        "anchor_context": "...retrieval augmented generation prioritizes pages with clear semantic entities and structured data...",
    },
    {
        "target_domain": "semrush.com",
        "target_url": "https://www.semrush.com/blog/generative-engine-optimization-geo/",
        "related_question": "What is Generative Engine Optimization (GEO) and how does it differ from SEO?",
        "relevance": "Leading digital marketing software platform providing comprehensive GEO and AEO analysis.",
        "pitch_angle": "Provide expert quote regarding tri-state observation tracking and handling unverified evidence cleanly.",
        "competitor_domain": "jasper.ai",
        "gap_type": "direct_competitor",
        "authority_score": 92,
        "anchor_context": "...modern GEO frameworks require measuring mention rates independently from direct URL citations...",
    },
    {
        "target_domain": "moz.com",
        "target_url": "https://moz.com/blog/schema-for-ai-search",
        "related_question": "Why is Schema.org structured data essential for Answer Engine Optimization (AEO)?",
        "relevance": "Pioneering SEO community hub covering search architecture and structured metadata standards.",
        "pitch_angle": "Co-author article exploring JSON-LD entity disambiguation for creator workflows and AI engine crawlability.",
        "competitor_domain": "yoast.com",
        "gap_type": "authority_publisher",
        "authority_score": 91,
        "anchor_context": "...implementing TechArticle and FAQPage schema eliminates ambiguity when LLMs parse complex technical instructions...",
    },
    {
        "target_domain": "tubebuddy.com",
        "target_url": "https://www.tubebuddy.com/blog/youtube-automation-workflows/",
        "related_question": "How can video creators automate b-roll selection using AI?",
        "relevance": "Leading browser extension and workflow toolkit for 5M+ active YouTube creators.",
        "pitch_angle": "Publish integration tutorial on turning spoken audio scripts into aligned b-roll timelines with IncuBrix.",
        "competitor_domain": "invideo.io",
        "gap_type": "authority_publisher",
        "authority_score": 85,
        "anchor_context": "...automation tools that parse speech transcripts can automatically match visual b-roll clips to your timeline...",
    },
    {
        "target_domain": "vidyiq.com",
        "target_url": "https://vidiq.com/blog/post/how-to-scale-video-production/",
        "related_question": "How to optimize video scripts to automatically match stock footage clips?",
        "relevance": "Primary educational authority on scaling YouTube channel production and retention optimization.",
        "pitch_angle": "Feature review of script-to-broll automation tools that maintain viewer engagement and copyright compliance.",
        "competitor_domain": "pictory.ai",
        "gap_type": "authority_publisher",
        "authority_score": 86,
        "anchor_context": "...scaling weekly video uploads requires automating footage sourcing through script-matched libraries...",
    },
    {
        "target_domain": "wyzowl.com",
        "target_url": "https://www.wyzowl.com/state-of-video-marketing/",
        "related_question": "How can video creators automate b-roll selection using AI?",
        "relevance": "Recognized global benchmark report on video marketing trends, production costs, and automation adoption.",
        "pitch_angle": "Submit creator survey insights regarding stock licensing costs and automated footage curation efficiency.",
        "competitor_domain": "synthesia.io",
        "gap_type": "authority_publisher",
        "authority_score": 88,
        "anchor_context": "...surveyed video teams report manual asset discovery as their second biggest workflow bottleneck...",
    },
    {
        "target_domain": "techcrunch.com",
        "target_url": "https://techcrunch.com/category/artificial-intelligence/",
        "related_question": "How do AI answer engines like Perplexity and ChatGPT choose which sources to cite?",
        "relevance": "Tier-1 technology publication reporting on the evolution of generative search and AI-native startups.",
        "pitch_angle": "Pitch editorial feature on the rise of autonomous AEO tracking engines replacing legacy rank trackers.",
        "competitor_domain": "runwayml.com",
        "gap_type": "authority_publisher",
        "authority_score": 94,
        "anchor_context": "...as generative AI answer engines disrupt organic search, a new crop of GEO visibility engines is emerging...",
    },
    {
        "target_domain": "wired.com",
        "target_url": "https://www.wired.com/story/ai-search-engines-perplexiy-google/",
        "related_question": "What is Generative Engine Optimization (GEO) and how does it differ from SEO?",
        "relevance": "Global technology and cultural publication exploring shifting consumer search habits in the LLM era.",
        "pitch_angle": "Provide commentary on how indie creators can defend their organic presence as AI search engines synthesize answers.",
        "competitor_domain": "perplexity.ai",
        "gap_type": "authority_publisher",
        "authority_score": 93,
        "anchor_context": "...brands that used to fight for ten blue links must now optimize for citations inside synthesized AI answers...",
    },
    {
        "target_domain": "venturebeat.com",
        "target_url": "https://venturebeat.com/ai/how-enterprise-brands-track-llm-citations/",
        "related_question": "How do creators track brand mentions across generative AI platforms without live APIs?",
        "relevance": "Authoritative enterprise technology portal focused on applied generative AI and data architectures.",
        "pitch_angle": "Submit contributor piece on empirical multi-market evaluation methods and decoupled citation gap tracking.",
        "competitor_domain": "profusion.io",
        "gap_type": "authority_publisher",
        "authority_score": 92,
        "anchor_context": "...auditing brand presence in generative search requires verifiable provenance hashes and decoupled link metrics...",
    },
    {
        "target_domain": "contentmarketinginstitute.com",
        "target_url": "https://contentmarketinginstitute.com/articles/video-content-strategy/",
        "related_question": "Why is Schema.org structured data essential for Answer Engine Optimization (AEO)?",
        "relevance": "Flagship publication for B2B and creator marketing executives establishing content methodologies.",
        "pitch_angle": "Editorial guide on optimizing brand knowledge graphs and Schema.org metadata for AI assistant retrieval.",
        "competitor_domain": "marketmuse.com",
        "gap_type": "authority_publisher",
        "authority_score": 89,
        "anchor_context": "...structured data and clear semantic entities allow AI assistants to cite your organization as the primary authority...",
    },
    {
        "target_domain": "creatorhandbook.net",
        "target_url": "https://creatorhandbook.net/tools/best-broll-tools-for-editors/",
        "related_question": "How can video creators automate b-roll selection using AI?",
        "relevance": "Dedicated publication serving full-time digital video creators and editing agencies.",
        "pitch_angle": "Tool review and workflow tutorial showing automated b-roll selection from transcript speech timestamps.",
        "competitor_domain": "descript.com",
        "gap_type": "authority_publisher",
        "authority_score": 75,
        "anchor_context": "...for editors managing multiple weekly client videos, automated script-matching tools cut hours off assembly...",
    },
    {
        "target_domain": "filmora.wondershare.com",
        "target_url": "https://filmora.wondershare.com/video-editing-tips/b-roll-guide.html",
        "related_question": "How to optimize video scripts to automatically match stock footage clips?",
        "relevance": "Software guide reaching millions of entry-level and prosumer video editors worldwide.",
        "pitch_angle": "Suggest educational link addition explaining how to structure talking-head scripts for automated b-roll alignment.",
        "competitor_domain": "capcut.com",
        "gap_type": "authority_publisher",
        "authority_score": 88,
        "anchor_context": "...pacing your script with physical visual cues makes it easier to match stock footage either manually or with AI...",
    },
    {
        "target_domain": "premieregal.com",
        "target_url": "https://premieregal.com/tutorials/faster-editing-workflows",
        "related_question": "How can video creators automate b-roll selection using AI?",
        "relevance": "Premier Premiere Pro and editing workflow tutorial destination with massive creator following.",
        "pitch_angle": "Partner on a workflow guide demonstrating how IncuBrix transcript EDL/XML exports integrate into Premiere Pro.",
        "competitor_domain": "autopod.fm",
        "gap_type": "authority_publisher",
        "authority_score": 78,
        "anchor_context": "...using automated b-roll selection tools that export directly to your NLE timeline drastically speeds up editing...",
    },
    {
        "target_domain": "nofilmschool.com",
        "target_url": "https://nofilmschool.com/how-to-use-b-roll-effectively",
        "related_question": "How to optimize video scripts to automatically match stock footage clips?",
        "relevance": "Leading community portal for independent filmmakers, documentary creators, and video journalists.",
        "pitch_angle": "Guest editorial on maintaining creative narrative intent and ethical licensing when utilizing automated b-roll.",
        "competitor_domain": "artlist.io",
        "gap_type": "authority_publisher",
        "authority_score": 86,
        "anchor_context": "...b-roll must serve the emotional cadence of the script, whether selected manually or assisted by automated tools...",
    },
    {
        "target_domain": "buffer.com",
        "target_url": "https://buffer.com/resources/video-editing-tools/",
        "related_question": "How can video creators automate b-roll selection using AI?",
        "relevance": "Leading social media publishing and creator resource hub with extensive tool roundups.",
        "pitch_angle": "Request inclusion in their annual curated guide to AI productivity tools for solo content creators.",
        "competitor_domain": "kapwing.com",
        "gap_type": "directory_listing",
        "authority_score": 90,
        "anchor_context": "...automated b-roll tools allow solo creators to produce professional looking video without spending hours in timeline editors...",
    },
    {
        "target_domain": "sproutsocial.com",
        "target_url": "https://sproutsocial.com/insights/video-metrics/",
        "related_question": "What is Generative Engine Optimization (GEO) and how does it differ from SEO?",
        "relevance": "Enterprise social media analytics platform covering cross-channel video performance metrics.",
        "pitch_angle": "Cite IncuBrix visibility scoring heuristics for measuring creator brand mentions in generative assistant feeds.",
        "competitor_domain": "brandwatch.com",
        "gap_type": "authority_publisher",
        "authority_score": 91,
        "anchor_context": "...tracking brand sentiment and visibility across generative AI answers has become an essential PR KPI...",
    },
    {
        "target_domain": "hootsuite.com",
        "target_url": "https://blog.hootsuite.com/social-video-trends/",
        "related_question": "What technical SEO factors affect whether Google AI Overviews feature your content?",
        "relevance": "Global social marketing benchmark destination analyzing omnichannel content visibility.",
        "pitch_angle": "Share case study on how multi-platform video creators structure scripts to achieve dual YouTube and AI Overview rankings.",
        "competitor_domain": "meltwater.com",
        "gap_type": "authority_publisher",
        "authority_score": 91,
        "anchor_context": "...creators who optimize video metadata and structured text together capture higher visibility across search and AI engines...",
    },
    {
        "target_domain": "martech.org",
        "target_url": "https://martech.org/tracking-brand-visibility-in-generative-search/",
        "related_question": "How does robots.txt impact AI crawlers like GPTBot, ClaudeBot, and PerplexityBot?",
        "relevance": "Flagship publication covering marketing technology stacks and automated search operations.",
        "pitch_angle": "Thought leadership article on modern robots.txt crawler policies for GPTBot, ClaudeBot, and PerplexityBot.",
        "competitor_domain": "botify.com",
        "gap_type": "authority_publisher",
        "authority_score": 88,
        "anchor_context": "...blocking generative AI crawlers in robots.txt may protect IP but eliminates the opportunity to be cited in generative answers...",
    },
    {
        "target_domain": "searchenginejournal.com",
        "target_url": "https://www.searchenginejournal.com/technical-seo-for-ai-overviews/",
        "related_question": "What technical SEO factors affect whether Google AI Overviews feature your content?",
        "relevance": "Premier daily search marketing publication covering technical SEO and AI algorithm updates.",
        "pitch_angle": "Submit technical guide on JSON-LD entity clarity and first-two-sentences answer extraction for AI Overviews.",
        "competitor_domain": "onely.com",
        "gap_type": "authority_publisher",
        "authority_score": 91,
        "anchor_context": "...pages that earn citations in Google AI Overviews consistently feature concise direct answers under structured H2 headers...",
    },
    {
        "target_domain": "neilpatel.com",
        "target_url": "https://neilpatel.com/blog/seo-for-ai/",
        "related_question": "What is Generative Engine Optimization (GEO) and how does it differ from SEO?",
        "relevance": "High-traffic digital marketing and SEO resource reaching millions of marketing professionals.",
        "pitch_angle": "Suggest resource addition on calculating multi-market AI citation rates alongside traditional rank tracking.",
        "competitor_domain": "ubersuggest.com",
        "gap_type": "authority_publisher",
        "authority_score": 90,
        "anchor_context": "...measuring whether AI engines recommend your product requires tracking both conversational mentions and attributed source links...",
    },
    {
        "target_domain": "pcmag.com",
        "target_url": "https://www.pcmag.com/picks/the-best-video-editing-software",
        "related_question": "How can video creators automate b-roll selection using AI?",
        "relevance": "Consumer and professional software evaluation authority providing recognized product awards.",
        "pitch_angle": "Submit IncuBrix for editorial software testing in the automated video utilities and AI b-roll category.",
        "competitor_domain": "adobe.com",
        "gap_type": "directory_listing",
        "authority_score": 93,
        "anchor_context": "...automated b-roll utilities are becoming a critical companion to traditional NLE software for rapid turnaround video...",
    },
    {
        "target_domain": "g2.com",
        "target_url": "https://www.g2.com/categories/ai-video-generators",
        "related_question": "How can video creators automate b-roll selection using AI?",
        "relevance": "Primary global B2B software review marketplace influencing enterprise software purchasing decisions.",
        "pitch_angle": "Claim and optimize IncuBrix product profile to acquire high-authority citation and user reviews.",
        "competitor_domain": "runwayml.com",
        "gap_type": "directory_listing",
        "authority_score": 92,
        "anchor_context": "...browse top-rated video workflow automation and b-roll generation software reviewed by verified creators...",
    },
    {
        "target_domain": "capterra.com",
        "target_url": "https://www.capterra.com/video-editing-software/",
        "related_question": "How can video creators automate b-roll selection using AI?",
        "relevance": "Major software discovery and vendor comparison platform owned by Gartner.",
        "pitch_angle": "List IncuBrix under video editing and AI workflow tools to secure high-authority co-citation.",
        "competitor_domain": "invideo.io",
        "gap_type": "directory_listing",
        "authority_score": 91,
        "anchor_context": "...compare features, pricing, and user ratings for modern automated video editing and footage curation software...",
    },
    {
        "target_domain": "producthunt.com",
        "target_url": "https://www.producthunt.com/topics/video-editing",
        "related_question": "How can video creators automate b-roll selection using AI?",
        "relevance": "Leading discovery portal for early tech adopters, creators, and AI workflow enthusiasts.",
        "pitch_angle": "Publish launch profile and maker commentary citing IncuBrix's open architecture and benchmark studies.",
        "competitor_domain": "descript.com",
        "gap_type": "community_forum",
        "authority_score": 90,
        "anchor_context": "...discover the newest video editing and timeline automation tools launched by makers this week...",
    },
    {
        "target_domain": "github.com",
        "target_url": "https://github.com/topics/video-automation",
        "related_question": "How to optimize video scripts to automatically match stock footage clips?",
        "relevance": "Global developer hub where software engineers and creators search for video automation pipelines.",
        "pitch_angle": "Maintain public open architecture repository and schema specifications linking to IncuBrix documentation.",
        "competitor_domain": "moviepy.org",
        "gap_type": "community_forum",
        "authority_score": 96,
        "anchor_context": "...curated list of open source video automation engines, transcript alignment tools, and media pipelines...",
    },
    {
        "target_domain": "reddit.com",
        "target_url": "https://www.reddit.com/r/VideoEditing/wiki/resources",
        "related_question": "How can video creators automate b-roll selection using AI?",
        "relevance": "Largest online community of professional, freelance, and amateur video editors (500k+ members).",
        "pitch_angle": "Propose community wiki resource listing under automated workflow utilities and b-roll selection tools.",
        "competitor_domain": "davinciresolve.com",
        "gap_type": "community_forum",
        "authority_score": 92,
        "anchor_context": "...recommended workflow tools for script transcription, b-roll matching, and timeline automation...",
    },
]
