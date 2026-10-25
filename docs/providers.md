# Provider Specifications & Requirements

This document outlines the architecture, configuration requirements, error handling contracts, and evidence collection workflows for Search Engine (SEO), Answer Engine (AEO), and Manual Evidence adapters within the **IncuBrix Visibility Engine**.

---

## 1. Core Operating Principles

1. **No Simulated or Fabricated Results**: External search and AI providers are **only executed when explicitly configured** with valid API credentials. When unconfigured, providers return `CollectionStatus.UNAVAILABLE` with error code `PROVIDER_NOT_CONFIGURED`. Fake results are never fabricated.
2. **Explicit Nullability & Tri-State Logic**: Missing evidence or unobserved elements are represented explicitly as `None` or `unknown`/`unavailable`. Missing data is never coerced to negative visibility or False.
3. **Full Provenance Preservation**: Every observation persists its raw evidence payload as a SHA-256 deduplicated `EvidenceArtifactModel`, recording exact timestamps, source URLs, platforms, and operator/collector identities.

---

## 2. Permitted Search API Provider (SEO)

### Overview
Connects to external Google SERP APIs (defaulting to Serper.dev or compatible SERP endpoints) to monitor creator question presence in organic rankings, answer boxes, and knowledge panels.

### Configuration Requirements
Set the following environment variables in `.env`:
```ini
SEARCH_PROVIDER_API_KEY=your_search_api_key_here
SEARCH_PROVIDER_API_URL=https://google.serper.dev/search
HTTP_REQUEST_TIMEOUT_SECONDS=10.0
```

### Request Contract
- **Method**: `POST`
- **Headers**:
  - `X-API-KEY`: `<SEARCH_PROVIDER_API_KEY>`
  - `Content-Type`: `application/json`
- **JSON Payload**:
  ```json
  {
    "q": "How do creators use AI to edit podcast b-roll footage?",
    "gl": "us",
    "location": "Austin, TX"
  }
  ```

### Extracted Metrics & Observed Answer Features
- `rank_position`: Organic ranking position (1-100) where an IncuBrix domain is detected, or 1 if cited in the answer box.
- `answer_box_present`: `True` if `answerBox` or featured snippet was present in the SERP.
- `observed_features`: List of SERP components observed (`answer_box`, `featured_snippet`, `organic_results`, `knowledge_graph`, `people_also_ask`).
- `quoted_urls`: List of exact full source URLs from the answer box link and organic result entries.
- `quoted_domains`: Normalized domains extracted from `quoted_urls`.
- `raw_payload`: Full raw JSON response stored in `EvidenceArtifactModel`.

### Error Handling & Rate Limits
- **HTTP 429**: Mapped to `CollectionStatus.FAILED` with `error_code="RATE_LIMITED"`.
- **HTTP 401 / 403**: Mapped to `CollectionStatus.FAILED` with `error_code="AUTHENTICATION_FAILED"`.
- **Timeout (`httpx.TimeoutException`)**: Mapped to `CollectionStatus.FAILED` with `error_code="TIMEOUT"`.
- **Malformed Response**: Mapped to `CollectionStatus.FAILED` with `error_code="INVALID_RESPONSE_JSON"`.

---

## 3. Permitted Answer Engine & GEO Providers (AEO & GEO)

### Overview
Connects to permitted Answer Engine & Generative Engine platforms (Perplexity AI Sonar, OpenAI ChatGPT, Google Gemini Grounding, Anthropic Claude, and Google AI Overview) to monitor generative brand citations and authority references.

### Configuration Settings
```ini
# Perplexity AI
PERPLEXITY_API_KEY=your_perplexity_key_here
PERPLEXITY_API_URL=https://api.perplexity.ai/chat/completions
PERPLEXITY_MODEL=sonar

# OpenAI / ChatGPT
OPENAI_API_KEY=your_openai_key_here
OPENAI_API_URL=https://api.openai.com/v1/chat/completions
OPENAI_MODEL=gpt-4o

# Google Gemini (Search Grounding)
GEMINI_API_KEY=your_gemini_key_here
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent
GEMINI_MODEL=gemini-1.5-pro

# Anthropic Claude
CLAUDE_API_KEY=your_claude_key_here
CLAUDE_API_URL=https://api.anthropic.com/v1/messages
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Google AI Overview
SERP_API_KEY=your_serp_key_here
SERP_API_URL=https://google.serper.dev/search
```

