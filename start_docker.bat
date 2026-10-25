@echo off
echo ==========================================================
echo  Starting IncuBrix Visibility Engine in Docker Container
echo ==========================================================

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    exit /b 1
)

echo [INFO] Building and starting containers via docker compose...
docker compose up --build -d

if errorlevel 0 (
    echo.
    echo [SUCCESS] Visibility Engine is up and running!
    echo  - FastAPI Backend API:   http://localhost:8001/docs
    echo  - Streamlit Dashboard:   http://localhost:8501
    echo.
    echo To view logs:     docker compose logs -f
    echo To stop services: docker compose down
) else (
    echo [ERROR] Failed to start Docker containers.
)
