# IncuBrix AEO, SEO & GEO Visibility Engine

The **IncuBrix Visibility Engine** is a production-minded, modular platform designed to evaluate and optimize brand visibility across traditional search engines (Google, Bing) and Answer/Generative AI engines (Google AI Overview, ChatGPT, Claude, Perplexity, Copilot).

---

## 🛠️ Technology Stack

- **Python**: 3.12+ (tested on Python 3.13)
- **Framework**: FastAPI
- **Validation**: Pydantic v2
- **ORM / Database**: SQLAlchemy 2.0+ with SQLite (local development)
- **HTTP Client**: HTTPX
- **Environment**: python-dotenv
- **Testing**: pytest
- **Interactive Dashboard**: Streamlit

---

## 📁 Modular Architecture

The codebase separates concerns across dedicated, isolated modules:

```
visibility-engine/
├── .env.example                     # Safe environment variable template
├── .gitignore                       # Git ignore rules for caches, venv, data
├── README.md                        # Setup and operational documentation
├── requirements.txt                 # Pinned project dependencies
├── app/
│   ├── main.py                      # FastAPI app entrypoint, exception handlers & lifespan
│   ├── config.py                    # Environment settings container
│   ├── logging_config.py            # Structured logging setup
│   ├── exceptions.py                # Domain exception hierarchy
│   ├── api/
│   │   ├── dependencies.py          # FastAPI DB session & repository dependencies
│   │   └── v1/
│   │       ├── router.py            # Aggregated v1 API router
│   │       ├── questions.py         # Creator question endpoints
│   │       ├── observations.py      # Visibility observation & summary endpoints
│   │       ├── geo.py               # Generative Engine Optimization (GEO) assistant endpoints
│   │       ├── evidence.py          # Source evidence artifact endpoints
│   │       ├── audit.py             # Technical audit finding endpoints
│   │       ├── content.py           # Content brief & generated page endpoints
│   │       ├── citation.py          # Citation target matrix endpoints
│   │       ├── reports.py           # Report generation & CSV export endpoints
│   │       └── pipeline.py          # Pipeline execution telemetry endpoints
│   ├── schemas/                     # Shared Pydantic v2 validation models
│   │   ├── common.py                # Enums (MentionStatus, CitationStatus, ProviderType, etc.)
│   │   ├── questions.py             # Creator questions schemas
│   │   ├── evidence.py              # Source evidence & SHA-256 schemas
│   │   ├── observations.py          # Search & AI observation schemas
│   │   ├── audit.py                 # Technical audit findings schemas
│   │   ├── content.py               # Content brief & generated page schemas
│   │   ├── citation.py              # Citation opportunity & target schemas
│   │   ├── reports.py               # Weekly report & provenance breakdown schemas
│   │   └── pipeline.py              # Pipeline run tracking schemas
│   ├── database/                    # Persistence layer
│   │   ├── session.py               # Engine, sessionmaker, init_db, get_db
│   │   ├── base.py                  # DeclarativeBase and CommonMixin (id, timestamps)
│   │   ├── init_db.py               # Database initialization and seed script
│   │   ├── models/                  # SQLAlchemy 2.0 ORM models
│   │   └── repositories/            # Repository layer isolating DB queries from route handlers
│   ├── engine/                      # Core scoring and query normalizer
│   │   ├── scoring.py               # Transparent visibility heuristic scoring
│   │   ├── visibility_metrics.py    # Multi-market/provider scoring & period comparison analytics
│   │   ├── report_generator.py      # CSV export engine & weekly report synthesis
│   │   ├── normalizer.py            # Query and domain normalization
│   │   ├── mention_analyzer.py      # Brand mentions, citations, and competitor gap analyzer
│   │   └── question_ingestion.py    # CSV import/export, URL validation, and intent categorization
│   ├── collectors/                  # Observation collectors
│   │   ├── base.py                  # BaseCollector abstract class
│   │   ├── manual_collector.py      # Manual operator submission collector
│   │   ├── geo_collector.py         # Generative Engine Optimization (GEO) collector
│   │   └── automated_collector.py   # Automated provider query and evidence ingestion pipeline
│   ├── providers/                   # Search & AI assistant provider clients
│   │   ├── base.py                  # BaseProvider & BaseAIProvider contracts and ProviderResult
│   │   ├── search_provider.py       # Google SERP provider client (organic rank, snippet, answer box)
│   │   └── ai_provider.py           # Perplexity, OpenAI, Gemini, Claude & Google AI Overview adapters
│   ├── audit/                       # Technical SEO/AEO audit evaluations (robots.txt, llms.txt, Schema.org)
│   ├── content/                     # AEO content brief generator & page generator
│   ├── frontend/                    # Streamlit interactive dashboard (app/frontend/app.py)
│   └── pipeline/                    # Pipeline orchestration, bounded retries, cost tracking & CLI
│       ├── orchestrator.py          # Unified six-stage pipeline orchestrator
│       ├── cli.py                   # Complete & refresh CLI command runner
│       ├── cost_tracker.py          # Provider rate cards & API expenditure tracking
│       └── retry.py                 # Bounded retry with error discrimination
├── data/                            # Local SQLite storage and test fixtures
│   ├── synthetic_fixtures.json      # Labeled TEST DATA fixtures
│   └── live_review_sample.csv       # Small new input set for live review
├── evidence/                        # File-based evidence artifact storage
├── outputs/                         # Generated reports, pages, and exports
│   └── reports/                     # Persisted executive intelligence reports (.md, .json)
├── docs/                            # In-depth architectural documentation
│   ├── ARCHITECTURE.md              # Domain models and entity-relationship guide
│   └── providers.md                 # Provider requirements, rate limits, and manual evidence guide
└── tests/                           # Pytest test suite
    ├── conftest.py                  # In-memory SQLite fixtures & TestClient overrides
    ├── fixtures/                    # Labeled synthetic test data fixtures
    ├── test_schemas.py              # Schema validation & missing data handling tests
    ├── test_repositories.py         # DB operations & duplicate prevention tests
    ├── test_scoring.py              # Scoring heuristic tests
    ├── test_mention_analyzer.py     # Brand mention & citation analyzer tests
    ├── test_providers.py            # Search & AI provider adapter resilience tests
    ├── test_collector.py            # Automated collector pipeline & harvest API tests
    ├── test_manual_collector.py     # Manual evidence import adapter & API tests
    ├── test_geo_collector.py        # Generative Engine Optimization (GEO) tests
    ├── test_question_ingestion.py   # CSV import/export & intent categorization tests
    ├── test_technical_audit.py      # Technical SEO/AEO auditor tests
    ├── test_content_engine.py       # Content & citation engine tests
    ├── test_report_generator.py     # CSV exports, provenance classification & report tests
    ├── test_pipeline_orchestration.py # Pipeline integration, retries, idempotency & CLI tests
    └── test_api.py                  # FastAPI endpoint integration tests
```