### Supported Independent Adapters
1. **PerplexityAIAdapter**: Direct citation extraction from Perplexity's citation array.
2. **OpenAIAdapter**: Generative synthesis with mention evaluation on message text.
3. **GeminiAIAdapter**: Extracts grounding URLs from `groundingMetadata.groundingChunks[].web.uri`.
4. **ClaudeAIAdapter**: Evaluates text synthesis for brand mentions and competitor comparisons.
5. **GoogleAIOverviewAdapter**: Hybrid overview extraction with link tracking.
6. **UnsupportedAIAdapter**: Safe fallback for unconfigured assistants (e.g. Bing Copilot web), ensuring the system never claims unsupported assistants were queried.

### Decoupled Mention vs. Citation Policy
The engine enforces complete decoupling between mentions and direct citations:
- **Brand Mention (`incubrix_mentioned`)**: Set to `MENTIONED` if "IncuBrix" is named in the response text; `NOT_MENTIONED` if absent.
- **Direct Citation (`incubrix_cited`)**: Set to `CITED` only if `incubrix.com` is linked in citations; `NOT_CITED` if links exist without our domain; `UNAVAILABLE` if the model produced no links.
- **Never Conflated**: An assistant mentioning IncuBrix in text without citing our website is accurately recorded as `MENTIONED` and `NOT_CITED` or `UNAVAILABLE`.

---

## 4. Manual Evidence-Import Adapter (SEO & GEO)

### Overview
Provides human operators and researchers with a formal ingestion pipeline for manual search observations, browser screenshots, HTML snapshots, and generative assistant sessions (e.g. ChatGPT web UI, Claude chat, Copilot web) without requiring paid API keys.

### Endpoints
- `POST /api/v1/observations/manual-import`: General manual evidence import.
- `POST /api/v1/geo/manual-import`: Specialized GEO assistant transcript import (`GEOManualImportRequest`).


### Capabilities & Processing Steps
1. **Validation**: Verifies associated `question_id` exists in the database and validates all `quoted_source_urls` for proper HTTP/HTTPS structure.
2. **Artifact Typing**: Automatically inspects `raw_evidence`:
   - JSON structure (`{...}` or `[...]`) -> `ArtifactType.JSON_PAYLOAD`.
   - HTML markup (`<html`, `<body`, `<div>`) -> `ArtifactType.HTML_SNAPSHOT`.
   - Text -> `ArtifactType.RAW_TEXT`.
3. **Evidence SHA-256 Deduplication**: Hashes raw evidence and reuses existing artifact records if identical text is uploaded.
4. **Mention & Citation Extraction**: Runs `MentionAnalyzer` on text and links to detect brand mentions and competitor domains, while honoring explicit operator overrides if supplied.
5. **Observation Scoring & Fingerprinting**: Computes 0-100 visibility score and assigns daily deterministic fingerprint (`question_id:provider:market:location:YYYY-MM-DD`).

### API Endpoint: `POST /api/v1/observations/manual-import`

#### Request Payload (`ManualEvidenceImportRequest`)
```json
{
  "question_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "raw_evidence": "IncuBrix automatically parses video transcripts to assemble b-roll clips. Runway and Descript offer manual timeline editing.",
  "provider": "google_search",
  "observation_type": "search_engine",
  "market": "US",
  "location": "Austin, TX",
  "rank_position": 1,
  "observed_features": ["answer_box", "featured_snippet", "organic_results"],
  "quoted_source_urls": [
    "https://incubrix.com/features",
    "https://runwayml.com"
  ],
  "source_url": "https://www.google.com/search?q=podcast+b-roll+automation",
  "collector_notes": "Captured during manual weekly competitor audit.",
  "operator_id": "analyst_sarah"
}
```

#### PowerShell Execution Example
```powershell
$Body = @{
    question_id = "your-question-id-here"
    raw_evidence = "IncuBrix ranked #1 for creator automated b-roll query."
    provider = "google_search"
    observation_type = "search_engine"
    rank_position = 1
    observed_features = @("answer_box", "organic_results")
    quoted_source_urls = @("https://incubrix.com/overview")
    operator_id = "analyst_1"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8001/v1/observations/manual-import" -Method Post -Body $Body -ContentType "application/json"
```
