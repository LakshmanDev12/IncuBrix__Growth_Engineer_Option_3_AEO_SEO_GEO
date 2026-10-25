"""Main FastAPI Application Entrypoint for IncuBrix Visibility Engine."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import v1_router
from app.config import get_settings
from app.database.session import init_db
from app.exceptions import AppException, DuplicateEntityError, EntityNotFoundError
from app.logging_config import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger("incubrix.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    logger.info("Starting %s in %s mode...", settings.app_name, settings.app_env)
    init_db()
    yield
    logger.info("Shutting down %s...", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description=(
        "Production-minded AEO, SEO and GEO Visibility Engine foundation for Vk Analysis. "
        "Provides modular tracking, evidence integrity, technical audits, content briefs, "
        "and explicit tri-state visibility metrics."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
    """Handle 404 entity not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "Not Found", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(DuplicateEntityError)
async def duplicate_entity_handler(request: Request, exc: DuplicateEntityError) -> JSONResponse:
    """Handle 409 conflict duplicate errors."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": "Conflict", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(AppException)
async def domain_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle generic domain exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Bad Request", "message": exc.message, "details": exc.details},
    )


# Health check
@app.get("/health", tags=["Health"], summary="Service health check")
def health() -> dict:
    """Return operational health status."""
    return {
        "status": "ok",
        "service": "incubrix-visibility-engine",
        "environment": settings.app_env,
        "database": "sqlite_connected",
    }


# Root information endpoint
@app.get("/", tags=["Info"], summary="Engine metadata and documentation")
def root_info() -> dict:
    """Return engine metadata and navigational API links."""
    return {
        "name": settings.app_name,
        "version": "0.2.0",
        "documentation": "/docs",
        "v1_api": f"{settings.api_v1_prefix}",
        "endpoints": {
            "questions": f"{settings.api_v1_prefix}/questions",
            "observations": f"{settings.api_v1_prefix}/observations",
            "summary": f"{settings.api_v1_prefix}/summary",
            "evidence": f"{settings.api_v1_prefix}/evidence",
            "audit": f"{settings.api_v1_prefix}/audit/findings",
            "content": f"{settings.api_v1_prefix}/content/briefs",
            "pipeline": f"{settings.api_v1_prefix}/pipeline/runs",
        },
    }


# Mount v1 router
app.include_router(v1_router, prefix=settings.api_v1_prefix)
