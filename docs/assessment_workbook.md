# IncuBrix Visibility Engine — Assessment Workbook & Self-Check References

This document serves as the formal **Assessment Workbook and Traceability Matrix** for the IncuBrix AEO, SEO, and GEO Visibility Engine. It maps every technical and architectural requirement across all 9 modules to its concrete implementation files, database models, schemas, and verification tests.

---

## 📋 Executive Verification Summary

| Evaluation Domain | Scope | Status | Verification Evidence |
| :--- | :--- | :---: | :--- |
| **Module 1: Architecture & Foundation** | Pydantic v2 schemas, SQLite/SQLAlchemy 2.0 ORM, tri-state enums, config, structured logging | **PASS** | 100% type coverage, 0 circular imports, `tests/test_schemas.py` |
| **Module 2: Question Ingestion** | CSV parsing, RFC 4180 validation, intent categorization, deduplication, review curation | **PASS** | `tests/test_question_ingestion.py` (14/14 passed) |
| **Module 3: SEO & AEO Collection** | Search provider interface, manual evidence import, SHA-256 artifacts, rate limits | **PASS** | `tests/test_manual_collector.py` (7/7 passed), `tests/test_collector.py` |
| **Module 4: GEO Collector** | Multi-assistant adapters (Perplexity, OpenAI, Claude, Gemini), distinct mentions vs citations | **PASS** | `tests/test_geo_collector.py` (11/11 passed) |
| **Module 5: Visibility Scoring** | Documented SEO/AEO/GEO heuristics, period comparisons, safe zero-denominator handling | **PASS** | `tests/test_scoring.py` (10/10 passed) |
| **Module 6: Technical SEO Auditor** | 10 audit signals (robots.txt, llms.txt, Schema.org, canonical, etc.), 20 verified fixes | **PASS** | `tests/test_technical_audit.py` (13/13 passed), `outputs/20_prioritized_technical_fixes.md` |
| **Module 7: Content & Citation Engine** | 10 publish-ready AEO drafts, direct answers in 2 sentences, 30 real citation targets | **PASS** | `tests/test_content_engine.py` (11/11 passed), `outputs/content_pages/`, `outputs/citation_targets.csv` |
| **Module 8: Dashboard & Reporting** | Streamlit UI, provenance classification, RFC 4180 exports (visibility.csv, technical_fixes.csv) | **PASS** | `tests/test_reporting_and_dashboard.py` (12/12 passed), `app/frontend/app.py` |
| **Module 9: Pipeline Orchestration** | 6-stage unified workflow, bounded retries, provider recovery, cost tracking, CLI runners | **PASS** | `tests/test_pipeline_orchestration.py` (12/12 passed), `app/pipeline/cli.py` |
| **End-to-End Test Suite** | Full regression across all unit, integration, and API test suites | **PASS** | **142 passed, 0 failures** in ~4.3s |

---

## 🔍 Module-by-Module Traceability Matrix

