# IncuBrix Visibility Engine — Docker Container Guide

This guide details the standalone container architecture, orchestration options, volume persistence, and CLI operations for the **IncuBrix AEO, SEO & GEO Visibility Engine**.

---

## 🏗️ Container Architecture

The container image is built on `python:3.12-slim` and encapsulates both the **FastAPI Backend** and the **Streamlit Dashboard**, with persistent storage volumes for SQLite data, raw evidence artifacts, and generated reports.

```
                              ┌─────────────────────────────────────────┐
                              │         Host Machine (Windows/Linux)    │
                              │                                         │
                              │    Port 8001           Port 8501        │
                              └────────┬───────────────────┬────────────┘
                                       │                   │
                                       ▼                   ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Docker Network: incubrix-visibility-net                                │
│                                                                       │
│  ┌───────────────────────────────────┐    ┌────────────────────────┐  │
│  │ service: api                      │    │ service: dashboard     │  │
│  │ container: incubrix-visibility-api│    │ container:             │  │
│  │ (FastAPI on :8001)                │◄───┤ incubrix-visibility-   │  │
│  │                                   │    │ dashboard              │  │
│  │ - REST API endpoints              │    │ (Streamlit on :8501)   │  │
│  │ - SQLite DB access                │    │                        │  │
│  │ - Pipeline orchestrator           │    │ - Interactive UI       │  │
│  │ - Evidence preservation           │    │ - Real-time metrics    │  │
│  └─────────────────┬─────────────────┘    └───────────┬────────────┘  │
│                    │                                  │               │
└────────────────────┼──────────────────────────────────┼───────────────┘
                     │                                  │
                     ▼                                  ▼
      ┌────────────────────────────────────────────────────────┐
      │ Persistent Volumes (Mounted from host):                │
      │   - ./data     -> /app/data        (SQLite database)   │
      │   - ./evidence -> /app/evidence    (Raw JSON/HTML/img) │
      │   - ./outputs  -> /app/outputs     (CSVs & Reports)    │
      └────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart Options

### Option 1: Docker Compose (Recommended)

Run both the FastAPI backend and Streamlit dashboard as isolated, networked services:

```powershell
# 1. Start all services in the background
docker compose up --build -d

# 2. View streaming logs
docker compose logs -f

# 3. Stop services
docker compose down
```

**Access URLs:**
- **FastAPI Backend API**: [`http://localhost:8001/docs`](http://localhost:8001/docs) (Swagger UI)
- **FastAPI Healthcheck**: [`http://localhost:8001/health`](http://localhost:8001/health)
- **Streamlit Dashboard**: [`http://localhost:8501`](http://localhost:8501)

Alternatively, on Windows PowerShell, run:
```powershell
.\start_docker.ps1
```

---

### Option 2: Standalone Single-Container

Run both backend and dashboard inside a single lightweight container using the built-in process supervisor:

```powershell
# 1. Build the standalone image
docker build -t incubrix-visibility-engine .

# 2. Run container with port bindings and persistent volumes
docker run -d `
  --name incubrix-visibility `
  -p 8001:8001 `
  -p 8501:8501 `
  -v "${PWD}/data:/app/data" `
  -v "${PWD}/evidence:/app/evidence" `
  -v "${PWD}/outputs:/app/outputs" `
  incubrix-visibility-engine
```

To stop:
```powershell
docker stop incubrix-visibility
docker rm incubrix-visibility
```

---

### Option 3: Run Only Backend or Only Dashboard

The container entrypoint supports explicit operational modes via command arguments:

```powershell
# Run ONLY FastAPI Backend:
docker run -d -p 8001:8001 incubrix-visibility-engine api

# Run ONLY Streamlit Dashboard:
docker run -d -p 8501:8501 -e API_BASE_URL="http://host.docker.internal:8001/v1" incubrix-visibility-engine dashboard
```

---

## ⚡ Running Pipeline CLI Inside Docker

You can trigger complete pipeline runs or incremental measurements directly inside the running container:

```powershell
# Execute complete pipeline run with live review sample input
docker compose exec api python -m app.pipeline.cli complete --sample-input

# Execute incremental refresh run
docker compose exec api python -m app.pipeline.cli refresh --market "US"

# Execute test suite inside the container
docker compose exec api pytest -v
```

---

## ⚙️ Environment Variables

Create or update `.env` in the project root to pass live provider credentials:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `API_BASE_URL` | `http://127.0.0.1:8001/v1` (`http://api:8001/v1` in compose) | API endpoint URL used by Streamlit |
| `SERP_API_KEY` | *(empty)* | Google Search API key for live search queries |
| `PERPLEXITY_API_KEY` | *(empty)* | Perplexity Sonar API key for GEO queries |
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key for ChatGPT queries |
| `ANTHROPIC_API_KEY` | *(empty)* | Anthropic API key for Claude queries |
| `GEMINI_API_KEY` | *(empty)* | Google Gemini API key for search grounding |
| `DATABASE_URL` | `sqlite:////app/data/visibility.db` | Path to persistent SQLite database |

---

## 🔒 Security & Best Practices

1. **Non-Root / Minimal Footprint**: The base image is Debian slim (`python:3.12-slim`), excluding unnecessary compiler toolchains.
2. **Layer Caching**: `requirements.txt` is copied and installed independently before copying application code, ensuring sub-second rebuilds when modifying application logic.
3. **Deterministic Seeding**: If the persistent `visibility.db` volume is empty upon container launch, the entrypoint automatically seeds synthetic fixtures and initial tables.
4. **Healthchecks**: Built-in container healthchecks poll `/health` every 15 seconds to ensure automated restart on failure.
