"""FastAPI dependency injection providers."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.collectors.automated_collector import AutomatedCollector
from app.config import get_settings
from app.database.repositories.audit_repo import AuditFindingRepository
from app.database.repositories.citation_repo import CitationRepository
from app.database.repositories.content_repo import ContentRepository
from app.database.repositories.evidence_repo import EvidenceRepository
from app.database.repositories.observation_repo import ObservationRepository
from app.database.repositories.pipeline_repo import PipelineRunRepository
from app.database.repositories.question_repo import QuestionRepository
from app.database.session import get_db
from app.providers.ai_provider import AIProvider
from app.providers.base import BaseProvider
from app.providers.search_provider import SearchProvider


def get_question_repository(db: Session = Depends(get_db)) -> QuestionRepository:
    """Dependency providing QuestionRepository."""
    return QuestionRepository(db)


def get_observation_repository(db: Session = Depends(get_db)) -> ObservationRepository:
    """Dependency providing ObservationRepository."""
    return ObservationRepository(db)


def get_evidence_repository(db: Session = Depends(get_db)) -> EvidenceRepository:
    """Dependency providing EvidenceRepository."""
    return EvidenceRepository(db)


def get_audit_repository(db: Session = Depends(get_db)) -> AuditFindingRepository:
    """Dependency providing AuditFindingRepository."""
    return AuditFindingRepository(db)


def get_content_repository(db: Session = Depends(get_db)) -> ContentRepository:
    """Dependency providing ContentRepository."""
    return ContentRepository(db)


def get_citation_repository(db: Session = Depends(get_db)) -> CitationRepository:
    """Dependency providing CitationRepository."""
    return CitationRepository(db)


def get_pipeline_repository(db: Session = Depends(get_db)) -> PipelineRunRepository:
    """Dependency providing PipelineRunRepository."""
    return PipelineRunRepository(db)


def get_search_provider() -> SearchProvider:
    """Dependency providing configured SearchProvider."""
    settings = get_settings()
    return SearchProvider(
        api_key=settings.serp_api_key,
        api_url=settings.serp_api_url,
    )


def get_ai_provider() -> AIProvider:
    """Dependency providing configured AIProvider."""
    settings = get_settings()
    return AIProvider(
        api_key=settings.ai_provider_api_key,
        api_url=settings.ai_provider_api_url,
        model=settings.ai_provider_model,
    )


def get_automated_collector(
    provider: BaseProvider = Depends(get_search_provider),
    evidence_repo: EvidenceRepository = Depends(get_evidence_repository),
    obs_repo: ObservationRepository = Depends(get_observation_repository),
    citation_repo: CitationRepository = Depends(get_citation_repository),
) -> AutomatedCollector:
    """Dependency providing AutomatedCollector."""
    return AutomatedCollector(
        provider=provider,
        evidence_repo=evidence_repo,
        observation_repo=obs_repo,
        citation_repo=citation_repo,
    )
