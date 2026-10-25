#!/bin/sh
set -e

# =============================================================================
# IncuBrix Visibility Engine — Container Entrypoint
# =============================================================================

# Ensure data and output directories exist
mkdir -p /app/data /app/evidence/raw_responses /app/evidence/screenshots /app/outputs/reports /app/outputs/content_pages

# Initialize SQLite database if not present
if [ ! -f "/app/data/visibility.db" ]; then
    echo "[IncuBrix Docker] Initializing database and seeding synthetic fixtures..."
    python -m app.database.init_db --seed
fi

MODE="${1:-all}"

case "$MODE" in
    api)
        echo "[IncuBrix Docker] Starting FastAPI backend on port ${PORT:-8001}..."
        exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8001}"
        ;;
    dashboard)
        echo "[IncuBrix Docker] Starting Streamlit dashboard on port ${STREAMLIT_SERVER_PORT:-8501}..."
        exec streamlit run app/frontend/app.py \
            --server.port "${STREAMLIT_SERVER_PORT:-8501}" \
            --server.address 0.0.0.0 \
            --server.headless true
        ;;
    pipeline)
        shift
        echo "[IncuBrix Docker] Executing Pipeline CLI: $*"
        exec python -m app.pipeline.cli "$@"
        ;;
    all)
        echo "[IncuBrix Docker] Starting FastAPI backend (background) & Streamlit dashboard..."
        uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8001}" &
        UVICORN_PID=$!

        echo "[IncuBrix Docker] Waiting for backend API to be ready..."
        until curl -s "http://127.0.0.1:${PORT:-8001}/health" >/dev/null 2>&1; do
            sleep 1
        done
        echo "[IncuBrix Docker] Backend API is healthy!"

        streamlit run app/frontend/app.py \
            --server.port "${STREAMLIT_SERVER_PORT:-8501}" \
            --server.address 0.0.0.0 \
            --server.headless true &
        STREAMLIT_PID=$!

        # Trap termination signals and forward to child processes
        trap "kill -TERM $UVICORN_PID $STREAMLIT_PID 2>/dev/null" SIGINT SIGTERM
        wait $UVICORN_PID $STREAMLIT_PID
        ;;
    *)
        exec "$@"
        ;;
esac
