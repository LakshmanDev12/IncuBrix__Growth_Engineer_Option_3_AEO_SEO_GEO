# =============================================================================
# IncuBrix AEO, SEO & GEO Visibility Engine
# Multi-Purpose Container Image (FastAPI Backend + Streamlit Dashboard)
# =============================================================================

FROM python:3.12-slim

# Prevent Python from writing bytecode and enable unbuffered standard I/O
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8001 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Install minimal OS utilities needed for container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache dependency layer
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --retries 5 --timeout 60 -r requirements.txt

# Copy source code and default data/documentation
COPY app/ ./app/
COPY data/ ./data/
COPY evidence/ ./evidence/
COPY outputs/ ./outputs/
COPY docs/ ./docs/
COPY entrypoint.sh .

# Ensure storage directories exist, script is executable, and normalize CRLF to LF
RUN mkdir -p /app/data /app/evidence/raw_responses /app/evidence/screenshots /app/outputs/reports /app/outputs/content_pages && \
    chmod +x /app/entrypoint.sh && \
    sed -i 's/\r$//' /app/entrypoint.sh

# Expose FastAPI backend (8001) and Streamlit dashboard (8501)
EXPOSE 8001 8501

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["all"]
