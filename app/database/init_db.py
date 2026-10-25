"""Database schema initialization and seed runner."""

import argparse
import json
from pathlib import Path

from app.config import PROJECT_ROOT, get_settings
from app.database.repositories.audit_repo import AuditFindingRepository
from app.database.repositories.content_repo import ContentRepository
from app.database.repositories.evidence_repo import EvidenceRepository
from app.database.repositories.observation_repo import ObservationRepository
from app.database.repositories.question_repo import QuestionRepository
from app.database.session import SessionLocal, init_db
from app.logging_config import configure_logging, get_logger
from app.schemas.audit import AuditFindingCreate
from app.schemas.content import ContentBriefCreate
from app.schemas.evidence import EvidenceArtifactCreate
from app.schemas.observations import ObservationCreate
from app.schemas.questions import QuestionCreate

logger = get_logger("incubrix.init_db")


def seed_synthetic_fixtures() -> None:
    """Load labeled synthetic test fixtures into the database."""
    fixtures_path = PROJECT_ROOT / "data" / "synthetic_fixtures.json"
    if not fixtures_path.exists():
        logger.warning("No synthetic fixtures found at %s", fixtures_path)
        return

    logger.info("Loading labeled TEST DATA fixtures from %s...", fixtures_path)
    with open(fixtures_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    session = SessionLocal()
    try:
        q_repo = QuestionRepository(session)
        q_map = {}
        for q in data.get("questions", []):
            q_create = QuestionCreate(
                text=q["text"],
                target_market=q.get("target_market", "US"),
                target_location=q.get("target_location"),
                language=q.get("language", "en"),
                intent=q.get("intent", "informational"),
                persona=q.get("persona"),
                tags=q.get("tags", []),
                is_active=q.get("is_active", True),
            )
            entity, _ = q_repo.get_or_create(q_create)
            q_map[q["id"]] = entity.id

        ev_repo = EvidenceRepository(session)
        ev_map = {}
        for ev in data.get("evidence_artifacts", []):
            mapped_q_id = q_map.get(ev.get("question_id"))
            ev_create = EvidenceArtifactCreate(
                artifact_type=ev.get("artifact_type", "raw_text"),
                question_id=mapped_q_id,
                content=ev.get("content"),
                source_url=ev.get("source_url"),
                collected_by=ev.get("collected_by", "synthetic_test_generator"),
                content_hash=ev.get("content_hash"),
                metadata=ev.get("metadata", {}),
            )
            entity, _ = ev_repo.store_evidence(ev_create, allow_existing=True)
            ev_map[ev["id"]] = entity.id

        obs_repo = ObservationRepository(session)
        for obs in data.get("observations", []):
            mapped_q_id = q_map.get(obs.get("question_id"))
            if not mapped_q_id:
                continue
            mapped_ev_id = ev_map.get(obs.get("artifact_id"))
            obs_create = ObservationCreate(
                question_id=mapped_q_id,
                market=obs.get("market", "US"),
                location=obs.get("location"),
                provider=obs.get("provider", "other"),
                observation_type=obs.get("observation_type", "unknown"),
                raw_answer=obs.get("raw_answer"),
                artifact_id=mapped_ev_id,
                incubrix_mentioned=obs.get("incubrix_mentioned", "unknown"),
                incubrix_cited=obs.get("incubrix_cited", "unknown"),
                competitors_observed=obs.get("competitors_observed", []),
                quoted_domains=obs.get("quoted_domains", []),
                rank_position=obs.get("rank_position"),
                answer_box_present=obs.get("answer_box_present"),
                collection_status=obs.get("collection_status", "success"),
            )
            obs_repo.record_observation(
                obs_create,
                visibility_score=obs.get("visibility_score"),
                allow_existing=True,
            )

        audit_repo = AuditFindingRepository(session)
        for af in data.get("audit_findings", []):
            af_create = AuditFindingCreate(
                target_url=af["target_url"],
                audit_category=af["audit_category"],
                issue_code=af["issue_code"],
                severity=af.get("severity", "info"),
                status=af.get("status", "pass"),
                description=af["description"],
                recommendation=af.get("recommendation"),
                raw_metrics=af.get("raw_metrics", {}),
            )
            audit_repo.record_finding(af_create)

        content_repo = ContentRepository(session)
        for cb in data.get("content_briefs", []):
            mapped_q_id = q_map.get(cb.get("question_id"))
            cb_create = ContentBriefCreate(
                question_id=mapped_q_id,
                target_topic=cb["target_topic"],
                target_query=cb["target_query"],
                primary_intent=cb.get("primary_intent", "informational"),
                target_entities=cb.get("target_entities", []),
                required_sections=cb.get("required_sections", []),
                recommended_faqs=cb.get("recommended_faqs", []),
                target_word_count=cb.get("target_word_count", 1200),
                tone=cb.get("tone", "expert"),
                schema_type=cb.get("schema_type", "TechArticle"),
            )
            content_repo.create_brief(cb_create)

        logger.info("Successfully seeded synthetic test fixtures.")
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="IncuBrix Database Initializer")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed with synthetic test data fixtures (clearly labeled as TEST DATA)",
    )
    args = parser.parse_args()

    configure_logging("INFO")
    init_db()
    if args.seed:
        seed_synthetic_fixtures()


if __name__ == "__main__":
    main()