---

## 🪟 Windows PowerShell Setup Guide

Follow these steps in **Windows PowerShell**:

### 1. Prerequisites Check
Ensure Python 3.12 or newer is installed:
```powershell
python --version
```

### 2. Create and Activate Virtual Environment
```powershell
cd e:\Incubrix\visibility-engine
python -m venv .venv
```

Activate the virtual environment:
```powershell
.\.venv\Scripts\Activate.ps1
```

> [!NOTE]
> If PowerShell blocks script execution with `PSSecurityException`, bypass the policy for the current process:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\.venv\Scripts\Activate.ps1
> ```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the safe `.env.example` template:
```powershell
Copy-Item .env.example .env
```
Default values point to a local SQLite database at `./data/visibility.db`.

---

## 💾 Database Initialization & Seeding

### Initialize Database Schema
Create the tables and directory structures:
```powershell
python -m app.database.init_db
```

### Initialize and Seed Synthetic Test Records
To populate the database with labeled synthetic test records for immediate exploration:
```powershell
python -m app.database.init_db --seed
```
*(All seeded records are labeled as synthetic test data; none represent real search engine evidence).*

---

## 🚀 Running the API Server

Start the FastAPI application with Uvicorn:
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Once running, access:
- **API Documentation (Swagger UI)**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8001/redoc](http://127.0.0.1:8001/redoc)
- **Health Check Endpoint**: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)
- **Engine Overview**: [http://127.0.0.1:8001/](http://127.0.0.1:8001/)

### Triggering an Automated Observation Harvest
Harvest live or test observations for any creator question via the API:
```powershell
# Query Google Search SERP for question
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/observations/harvest/{question_id}?provider_type=google_search&market=US"

