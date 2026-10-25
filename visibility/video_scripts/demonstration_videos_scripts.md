# IncuBrix Visibility Engine — Demonstration Video Outlines & Submission Links

This document provides structured recording outlines, slide/screen walkthrough scripts, exact terminal commands, and submission link placeholders for the two required demonstration videos.

> [!IMPORTANT]
> **Candidate Action Required**: In compliance with the assessment guidelines (*"Do not fabricate missing deliverables. Report missing or incomplete items explicitly"*), video recording is performed directly by the candidate presenting the live codebase and dashboard. Use the placeholders below to insert your recorded video links prior to final submission.

---

## 📹 Video Submission Link Placeholders

| Video Deliverable | Focus Area | Recommended Duration | Submission Link Placeholder |
| :--- | :--- | :---: | :--- |
| **Video 1: Technical Architecture & Test Suite** | Architecture, CLI pipeline, database persistence, bounded retry, SHA-256 hashing, pytest | 5 – 7 Minutes | `[Candidate Submission Link - Video 1: Technical Architecture & Test Execution]` *(e.g., Loom / YouTube Unlisted / Google Drive)* |
| **Video 2: Executive Dashboard & Engine Walkthrough** | Streamlit UI, visibility metrics, date comparisons, 20 technical fixes, 10 content pages, 30 citations | 5 – 7 Minutes | `[Candidate Submission Link - Video 2: Executive Dashboard & Product Walkthrough]` *(e.g., Loom / YouTube Unlisted / Google Drive)* |

---

## 🎬 Video 1 Walkthrough Script: Technical Architecture & Pipeline Orchestration

### Target Audience
Engineering Leads, Technical Evaluators, and Senior Architects.

### Key Objectives
Demonstrate codebase modularity, strict schema validation, 100% test pass rate, database initialization, CLI pipeline execution with bounded retries, and raw evidence provenance.

### Screen Sequence & Script Outline

#### 1. Codebase Architecture & Schema Hygiene (0:00 – 1:30)
- **Visual**: VS Code / IDE displaying the modular project tree (`app/`, `schemas/`, `database/`, `engine/`, `collectors/`, `providers/`, `audit/`, `content/`, `pipeline/`).
- **Talking Points**:
  - Explain the separation of concerns: API routes never execute business logic directly; all access is mediated through repositories.
  - Highlight Pydantic v2 schemas and explicit tri-state enums (`MentionStatus`, `CitationStatus`, `CollectionStatus`, `ArtifactType`). Emphasize that **missing evidence is never treated as a negative result**.
  - Show SQLAlchemy 2.0 ORM models and SQLite persistence with SHA-256 evidence hashing.

#### 2. Test Suite Execution (1:30 – 3:00)
- **Terminal Command**:
  ```powershell
  pytest -v
  ```
- **Talking Points**:
  - Point out that all **142 tests pass with 0 failures** across unit, integration, repository, and API layers in under 5 seconds.
  - Highlight specific tests:
    - Bounded retries and transient error classification (`test_pipeline_orchestration.py`).
    - Provider failure isolation and recovery.
    - Zero denominator safety in scoring analytics (`test_scoring.py`).
    - Strict fix validation workflow in the technical auditor (`test_technical_audit.py`).

#### 3. Fresh Database Setup & Seed (3:00 – 4:15)
- **Terminal Command**:
  ```powershell
  Remove-Item data\visibility.db -Force -ErrorAction SilentlyContinue
  python -m app.database.init_db --seed
  ```
- **Talking Points**:
  - Demonstrate clean, deterministic database initialization from scratch.
  - Show that synthetic test fixtures are clearly tagged (`is_test_fixture=True`) and isolated from live measurements.

#### 4. Pipeline CLI Execution with Small New Input Set (4:15 – 6:00)
- **Terminal Command**:
  ```powershell
  python -m app.pipeline.cli complete --input-file "data/live_review_sample.csv"
  ```
