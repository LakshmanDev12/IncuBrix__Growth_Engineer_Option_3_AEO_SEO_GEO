"""API v1 router aggregating all modular sub-routers."""

from fastapi import APIRouter

from app.api.v1.audit import router as audit_router
from app.api.v1.citation import router as citation_router
from app.api.v1.content import router as content_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.geo import router as geo_router
from app.api.v1.observations import router as observations_router
from app.api.v1.pipeline import router as pipeline_router
from app.api.v1.questions import router as questions_router
from app.api.v1.reports import router as reports_router
from app.api.v1.scoring import router as scoring_router

v1_router = APIRouter()

v1_router.include_router(questions_router)
v1_router.include_router(observations_router)
v1_router.include_router(scoring_router)
v1_router.include_router(geo_router)
v1_router.include_router(evidence_router)
v1_router.include_router(audit_router)
v1_router.include_router(content_router)
v1_router.include_router(citation_router)
v1_router.include_router(reports_router)
v1_router.include_router(pipeline_router)
