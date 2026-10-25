# IncuBrix Visibility Engine - Docker Startup Script
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting IncuBrix Visibility Engine in Docker Container   " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Check if Docker is running
docker info >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Start containers via docker compose
Write-Host "[INFO] Building and starting containers..." -ForegroundColor Green
docker compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Visibility Engine is up and running!" -ForegroundColor Green
    Write-Host " - FastAPI Backend API:   http://localhost:8001/docs" -ForegroundColor Yellow
    Write-Host " - Streamlit Dashboard:   http://localhost:8501" -ForegroundColor Yellow
    Write-Host "`nTo view logs:     docker compose logs -f" -ForegroundColor Gray
    Write-Host "To stop services: docker compose down" -ForegroundColor Gray
} else {
    Write-Host "[ERROR] Failed to start Docker containers." -ForegroundColor Red
}
