"""Synthetic and realistic HTML/XML/robots fixtures for Technical SEO auditor testing.

DISCLAIMER: TEST DATA ONLY.
These fixtures simulate varied technical states (optimal, defective, malformed)
for unit and regression testing without querying external live servers.
"""

PERFECT_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IncuBrix - AI Visibility Engine for Creators</title>
    <meta name="description" content="Boost your organic creator visibility across Google search and AI answer engines with IncuBrix automated intelligence.">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://incubrix.com/features">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "IncuBrix Features",
        "description": "Comprehensive feature set for AEO and GEO visibility tracking."
    }
    </script>
</head>
<body>
    <header>
        <h1>IncuBrix AI Visibility Engine</h1>
    </header>
    <nav>
        <a href="https://incubrix.com/features">Explore platform features</a>
        <a href="https://incubrix.com/pricing">Transparent subscription pricing</a>
    </nav>
    <main>
        <h2>Real-time AEO Tracking</h2>
        <p>Monitor citation occurrences across generative answer engines.</p>
        <img src="/assets/diagram.webp" alt="IncuBrix architecture diagram illustrating data pipelines" loading="lazy">
        <h2>Citation Gap Discovery</h2>
        <p>Identify missing publisher references compared to competitors.</p>
    </main>
</body>
</html>
"""

NOINDEX_PAGE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Staging Environment - Private Access</title>
    <meta name="robots" content="noindex, nofollow">
</head>
<body>
    <h1>Private Staging</h1>
</body>
</html>
"""

DEFECTIVE_METADATA_HTML = """<!DOCTYPE html>
<html>
<head>
    <!-- Missing title and meta description -->
    <link rel="canonical" href="/relative-path">
    <link rel="canonical" href="/conflicting-path">
</head>
<body>
    <!-- Missing h1 -->
    <h3>Unanchored Subtitle</h3>
</body>
</html>
"""

HEADING_HIERARCHY_DEFECT_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Conflicting Headings Page - IncuBrix Test</title>
    <meta name="description" content="Valid description length for testing heading defects specifically.">
</head>
<body>
    <h1>First Primary Heading</h1>
    <h1>Second Conflicting Primary Heading</h1>
    <h1>Third Duplicate Primary Heading</h1>
</body>
</html>
"""

MALFORMED_SCHEMA_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Malformed Schema and Image Alt Defects</title>
    <meta name="description" content="Testing parser resilience against broken JSON-LD and missing alt text.">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "broken_json_syntax": unquoted_value
    }
    </script>
</head>
<body>
    <h1>Testing Schema Parse Errors</h1>
    <img src="/img1.png">
    <img src="/img2.jpg" alt="">
</body>
</html>
"""

GENERIC_LINKS_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Generic Anchor Texts and Placeholder Links</title>
    <meta name="description" content="Testing detection of non-descriptive anchor texts and placeholder links.">
</head>
<body>
    <h1>Internal Links Test</h1>
    <a href="#">Click here</a>
    <a href="javascript:void(0)">Read more</a>
    <a href="">Learn more</a>
    <a href="https://incubrix.com/docs">Documentation index</a>
</body>
</html>
"""

SAMPLE_ROBOTS_TXT_HEALTHY = """User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

Sitemap: https://incubrix.com/sitemap.xml
"""

SAMPLE_ROBOTS_TXT_DISALLOWED = """User-agent: *
Disallow: /

User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /
"""

SAMPLE_SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://incubrix.com/features</loc>
        <lastmod>2026-10-22</lastmod>
    </url>
    <url>
        <loc>https://incubrix.com/pricing</loc>
        <lastmod>2026-10-22</lastmod>
    </url>
</urlset>
"""

SAMPLE_INVALID_SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://incubrix.com/broken
    <!-- Unclosed tags causing XML parse failure -->
"""

SAMPLE_LLMS_TXT = """# IncuBrix Documentation

> Optional manifest for LLM consumption and knowledge retrieval.

## Overview
IncuBrix tracks brand presence across Google SERP and generative AI engines.

## Key Links
- [API Reference](https://incubrix.com/docs)
- [Architecture](https://incubrix.com/architecture)
"""