# Query Generative AI Assistant (e.g. Perplexity / Sonar)
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/observations/harvest/{question_id}?provider_type=perplexity&market=US"
```

### Module 2: Question Ingestion & Curation

Ingest creator questions from CSV files or inline text, preserve source provenance, curate manual review statuses, and export questions:

```powershell
# Ingest questions from inline CSV text
$body = @{
    csv_content = @"
text,target_market,source_url,source_platform,tags
"How do creators automate b-roll selection?","US","https://reddit.com/r/videocreators/comments/123","Reddit","b-roll;automation"
"Best tools to sync audio and video automatically?","US","https://youtube.com/watch?v=999","YouTube","editing;audio"
"@
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/questions/import-text" -Body $body -ContentType "application/json"

# Ingest questions via multipart CSV file upload
$form = @{
    file = Get-Item -Path ".\sample_questions.csv"
}
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/questions/import-csv" -Form $form

# Curate manual review status (pending, approved, rejected, flagged)
$review = @{
    review_status = "approved"
    notes = "Verified high demand query in creator community."
} | ConvertTo-Json

Invoke-RestMethod -Method Patch -Uri "http://127.0.0.1:8001/v1/questions/{question_id}/review" -Body $review -ContentType "application/json"

# Export filtered questions to CSV
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/questions/export.csv?market=US&review_status=approved" -OutFile "approved_questions.csv"

# Import manual visibility evidence (Module 3)
$evidencePayload = @{
    question_id = "your-question-id-here"
    raw_evidence = "IncuBrix ranks #1 in organic search. Competitor Runway is mentioned."
    provider = "google_search"
    observation_type = "search_engine"
    rank_position = 1
    observed_features = @("answer_box", "organic_results")
    quoted_source_urls = @("https://incubrix.com/overview")
    operator_id = "analyst_1"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/observations/manual-import" -Body $evidencePayload -ContentType "application/json"

# Import manual AI assistant transcript for GEO (Module 4)
$geoPayload = @{
    question_id = "your-question-id-here"
    assistant = "chatgpt"
    raw_response = "IncuBrix automatically matches video transcripts to b-roll clips. InVideo is an alternative."
    ai_model_version = "GPT-4o"
    citation_urls = @("https://incubrix.com/overview")
    operator_id = "geo_analyst"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/geo/manual-import" -Body $geoPayload -ContentType "application/json"

# List supported AI assistant engines and live configuration status
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/geo/assistants"

# Generate comprehensive SEO, AEO & GEO Visibility Metrics Report (Module 5)
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/scoring/report?market=US&deduplicate=true"

# Compare visibility metrics across two distinct date ranges (Module 5)
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/scoring/compare?period_a_start=2026-10-01T00:00:00&period_a_end=2026-10-15T23:59:59&period_b_start=2026-10-16T00:00:00&period_b_end=2026-10-31T23:59:59&period_a_label=Week1&period_b_label=Week2"

# Breakdown visibility metrics by dimension (market, provider, or question) (Module 5)
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/scoring/breakdown?group_by=market"

### Module 6: Technical SEO, AEO & GEO Auditor

Inspect accessible public pages for indexability signals, metadata bounds, headings structure, canonical links, robots.txt, sitemaps, internal links, performance signals, and Schema.org structured data. Treats `/llms.txt` as an optional discovery check, not a guaranteed ranking requirement.

```powershell
# Run a comprehensive technical audit on a page (offline HTML payload or live check)
$auditRequest = @{
    target_url = "https://incubrix.com/features"
    html_content = @"
<!DOCTYPE html>
<html>
<head>
    <title>IncuBrix - AI Visibility Engine for Creators</title>
    <meta name="description" content="Boost your organic creator visibility across Google search and AI answer engines.">
    <link rel="canonical" href="https://incubrix.com/features">
    <script type="application/ld+json">
    {"@context": "https://schema.org", "@type": "WebPage", "name": "Features"}
    </script>
</head>
<body>
    <h1>IncuBrix Features</h1>
    <h2>AEO Tracking</h2>
    <a href="https://incubrix.com/pricing">Explore platform pricing plans</a>
</body>
</html>
"@
    status_code = 200
    store_findings = $true
} | ConvertTo-Json

$report = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/audit/run" -Body $auditRequest -ContentType "application/json"
$report | Format-List target_url, health_score, total_findings, passed_count, failed_count

# Recheck and validate a remediation for an audit finding (strictly executes targeted re-inspection)
$validationPayload = @{
    updated_html = "<html><head><title>Fixed Page Title Within 30 to 60 Chars</title></head></html>"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/audit/validate/{finding_id}" -Body $validationPayload -ContentType "application/json"

# List audit findings with optional category, severity, status, and validation filters
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/audit/findings?url=https://incubrix.com/features&status=fail"

# Retrieve high-level audit summary statistics
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/audit/summary?url=https://incubrix.com/features"

### Module 7: Content and Citation Engine

Generate publish-ready, AEO-optimized page drafts from approved creator questions, verified IncuBrix product information, and sourced research. Delivers direct answers in the first two sentences, structured heading outlines, title/meta description length bounds, internal link suggestions, verified citations, and valid Schema.org JSON-LD. Researches and stores 30 specific real third-party citation opportunities. Labels all drafts as `unreviewed` until human curation.

```powershell
# 1. Seed the 30 specific real third-party citation opportunities catalog
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/citations/seed-catalog"

# 2. Query citation opportunities by target domain or gap type
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/citations/targets?domain=searchengineland.com"

# 3. Batch generate 10 publish-ready page drafts from approved creator questions
$batchPayload = @{
    use_llm = $false
    limit = 10
} | ConvertTo-Json

$batchResult = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/content/generate-batch" -Body $batchPayload -ContentType "application/json"
$batchResult | Format-List total_generated

# 4. Fetch a generated page draft by its URL slug
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/content/pages/how-to-automate-b-roll-selection-using-ai"

# 5. Run content quality and AEO direct-answer validation on a page draft
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/content/validate/{page_id}"

# 6. Human review workflow: transition draft status from 'unreviewed' to 'approved'
$reviewPayload = @{
    publication_status = "approved"
    reviewer_notes = "Senior editor verified factual accuracy, source citations, and schema markup."
} | ConvertTo-Json

Invoke-RestMethod -Method Patch -Uri "http://127.0.0.1:8001/v1/content/pages/{page_id}/review" -Body $reviewPayload -ContentType "application/json"

# 7. List unreviewed drafts awaiting human verification
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/content/pages?status=unreviewed"
```

---

### Module 8: Streamlit Dashboard and Report Generator

Run the interactive dashboard and generate enterprise exports and intelligence briefs based strictly on stored records:

```powershell
# 1. Launch the FastAPI backend server
uvicorn app.main:app --reload

# 2. In a separate terminal, launch the Streamlit Dashboard
streamlit run app/frontend/app.py

# 3. Export visibility observations as RFC 4180 CSV with explicit empirical provenance classification
# Supports filters: ?market=US&provider=google_search&start_date=2026-10-01T00:00:00
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/reports/export/visibility.csv" -OutFile "outputs/visibility.csv"

# 4. Export technical audit findings and code patches as RFC 4180 CSV
# Supports filters: ?status=fail&url=https://incubrix.com/blog
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/reports/export/technical_fixes.csv" -OutFile "outputs/technical_fixes.csv"

# 5. Export 30-target citation opportunities with relevance and pitch angles as RFC 4180 CSV
# Supports filters: ?domain=searchengineland.com&gap_type=authority_publisher
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/reports/export/citation_targets.csv" -OutFile "outputs/citation_targets.csv"

# 6. Synthesize executive weekly visibility report (persisted to outputs/reports/ in .md and .json)
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/reports/weekly?save_to_disk=true"
```

---

### Module 9: Pipeline Orchestration

Run the complete pipeline end-to-end or trigger a measurement refresh via the unified CLI runner or REST API:

```powershell
# 1. Complete end-to-end run with small new input set for live review
python -m app.pipeline.cli complete --sample-input

# 2. Complete run with user-provided CSV input file
python -m app.pipeline.cli complete --input-file "data/my_questions.csv" --market "US"

# 3. Refresh run (re-measures existing approved questions, updates scores and reports, skips content generation)
python -m app.pipeline.cli refresh --market "US"

# 4. Filter complete run to specific provider with bounded retries and fast content limit
python -m app.pipeline.cli complete --provider "google_search" --content-limit 5 --max-retries 2

# 5. Trigger complete pipeline run via REST API
$runPayload = @{
    mode = "complete"
    market = "US"
    sample_input = $true
    max_retries = 2
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/pipeline/run" -Body $runPayload -ContentType "application/json"

# 6. Trigger measurement refresh via REST API
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/v1/pipeline/refresh?market=US"

# 7. Inspect published API unit cost benchmarks
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8001/v1/pipeline/cost-rates"
```

---

## 🧪 Running the Test Suite

Execute the complete pytest suite:
```powershell
pytest -v
```

All 142 tests run against an isolated in-memory SQLite database, verifying:
- **Module 9 — Pipeline Orchestration**: Six-stage pipeline integration (Ingestion, Collection, Scoring, Technical Audit, Content Drafts, Reports & Exports); dual execution modes (`complete` vs `refresh`); CLI command execution and exit code contracts (0 on success/partial, 1 on required stage failure); bounded retry utility with error discrimination; provider failure recovery without premature job termination; daily deterministic fingerprint idempotency; API cost tracking telemetry with published rate cards; live review sample input set (`data/live_review_sample.csv`); and REST API endpoints.
- **Module 8 — Streamlit Dashboard and Report Generator**: Comprehensive RFC 4180 CSV exports for `visibility.csv`, `technical_fixes.csv`, and `citation_targets.csv`; provenance mode categorization distinguishing `real`, `manual`, `mocked`, and `unavailable` records without conflation; executive weekly intelligence report synthesis in Markdown and structured JSON with persistence to `outputs/reports/`; empty-state resilience across all exporters and tabs; interactive Streamlit UI with 7 dedicated tabs (Overview & KPIs, Period Comparisons, Evidence Inspector, Technical Audit, Content Drafts, Citation Opportunities, Reports & Exports); and REST API endpoints.
- **Module 7 — Content and Citation Engine**: Batch generation of 10 publish-ready AEO/GEO page drafts from approved creator questions; direct answer placement within the first two sentences without fluff; structured heading hierarchy (1 H1 and multiple H2s); title and meta description length constraints; internal link suggestions with descriptive anchor text; real third-party research citations without invented sources; valid Schema.org JSON-LD (`TechArticle`, `HowTo`, `FAQPage`); seeding and persistence of 30 specific real third-party citation opportunities with authority scores, URLs, relevance, and outreach pitch angles; configurable LLM integration with deterministic template fallback; content validation reporting via `ContentValidator`; initial draft labeling as `unreviewed`; and human review curation workflow (`/v1/content/pages/{id}/review`).
- **Module 6 — Technical SEO Auditor**: DOM and metadata inspection via `HTMLPageInspector`; evaluation of indexability signals (meta robots `noindex`/`nofollow`, HTTP status codes, `X-Robots-Tag`); title and meta description presence and optimal length bounds; heading hierarchy (single `<h1>` enforcement, `<h2>` subheadings); canonical links (presence, duplicates, relative path warnings); robots.txt (search crawler blanket disallow, AI bot permissions `GPTBot`/`ClaudeBot`/`PerplexityBot`, sitemap directives); XML sitemap inspection (XML validation, target URL containment); internal links (placeholder `#` or `javascript:` links, non-descriptive anchor texts); performance signals (latency threshold bands, HTML payload size, render-blocking scripts, image alt accessibility); Schema.org JSON-LD (parsing, syntax error handling, entity verification); optional `/llms.txt` discovery checks (strictly low/info severity, non-ranking requirement messaging); composite health scoring (0-100 weighted penalties); and strict fix validation workflows (`validate_fix`) that never claim a fix is validated without executing an appropriate check, marking unavailable checks explicitly.
- **Module 5 — Visibility Scoring & Analytics**: Calculation of documented SEO (Top-10 rate, Top-3 rate, average rank position), AEO (answer-feature presence rate, answer box rate), and GEO metrics (AI mention rate, AI citation rate, observed competitor lists); strict exclusion of failed, unavailable, and unknown observations from valid denominators with separate telemetry reporting; zero denominator resilience without division-by-zero crashes; missing value nullability; repeated record daily fingerprint deduplication; multi-period comparative deltas (`/v1/scoring/compare`); cohort breakdowns by market, provider, and question (`/v1/scoring/breakdown`); and dynamic report generation (`/v1/scoring/report`).
- **Module 4 — GEO Collector**: Shared `BaseAIProvider` interface with independent adapters for Perplexity AI, OpenAI/ChatGPT, Google Gemini Search Grounding, Anthropic Claude, and Google AI Overview; strict refusal to claim unsupported assistants were queried; decoupled brand mention vs direct website citation extraction without conflation; manual GEO evidence import for web UI assistants (ChatGPT, Claude, Copilot); mock test coverage, rate limits, timeouts, and missing evidence handling.
- **Module 3 — SEO & AEO Collection**: Permitted search API adapter (Google SERP) and AEO assistant adapter (Perplexity/generative AI) executed strictly when configured; unconfigured state gracefully returns `UNAVAILABLE` without simulating live results; comprehensive timeout handling (`httpx.TimeoutException`), rate-limit handling (HTTP 429), and authentication error handling (HTTP 401/403); full Manual Evidence-Import adapter capturing question associations, ranking position, answer features, quoted source URLs, raw evidence artifacts, and collection status; SHA-256 evidence deduplication and daily deterministic fingerprinting; complete documentation in `docs/providers.md`.
- **Module 2 — Question Ingestion**: CSV batch import with RFC 4180 parsing, row-level validation and error reporting, duplicate question prevention (in-batch and DB), URL validation, intent auto-classification (`informational`, `commercial`, `transactional`, `comparison`, `navigational`), manual review workflow (`pending`, `approved`, `rejected`, `flagged`), source provenance preservation, and CSV export.
- **Provider Adapters**: Real HTTP adapters for Google SERP and AI assistant providers, checking timeout resilience, rate limits (HTTP 429), authentication failures (HTTP 401), and unconfigured state handling without fabricating data.
- **Mention & Citation Analyzer**: Word-boundary brand detection, canonical domain verification, competitor discovery, and citation gap identification.
- **Automated Collector**: End-to-end question ingestion, raw evidence SHA-256 provenance storage, heuristic scoring, and daily deterministic fingerprint deduplication.
- **Schema Validation**: Correct field definitions, string lengths, ranges, and types.
- **Missing Data Handling**: Nullable fields remain `None` and are never coerced to `False`. Explicit unknown/unavailable states.
- **Duplicate Prevention**: Rejection of duplicate questions, duplicate observation fingerprints, duplicate evidence hashes, and duplicate page slugs.
- **Repository Operations**: Full CRUD across questions, observations, evidence, audit findings, content briefs, and pipeline runs.
- **Scoring Heuristics**: Transparent points for rank, featured snippet, mention, and citation.
- **API Endpoints**: Request handling, validation errors (422), conflict errors (409), and not found errors (404).

---

## 💡 Key Architectural Principles

### 1. Explicit Unknown States (No False Negatives)
In AEO/GEO measurement, if an AI engine does not return source links or if evidence cannot be retrieved, it must **never** be treated as a negative result (e.g. `False` or "not cited").
Observations enforce explicit tri-state enums:
```python
class MentionStatus(str, Enum):
    MENTIONED = "mentioned"
    NOT_MENTIONED = "not_mentioned"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"

class CitationStatus(str, Enum):
    CITED = "cited"
    NOT_CITED = "not_cited"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
```
The summary analytics endpoint (`/v1/summary`) calculates confirmed positive rates while isolating unknown/unavailable records.

### 2. Duplicate Prevention
- **Observations**: Deduplicated using a SHA-256 fingerprint generated from `(question_id, provider, market, location, date)`.
- **Evidence Artifacts**: Deduplicated by computing the SHA-256 hash of the payload content.
- **Questions**: Unique constraint on normalized question text.
- **Content Pages**: Unique constraint on the URL `slug`.

### 3. Decoupled Repository Pattern
Route handlers in `app/api/v1/` never execute raw queries or interact directly with the SQLAlchemy session. All data access flows through dedicated repositories injected via FastAPI `Depends()`.

---

## 🐳 Docker Container Deployment

The project includes a standalone container configuration and Docker Compose setup for running the backend and dashboard in an isolated environment.

### 1. Quickstart with Docker Compose (Recommended)
```powershell
# Build and start both FastAPI backend (:8001) and Streamlit dashboard (:8501)
docker compose up --build -d

# Check running status
docker compose ps

# View live logs
docker compose logs -f

# Stop containers
docker compose down
```

On Windows, you can also launch directly via:
```powershell
.\start_docker.ps1
```

### 2. Standalone Single-Container
```powershell
# Build the multi-purpose container image
docker build -t incubrix-visibility-engine .

# Run with both API and Dashboard in one container
docker run -d `
  --name incubrix-visibility `
  -p 8001:8001 `
  -p 8501:8501 `
  -v "${PWD}/data:/app/data" `
  -v "${PWD}/evidence:/app/evidence" `
  -v "${PWD}/outputs:/app/outputs" `
  incubrix-visibility-engine
```

For complete container architecture, healthchecks, and CLI execution inside Docker, refer to [`docs/docker_guide.md`](file:///e:/Incubrix/visibility-engine/docs/docker_guide.md).

---

## 🔧 Windows PowerShell Troubleshooting

1. **`Activate.ps1 cannot be loaded because running scripts is disabled`**:
   Run:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

2. **`database is locked` in SQLite**:
   SQLite is configured with `check_same_thread=False` and a `StaticPool` during tests. If a lock occurs in development, ensure no dangling background uvicorn processes are accessing `data/visibility.db`:
   ```powershell
   Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
   ```

3. **Re-creating the local database from scratch**:
   ```powershell
   Remove-Item -Force -Path "data\visibility.db" -ErrorAction SilentlyContinue
   python -m app.database.init_db --seed
   ```

---

## 📦 Deliverables & Submission Index

All required assessment submission assets and documentation are organized as follows:

| Deliverable | Location | Description |
| :--- | :--- | :--- |
| **Assessment Workbook** | [`docs/assessment_workbook.md`](file:///e:/Incubrix/visibility-engine/docs/assessment_workbook.md) | Full requirements traceability matrix and self-check references across Modules 1–9. |
| **90-Day Launch Kit** | [`docs/90_day_launch_kit.md`](file:///e:/Incubrix/visibility-engine/docs/90_day_launch_kit.md) | Phased operational roadmap, metric milestones, RACI matrix, and weekly runbook. |
| **Demonstration Videos** | [`docs/demonstration_videos.md`](file:///e:/Incubrix/visibility-engine/docs/demonstration_videos.md) | Full script outlines, screen sequences, test walkthroughs, and candidate submission link placeholders. |
| **Visibility Observations CSV** | [`outputs/visibility.csv`](file:///e:/Incubrix/visibility-engine/outputs/visibility.csv) | Exported observation records categorized by explicit provenance mode (`real`, `manual`, `mocked`, `unavailable`). |
| **20 Prioritized Technical Fixes** | [`outputs/20_prioritized_technical_fixes.md`](file:///e:/Incubrix/visibility-engine/outputs/20_prioritized_technical_fixes.md) | Curated 20 code patches and recommendations with strict validation evidence. |
| **Technical Fixes CSV** | [`outputs/technical_fixes.csv`](file:///e:/Incubrix/visibility-engine/outputs/technical_fixes.csv) | Machine-readable export of technical audit findings, patches, and validation statuses. |
| **10 Publish-Ready AEO Pages** | [`outputs/content_pages/`](file:///e:/Incubrix/visibility-engine/outputs/content_pages/) | 10 Markdown page drafts featuring 2-sentence direct answers, structured data, and real citations. |
| **30 Real Citation Targets** | [`outputs/citation_targets.csv`](file:///e:/Incubrix/visibility-engine/outputs/citation_targets.csv) | 30 verified third-party outreach opportunities with domain authority scores and editorial angles. |
| **Raw Evidence & Responses** | [`evidence/raw_responses/`](file:///e:/Incubrix/visibility-engine/evidence/raw_responses/) | Preserved JSON/text raw assistant payloads, SERP snippets, and screenshot capture guidelines. |
| **Weekly Intelligence Reports** | [`outputs/reports/`](file:///e:/Incubrix/visibility-engine/outputs/reports/) | Synthesized executive intelligence markdown and JSON reports generated by the engine. |