- **Talking Points**:
  - Walk through each of the 6 stages executing in the terminal:
    1. *Stage 1*: Question Ingestion & Validation (RFC 4180 parsing, intent categorization, auto-approval).
    2. *Stage 2*: Measurement & Collection (Google SERP and Perplexity querying with bounded retry).
    3. *Stage 3*: Scoring & Analytics (calculating Top-10 rate, AI mention rate, AI citation rate).
    4. *Stage 4*: Technical SEO Audit (DOM parsing, robots.txt, llms.txt, Schema.org).
    5. *Stage 5*: Content Draft Generation (10 pages with 2-sentence direct answers).
    6. *Stage 6*: Intelligence Reporting & RFC 4180 CSV export.
  - Emphasize total runtime tracking, idempotency via daily observation fingerprints, and actual/estimated API cost reporting.

---

## 🎬 Video 2 Walkthrough Script: Streamlit Dashboard & Product Walkthrough

### Target Audience
VP of Growth, Head of Product, SEO Strategists, and Marketing Executives.

### Key Objectives
Demonstrate the interactive Streamlit dashboard, executive scorecards, date comparisons, question-level inspection, technical SEO fixes, publish-ready AEO content drafts, and 30 citation targets.

### Screen Sequence & Script Outline

#### 1. Launching the Dashboard (0:00 – 0:45)
- **Terminal Command**:
  ```powershell
  streamlit run app/frontend/app.py
  ```
- **Talking Points**:
  - Show the live dashboard running locally at `http://localhost:8501`.
  - Emphasize that the dashboard is bound to live database records via REST API endpoints—**zero hardcoded or simulated mock values**.

#### 2. Overview Metrics & Provenance Breakdown (0:45 – 2:00)
- **Visual**: Overview tab with KPI metric cards.
- **Talking Points**:
  - Walk through the core KPIs: Average Visibility Score, Top-10 Ranking Rate, AI Mention Rate, and AI Citation Rate.
  - Point out the **Provenance Breakdown**: explicitly distinguishing `real`, `manual`, `mocked`, and `unavailable` observations.
  - Show date range and market filters in the sidebar.

#### 3. Question-Level Evidence Inspection (2:00 – 3:15)
- **Visual**: Detailed Observations & Questions tab.
- **Talking Points**:
  - Select an individual creator question (e.g., *"How can video creators automate b-roll selection using AI?"*).
  - Inspect ranking position, answer box presence, quoted domains, and raw evidence payload.
  - Demonstrate that brand mentions and web citations are tracked separately.

#### 4. Technical SEO Audit & 20 Prioritized Fixes (3:15 – 4:30)
- **Visual**: Technical SEO Audit tab.
- **Talking Points**:
  - Present the Technical Health Score (52/100 -> remediated target).
  - Show findings categorized by severity (`critical`, `high`, `medium`, `low`).
  - Highlight the 20 concrete code patches for `robots.txt`, `llms.txt`, and Schema.org structured data.
  - Demonstrate the **Strict Fix Validation Workflow**: findings cannot be marked validated without re-running the audit.

#### 5. Content Engine & 30 Citation Targets (4:30 – 5:30)
- **Visual**: Content Drafts & Citation Opportunities tabs.
- **Talking Points**:
  - Display the 10 publish-ready AEO drafts in `outputs/content_pages/`.
  - Verify that each draft begins with a direct answer in the first two sentences for immediate snippet extraction.
  - Showcase the 30 real third-party citation targets in `outputs/citation_targets.csv` with domain authority scores and pitch angles.

#### 6. Export Capabilities & Closing (5:30 – 6:00)
- **Visual**: Reports & Exports tab.
- **Talking Points**:
  - Download `visibility.csv`, `technical_fixes.csv`, and `citation_targets.csv`.
  - Show the persisted weekly executive markdown reports in `outputs/reports/`.
  - Reiterate that IncuBrix is primed for a 90-day scale-out.