### Module 1: Foundational Architecture & Shared Schemas
- **Requirement**: Provide clean, modular architecture separating API, ORM, schemas, engine, collectors, audit, content, and pipeline orchestration. Enforce strict tri-state / explicit unknown and unavailable states.
- **Implementation**:
  - Configuration container: [`app/config.py`](file:///e:/Incubrix/visibility-engine/app/config.py)
  - Structured logging: [`app/logging_config.py`](file:///e:/Incubrix/visibility-engine/app/logging_config.py)
  - Tri-state enums: [`app/schemas/common.py`](file:///e:/Incubrix/visibility-engine/app/schemas/common.py) (`MentionStatus`, `CitationStatus`, `CollectionStatus`, `ArtifactType`, `AuditSeverity`, `ValidationStatus`)
  - Shared Pydantic models: [`app/schemas/`](file:///e:/Incubrix/visibility-engine/app/schemas/)
  - SQLAlchemy 2.0 ORM Base: [`app/database/base.py`](file:///e:/Incubrix/visibility-engine/app/database/base.py), [`app/database/models/`](file:///e:/Incubrix/visibility-engine/app/database/models/)
- **Self-Check Reference**:
  - `tests/test_schemas.py::test_missing_data_never_treated_as_negative`
  - `tests/test_schemas.py::test_evidence_hashing_and_deduplication_checksum`
  - `tests/test_schemas.py::test_observation_fingerprint_generation`

---

### Module 2: Question Ingestion Engine
- **Requirement**: Support CSV import/export, RFC 4180 parsing, URL and source metadata validation, text deduplication (whitespace/casing normalized), intent categorization (informational, commercial, transactional, navigational), review curation workflow (`pending`, `approved`, `rejected`), and real source provenance.
- **Implementation**:
  - Ingestion Engine: [`app/engine/question_ingestion.py`](file:///e:/Incubrix/visibility-engine/app/engine/question_ingestion.py) (`QuestionIngestionEngine`, `validate_url`, `categorize_intent`)
  - Query Normalization: [`app/engine/normalizer.py`](file:///e:/Incubrix/visibility-engine/app/engine/normalizer.py) (`normalize_text`, `normalize_url`)
  - Question Repository: [`app/database/repositories/question_repo.py`](file:///e:/Incubrix/visibility-engine/app/database/repositories/question_repo.py)
  - REST API Endpoints: [`app/api/v1/questions.py`](file:///e:/Incubrix/visibility-engine/app/api/v1/questions.py) (`POST /v1/questions/import-csv`, `GET /v1/questions/export-csv`)
- **Self-Check Reference**:
  - `tests/test_question_ingestion.py::test_csv_import_valid_rows`
  - `tests/test_question_ingestion.py::test_csv_import_deduplication_preserves_first`
  - `tests/test_question_ingestion.py::test_csv_import_invalid_rows_reported`
  - `tests/test_question_ingestion.py::test_url_validation_rejection`
  - `tests/test_question_ingestion.py::test_intent_categorization_heuristic`
  - `tests/test_question_ingestion.py::test_csv_export_roundtrip`

---

### Module 3: SEO & AEO Collection
- **Requirement**: Provider interface for search engines and answer boxes. Live API adapter only when explicitly configured; manual evidence-import adapter for unconfigured engines. Capture question ID, market, location, timestamp, ranking position, observed features, quoted URLs, raw evidence reference, and collection status.
- **Implementation**:
  - Base Provider Contract: [`app/providers/base.py`](file:///e:/Incubrix/visibility-engine/app/providers/base.py) (`BaseProvider`, `ProviderResult`)
  - Search Provider Client: [`app/providers/search_provider.py`](file:///e:/Incubrix/visibility-engine/app/providers/search_provider.py) (`SearchProvider`)
  - Automated Observation Collector: [`app/collectors/automated_collector.py`](file:///e:/Incubrix/visibility-engine/app/collectors/automated_collector.py) (`AutomatedCollector`)
  - Manual Evidence Adapter: [`app/collectors/manual_collector.py`](file:///e:/Incubrix/visibility-engine/app/collectors/manual_collector.py) (`ManualEvidenceAdapter`)
  - Evidence Repository: [`app/database/repositories/evidence_repo.py`](file:///e:/Incubrix/visibility-engine/app/database/repositories/evidence_repo.py)
- **Self-Check Reference**:
  - `tests/test_manual_collector.py::test_manual_evidence_import_text_success`
  - `tests/test_manual_collector.py::test_manual_evidence_import_html_and_json_artifacts`
  - `tests/test_manual_collector.py::test_manual_evidence_deduplication`
  - `tests/test_manual_collector.py::test_manual_evidence_operator_override`
  - `tests/test_collector.py::test_automated_collector_unconfigured_resilience`

---

### Module 4: GEO (Generative Engine Optimization) Collector
- **Requirement**: Independent adapters for AI assistants (Perplexity, OpenAI ChatGPT, Anthropic Claude, Google Gemini). Support manual transcript import. Persist raw responses and citation URLs with question ID, assistant, model, market, timestamp, and status. Distinctly extract brand mentions and web citations without conflation. Never claim unqueried or unconfigured assistants were run.
- **Implementation**:
  - AI Assistant Adapters: [`app/providers/ai_provider.py`](file:///e:/Incubrix/visibility-engine/app/providers/ai_provider.py) (`PerplexityAIProvider`, `OpenAIProvider`, `GeminiProvider`, `ClaudeAIProvider`, `GoogleAIOverviewProvider`)
  - GEO Observation Collector: [`app/collectors/geo_collector.py`](file:///e:/Incubrix/visibility-engine/app/collectors/geo_collector.py) (`GEOCollector`)
  - Mention & Citation Analyzer: [`app/engine/mention_analyzer.py`](file:///e:/Incubrix/visibility-engine/app/engine/mention_analyzer.py) (`MentionAnalyzer`, separating `incubrix_mentioned` from `incubrix_cited`)
- **Self-Check Reference**:
  - `tests/test_geo_collector.py::test_geo_perplexity_adapter_with_citations_and_mention`
  - `tests/test_geo_collector.py::test_geo_openai_adapter_mention_without_citation`
  - `tests/test_geo_collector.py::test_geo_citation_without_mention`
  - `tests/test_geo_collector.py::test_geo_unsupported_assistant_does_not_claim_queried`
  - `tests/test_geo_collector.py::test_geo_manual_import_chatgpt_transcript`
  - `tests/test_mention_analyzer.py::test_missing_text_is_explicit_unknown`
  - `tests/test_mention_analyzer.py::test_missing_links_is_explicit_unavailable`

---

### Module 5: Visibility Scoring & Analytics
- **Requirement**: Calculate documented visibility metrics: Top-10 Ranking Rate, Answer-Feature Presence Rate, AI Mention Rate, AI Citation Rate, and Blended Visibility Score (0–100). Exclude failed/unavailable observations from valid denominators and report them separately. Handle zero denominators safely without `ZeroDivisionError`. Deduplicate repeated observations and support date, market, and provider period comparisons.
- **Implementation**:
  - Heuristic Scoring Formula: [`app/engine/scoring.py`](file:///e:/Incubrix/visibility-engine/app/engine/scoring.py) (`calculate_visibility_score`)
  - Analytics & Aggregation Engine: [`app/engine/visibility_metrics.py`](file:///e:/Incubrix/visibility-engine/app/engine/visibility_metrics.py) (`VisibilityMetricsCalculator.calculate_metrics`, `compare_periods`)
  - REST API Endpoints: [`app/api/v1/observations.py`](file:///e:/Incubrix/visibility-engine/app/api/v1/observations.py) (`GET /v1/observations/metrics`, `GET /v1/observations/summary`)
- **Self-Check Reference**:
  - `tests/test_scoring.py::test_perfect_visibility_score`
  - `tests/test_scoring.py::test_ai_assistant_unranked_mention_only`
  - `tests/test_scoring.py::test_failed_collection_returns_none`
  - `tests/test_scoring.py::test_unknown_evidence_not_penalized_with_false_score`
  - `tests/test_scoring.py::test_metrics_zero_denominators_safe_handling`
  - `tests/test_scoring.py::test_metrics_missing_values_and_exclusions`
  - `tests/test_scoring.py::test_metrics_repeated_records_deduplication`
  - `tests/test_scoring.py::test_metrics_date_period_comparison`

---

### Module 6: Technical SEO & AEO Auditor
- **Requirement**: Public page technical inspection across indexability signals, meta title/description bounds, heading hierarchy, canonical links, sitemap.xml, robots.txt, internal links, performance signals, Schema.org structured data, and optional `llms.txt` discovery check. Generate evidence-backed findings with severity, confidence, recommendation, and code/text patches. Enforce strict fix validation (`TechnicalAuditor.validate_fix`). Never claim a fix is validated without re-running the audit.
- **Implementation**:
  - HTML & Page Inspector: [`app/audit/html_inspector.py`](file:///e:/Incubrix/visibility-engine/app/audit/html_inspector.py)
  - Specialized Audit Evaluators: [`app/audit/evaluators/`](file:///e:/Incubrix/visibility-engine/app/audit/evaluators/) (`robots_evaluator.py`, `llms_txt_evaluator.py`, `schema_evaluator.py`, `performance_evaluator.py`)
  - Technical Auditor Orchestrator: [`app/audit/auditor.py`](file:///e:/Incubrix/visibility-engine/app/audit/auditor.py) (`TechnicalAuditor.audit_url`, `validate_fix`)
  - Prioritized Fixes Artifact: [`outputs/20_prioritized_technical_fixes.md`](file:///e:/Incubrix/visibility-engine/outputs/20_prioritized_technical_fixes.md)
  - Audit Export: [`outputs/technical_fixes.csv`](file:///e:/Incubrix/visibility-engine/outputs/technical_fixes.csv)
- **Self-Check Reference**:
  - `tests/test_technical_audit.py::test_audit_indexability_signals`
  - `tests/test_technical_audit.py::test_audit_robots_txt`
  - `tests/test_technical_audit.py::test_audit_llms_txt_optional_discovery_check`
  - `tests/test_technical_audit.py::test_audit_structured_data_schema_org`
  - `tests/test_technical_audit.py::test_strict_fix_validation_workflow`

---

### Module 7: Content & Citation Engine
- **Requirement**: Generate ten publish-ready page drafts from approved creator questions. Include direct answers in the first two sentences, structured headings, title (max 60 chars), meta description (max 160 chars), internal-link suggestions with anchor text, citations to real third-party sources, and valid Schema.org JSON-LD. Maintain deterministic fallback when LLM is unconfigured. Label drafts as unreviewed until human verification. Identify and store 30 real third-party citation targets with authority score, URL, and angle.
- **Implementation**:
  - Verified Product Knowledge: [`app/content/product_knowledge.py`](file:///e:/Incubrix/visibility-engine/app/content/product_knowledge.py)
  - Content Engine: [`app/content/content_engine.py`](file:///e:/Incubrix/visibility-engine/app/content/content_engine.py) (`ContentCitationEngine`)
  - Content Validator: [`app/content/validator.py`](file:///e:/Incubrix/visibility-engine/app/content/validator.py) (`ContentValidator`)
  - 10 Generated Drafts: [`outputs/content_pages/`](file:///e:/Incubrix/visibility-engine/outputs/content_pages/)
  - 30 Citation Opportunities: [`outputs/citation_targets.csv`](file:///e:/Incubrix/visibility-engine/outputs/citation_targets.csv)
- **Self-Check Reference**:
  - `tests/test_content_engine.py::test_ten_publish_ready_pages_generation`
  - `tests/test_content_engine.py::test_direct_answers_in_first_two_sentences`
  - `tests/test_content_engine.py::test_useful_headings_and_structure`
  - `tests/test_content_engine.py::test_metadata_title_and_description_bounds`
  - `tests/test_content_engine.py::test_internal_link_suggestions_and_anchor_text`
  - `tests/test_content_engine.py::test_sourced_citations_real_third_party`
  - `tests/test_content_engine.py::test_appropriate_structured_data_json_ld`
  - `tests/test_content_engine.py::test_thirty_real_third_party_citation_opportunities`
  - `tests/test_content_engine.py::test_deterministic_template_fallback_when_llm_unconfigured`
  - `tests/test_content_engine.py::test_drafts_labeled_unreviewed_until_human_verification`
  - `tests/test_content_engine.py::test_content_validator_detects_defects`

---

### Module 8: Streamlit Dashboard & Report Generator
- **Requirement**: Build an interactive Streamlit dashboard displaying overview metrics, date comparisons, market/provider filters, question-level evidence inspection, technical audit findings, content drafts, and citation opportunities. Export `visibility.csv`, `technical_fixes.csv`, `citation_targets.csv`, and weekly intelligence reports (`.md` and `.json`). Clearly categorize provenance into `real`, `manual`, `mocked`, or `unavailable`. Never invent dashboard metrics.
- **Implementation**:
  - Streamlit UI Dashboard: [`app/frontend/app.py`](file:///e:/Incubrix/visibility-engine/app/frontend/app.py)
  - Report Generation Engine: [`app/engine/report_generator.py`](file:///e:/Incubrix/visibility-engine/app/engine/report_generator.py) (`ReportGenerator.export_visibility_csv`, `export_technical_fixes_csv`, `export_citation_targets_csv`, `generate_weekly_report`)
  - Provenance Mode Classifier: `ReportGenerator.determine_provenance_mode`
  - Weekly Intelligence Reports: [`outputs/reports/`](file:///e:/Incubrix/visibility-engine/outputs/reports/)
- **Self-Check Reference**:
  - `tests/test_reporting_and_dashboard.py::test_export_visibility_csv_rfc4180`
  - `tests/test_reporting_and_dashboard.py::test_export_technical_fixes_csv`
  - `tests/test_reporting_and_dashboard.py::test_export_citation_targets_csv`
  - `tests/test_reporting_and_dashboard.py::test_weekly_report_generation_markdown_and_json`
  - `tests/test_reporting_and_dashboard.py::test_provenance_mode_classification`
  - `tests/test_reporting_and_dashboard.py::test_dashboard_empty_states_handled`

---

### Module 9: Pipeline Orchestration & CLI
- **Requirement**: Unified 6-stage pipeline orchestrator (Ingestion -> Collection -> Scoring -> Auditing -> Content -> Reporting). CLI runners for complete run and incremental refresh. Job status tracking, bounded retries with error discrimination (transient vs permanent), idempotency via daily observation fingerprints, provider failure isolation, duration tracking, and actual/estimated cost accounting.
- **Implementation**:
  - Unified Orchestrator: [`app/pipeline/orchestrator.py`](file:///e:/Incubrix/visibility-engine/app/pipeline/orchestrator.py) (`PipelineOrchestrator`)
  - CLI Runner: [`app/pipeline/cli.py`](file:///e:/Incubrix/visibility-engine/app/pipeline/cli.py) (`complete`, `refresh`)
  - Bounded Retries: [`app/pipeline/retry.py`](file:///e:/Incubrix/visibility-engine/app/pipeline/retry.py) (`retry_with_backoff`, `is_transient_error`)
  - Cost Accounting: [`app/pipeline/cost_tracker.py`](file:///e:/Incubrix/visibility-engine/app/pipeline/cost_tracker.py) (`CostTracker`)
  - Pipeline Telemetry Schema: [`app/schemas/pipeline.py`](file:///e:/Incubrix/visibility-engine/app/schemas/pipeline.py)
- **Self-Check Reference**:
  - `tests/test_pipeline_orchestration.py::test_retry_transient_error_eventual_success`
  - `tests/test_pipeline_orchestration.py::test_retry_permanent_error_fails_immediately`
  - `tests/test_pipeline_orchestration.py::test_retry_exhausted_raises_last_error`
  - `tests/test_pipeline_orchestration.py::test_is_transient_error_classification`
  - `tests/test_pipeline_orchestration.py::test_cost_tracker_recording_and_summary`
  - `tests/test_pipeline_orchestration.py::test_pipeline_provider_failure_recovery`
  - `tests/test_pipeline_orchestration.py::test_pipeline_stage_failure_short_circuit`
  - `tests/test_pipeline_orchestration.py::test_pipeline_idempotency_daily_fingerprint`
  - `tests/test_pipeline_orchestration.py::test_pipeline_cli_complete_execution`
  - `tests/test_pipeline_orchestration.py::test_pipeline_cli_refresh_execution`

---

## 🔒 Security, Reliability & Public Website Limits
1. **Secret Handling**: Zero API keys or secrets are committed or hardcoded. The `.env.example` file contains safe configuration templates. Unconfigured providers log explicit warnings and safely enter `unavailable` status without throwing unhandled exceptions.
2. **Crawl Politeness & Limits**: Public technical audits respect HTTP rate limits, utilize polite User-Agent headers, enforce bounded crawl depths (max 10 pages per run), and inspect `robots.txt` directives before making requests.
3. **Database Concurrency**: SQLAlchemy sessions use atomic context managers (`with SessionLocal() as session:`) ensuring dirty state is never leaked across concurrent web or pipeline requests.
