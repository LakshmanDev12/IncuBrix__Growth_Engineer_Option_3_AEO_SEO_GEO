"""Pipeline Orchestrator for the IncuBrix Visibility Engine.

Integrates:
- Stage 1: Question Ingestion & Input Processing (with live review sample support)
- Stage 2: Measurement & Collection (Search and GEO AI collectors with bounded retries & provider failure recovery)
- Stage 3: Visibility Scoring & Analytics (via VisibilityMetricsCalculator)
- Stage 4: Technical SEO & AEO Auditing (via TechnicalAuditor)
- Stage 5: Content & Citation Generation (via ContentCitationEngine)
- Stage 6: Reports & Exports (via ReportGenerator for CSVs and weekly executive intelligence)

Supports:
- Complete run (`mode='complete'`) and Refresh run (`mode='refresh'`).
- Job status tracking, structured logs, duration metrics, idempotency, and cost accounting.
- Never reports success if required stages fail.
"""

from __future__ import annotations

import csv
import io
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.audit.technical_audit import TechnicalAuditor
from app.collectors.automated_collector import AutomatedCollector
from app.collectors.geo_collector import GEOCollector
from app.config import PROJECT_ROOT
from app.content.generator import ContentCitationEngine
from app.content.verified_knowledge import APPROVED_CREATOR_QUESTIONS
from app.database.base import utc_now
from app.database.models.question import QuestionModel
from app.database.repositories.audit_repo import AuditFindingRepository
from app.database.repositories.citation_repo import CitationRepository
from app.database.repositories.evidence_repo import EvidenceRepository
from app.database.repositories.observation_repo import ObservationRepository
from app.database.repositories.pipeline_repo import PipelineRunRepository
from app.database.repositories.question_repo import QuestionRepository
from app.engine.question_ingestion import QuestionIngestionEngine
from app.engine.report_generator import ReportGenerator
from app.engine.visibility_metrics import VisibilityMetricsCalculator
from app.logging_config import get_logger
from app.pipeline.cost_tracker import CostTracker
from app.pipeline.retry import execute_with_retry
from app.providers.ai_provider import get_ai_adapter
from app.providers.search_provider import SearchProvider
from app.schemas.common import PipelineRunStatus, ProviderType, ReviewStatus
from app.schemas.pipeline import (
    PipelineExecutionRequest,
    PipelineExecutionResponse,
    PipelineRunCreate,
    PipelineStageResult,
    PipelineStageStatus,
)
from app.schemas.questions import QuestionCreate

logger = get_logger("incubrix.pipeline")


class PipelineOrchestrator:
    """Production modular pipeline orchestrator coordinating all visibility engine modules."""

    REQUIRED_STAGES = {"ingestion", "collection", "scoring", "reporting"}
    DEFAULT_SAMPLE_PATH = PROJECT_ROOT / "data" / "live_review_sample.csv"

    def __init__(
        self,
        db: Session,
        cost_tracker: Optional[CostTracker] = None,
        max_retries: int = 2,
        retry_delay: float = 0.02,
        outputs_dir: Optional[Path] = None,
    ) -> None:
        self.db = db
        self.cost_tracker = cost_tracker or CostTracker()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.outputs_dir = outputs_dir

        # Repositories
        self.pipeline_repo = PipelineRunRepository(db)
        self.question_repo = QuestionRepository(db)
        self.observation_repo = ObservationRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.audit_repo = AuditFindingRepository(db)
        self.citation_repo = CitationRepository(db)

    def run(self, request: PipelineExecutionRequest) -> PipelineExecutionResponse:
        """Execute a complete or refresh pipeline run across engine modules."""
        start_time = datetime.now(timezone.utc).replace(tzinfo=None)
        perf_start = time.perf_counter()

        logger.info(
            "=== Starting IncuBrix Pipeline run [mode: %s, market: %s, retries: %d] ===",
            request.mode,
            request.market or "All",
            request.max_retries,
        )

        # 1. Initialize PipelineRun record in database
        run_record = self.pipeline_repo.start_run(
            PipelineRunCreate(
                pipeline_type=f"pipeline_{request.mode}",
                status=PipelineRunStatus.RUNNING,
                total_items=0,
                parameters={
                    "mode": request.mode,
                    "market": request.market,
                    "provider": request.provider,
                    "sample_input": request.sample_input,
                    "input_file": request.input_file,
                    "skip_audit": request.skip_audit,
                    "skip_content": request.skip_content,
                },
            )
        )

        stages: List[PipelineStageResult] = []
        target_questions: List[QuestionModel] = []
        error_messages: List[str] = []
        report_paths: Dict[str, str] = {}
        total_items_count = 0
        successful_items_count = 0
        failed_items_count = 0

        try:
            # -----------------------------------------------------------------
            # Stage 1: Question Ingestion & Input Processing
            # -----------------------------------------------------------------
            stage_1 = self._run_ingestion_stage(request)
            stages.append(stage_1)
            target_questions = stage_1.details.get("questions", [])
            total_items_count = len(target_questions)

            if stage_1.status == PipelineStageStatus.FAILED:
                error_messages.append(f"Ingestion stage failed: {stage_1.error_message}")
                raise RuntimeError(f"Ingestion failed: {stage_1.error_message}")

            # -----------------------------------------------------------------
            # Stage 2: Measurement & Collection
            # -----------------------------------------------------------------
            stage_2 = self._run_collection_stage(request, target_questions)
            stages.append(stage_2)
            successful_items_count += stage_2.items_succeeded
            failed_items_count += stage_2.items_failed

            if stage_2.status == PipelineStageStatus.FAILED:
                error_messages.append(f"Collection stage failed: {stage_2.error_message}")
                raise RuntimeError(f"Collection failed: {stage_2.error_message}")

            # -----------------------------------------------------------------
            # Stage 3: Visibility Scoring & Analytics
            # -----------------------------------------------------------------
            stage_3 = self._run_scoring_stage(request)
            stages.append(stage_3)

            if stage_3.status == PipelineStageStatus.FAILED:
                error_messages.append(f"Scoring stage failed: {stage_3.error_message}")
                raise RuntimeError(f"Scoring failed: {stage_3.error_message}")

            # -----------------------------------------------------------------
            # Stage 4: Technical SEO & AEO Audit
            # -----------------------------------------------------------------
            stage_4 = self._run_audit_stage(request)
            stages.append(stage_4)

            # -----------------------------------------------------------------
            # Stage 5: Content & Citation Generation
            # -----------------------------------------------------------------
            stage_5 = self._run_content_stage(request)
            stages.append(stage_5)

            # -----------------------------------------------------------------
            # Stage 6: Reports & Exports
            # -----------------------------------------------------------------
            stage_6 = self._run_reporting_stage(request)
            stages.append(stage_6)
            report_paths = stage_6.details.get("paths", {})

            if stage_6.status == PipelineStageStatus.FAILED:
                error_messages.append(f"Reporting stage failed: {stage_6.error_message}")
                raise RuntimeError(f"Reporting failed: {stage_6.error_message}")

        except Exception as exc:
            logger.error("Catastrophic error in pipeline execution: %s", exc)
            if not error_messages:
                error_messages.append(str(exc))

        # ---------------------------------------------------------------------
        # Finalize Pipeline Run & Evaluate Overall Status
        # ---------------------------------------------------------------------
        perf_end = time.perf_counter()
        total_duration = round(perf_end - perf_start, 3)
        completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        # Check required stage health: if any required stage failed, run fails
        has_required_failure = any(
            s.stage_name in self.REQUIRED_STAGES and s.status == PipelineStageStatus.FAILED
            for s in stages
        )

        has_any_partial = any(
            s.status in (PipelineStageStatus.PARTIAL, PipelineStageStatus.FAILED)
            for s in stages
        )

        if has_required_failure or (error_messages and successful_items_count == 0):
            overall_status = PipelineRunStatus.FAILED.value
        elif has_any_partial or failed_items_count > 0:
            overall_status = PipelineRunStatus.PARTIAL.value
        else:
            overall_status = PipelineRunStatus.COMPLETED.value

        cost_summary = self.cost_tracker.get_summary()
        error_summary_str = "; ".join(error_messages) if error_messages else None

        # Clean stage details for JSON serialization (remove ORM models)
        serialized_stages = []
        for s in stages:
            s_dict = s.model_dump()
            if "questions" in s_dict.get("details", {}):
                s_dict["details"]["questions_count"] = len(s_dict["details"].pop("questions"))
            serialized_stages.append(s_dict)

        # Persist completion telemetry to database
        self.pipeline_repo.complete_run(
            run_id=run_record.id,
            processed_items=total_items_count,
            successful_items=successful_items_count,
            failed_items=failed_items_count,
            error_summary=error_summary_str,
            status=overall_status,
            parameters={
                "duration_seconds": total_duration,
                "stages": serialized_stages,
                "cost_summary": cost_summary.model_dump(),
                "report_paths": report_paths,
            },
        )

        logger.info(
            "=== Pipeline run completed [status: %s, duration: %.2fs, items: %d, cost: $%.4f] ===",
            overall_status,
            total_duration,
            total_items_count,
            cost_summary.total_cost_usd,
        )

        # Remove ORM models from the stage objects in the returned response
        for s in stages:
            if "questions" in s.details:
                s.details["questions_count"] = len(s.details.pop("questions"))

        return PipelineExecutionResponse(
            run_id=run_record.id,
            pipeline_type=f"pipeline_{request.mode}",
            status=overall_status,
            started_at=start_time,
            completed_at=completed_at,
            total_duration_seconds=total_duration,
            stages=stages,
            cost_summary=cost_summary,
            total_items=total_items_count,
            successful_items=successful_items_count,
            failed_items=failed_items_count,
            error_summary=error_summary_str,
            report_paths=report_paths,
        )

    # -------------------------------------------------------------------------
    # Stage Implementation Details
    # -------------------------------------------------------------------------

    def _run_ingestion_stage(self, request: PipelineExecutionRequest) -> PipelineStageResult:
        """Stage 1: Question Ingestion and Target Loading."""
        stage_name = "ingestion"
        t0 = time.perf_counter()
        logger.info("[Stage 1/6: Question Ingestion] Initiating input loading...")

        questions: List[QuestionModel] = []
        ingested_count = 0
        failed_count = 0

        try:
            # 1. Sample input set for live review
            if request.sample_input:
                sample_file = self.DEFAULT_SAMPLE_PATH
                if sample_file.exists():
                    csv_text = sample_file.read_text(encoding="utf-8")
                    engine = QuestionIngestionEngine(self.question_repo)
                    batch_res = engine.import_from_csv(csv_text, default_review_status=ReviewStatus.APPROVED)
                    ingested_count = batch_res.imported_count
                    failed_count = batch_res.invalid_count
                    # Load specifically the sample questions
                    parsed_texts = [row.get("text") for row in csv.DictReader(io.StringIO(csv_text)) if row.get("text")]
                    questions = [self.question_repo.get_by_text(t) for t in parsed_texts if self.question_repo.get_by_text(t)]
                    logger.info("Targeting %d questions from live review sample.", len(questions))
                else:
                    logger.warning("Sample input file %s not found, loading defaults.", sample_file)

            # 2. User-provided CSV input file
            elif request.input_file:
                input_path = Path(request.input_file)
                if not input_path.exists():
                    return PipelineStageResult(
                        stage_name=stage_name,
                        status=PipelineStageStatus.FAILED,
                        duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                        error_message=f"Input file '{request.input_file}' not found.",
                    )
                csv_text = input_path.read_text(encoding="utf-8")
                engine = QuestionIngestionEngine(self.question_repo)
                batch_res = engine.import_from_csv(csv_text, default_review_status=ReviewStatus.APPROVED)
                ingested_count = batch_res.imported_count
                failed_count = batch_res.invalid_count
                # Load specifically the input questions
                parsed_texts = [row.get("text") for row in csv.DictReader(io.StringIO(csv_text)) if row.get("text")]
                questions = [self.question_repo.get_by_text(t) for t in parsed_texts if self.question_repo.get_by_text(t)]
                logger.info("Targeting %d questions from provided input file.", len(questions))

            # 3. If in refresh mode or no questions yet loaded, load active questions from DB
            if not questions:
                questions = self.question_repo.filter_questions(
                    market=request.market,
                    is_active=True,
                    limit=100,
                )

            # 4. If zero questions found in database, seed from approved creator questions
            if not questions:
                logger.info("No active questions in database. Seeding approved creator questions...")
                for q_blueprint in APPROVED_CREATOR_QUESTIONS:
                    q_text = q_blueprint.get("text") or q_blueprint.get("question") or ""
                    q_intent = q_blueprint.get("intent") or "informational"
                    q_entity, _ = self.question_repo.get_or_create(
                        QuestionCreate(
                            text=q_text,
                            target_audience="Creators",
                            creator_intent=q_intent,
                            target_market="US",
                            review_status=ReviewStatus.APPROVED,
                        )
                    )
                    questions.append(q_entity)
                ingested_count += len(questions)

            # 5. Auto-approve inputs if requested
            if request.auto_approve_inputs:
                for q in questions:
                    if q.review_status != ReviewStatus.APPROVED.value:
                        self.question_repo.update_review_status(q.id, ReviewStatus.APPROVED.value)

            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.COMPLETED,
                duration_ms=duration_ms,
                items_processed=len(questions),
                items_succeeded=len(questions),
                items_failed=failed_count,
                details={
                    "questions": questions,
                    "ingested_count": ingested_count,
                    "target_questions_count": len(questions),
                },
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.error("Stage 1 (Ingestion) failed: %s", exc)
            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.FAILED,
                duration_ms=duration_ms,
                error_message=str(exc),
            )

    def _run_collection_stage(
        self,
        request: PipelineExecutionRequest,
        questions: List[QuestionModel],
    ) -> PipelineStageResult:
        """Stage 2: Measurement & Collection with bounded retries and provider failure recovery."""
        stage_name = "collection"
        t0 = time.perf_counter()
        logger.info("[Stage 2/6: Collection] Running observations across providers for %d questions...", len(questions))

        if not questions:
            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.COMPLETED,
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                details={"observations_recorded": 0, "notice": "No questions to collect"},
            )

        items_processed = 0
        items_succeeded = 0
        items_failed = 0
        stage_cost = 0.0

        # Instantiate collectors
        search_provider = SearchProvider()
        automated_collector = AutomatedCollector(
            provider=search_provider,
            evidence_repo=self.evidence_repo,
            observation_repo=self.observation_repo,
            citation_repo=self.citation_repo,
        )

        geo_collector = GEOCollector(
            question_repo=self.question_repo,
            evidence_repo=self.evidence_repo,
            observation_repo=self.observation_repo,
            citation_repo=self.citation_repo,
        )

        for q in questions:
            # 1. Search Engine Observation (Google SERP)
            if not request.provider or request.provider in ("google_search", "search_engine"):
                items_processed += 1
                try:
                    obs, attempts, err = execute_with_retry(
                        automated_collector.collect,
                        question=q,
                        market=request.market,
                        max_retries=self.max_retries,
                        base_delay=self.retry_delay,
                        operation_name=f"GoogleSearch:{q.id[:8]}",
                    )
                    cost = self.cost_tracker.record_call(
                        provider="google_search",
                        operation="search_serp",
                        stage="collection",
                    )
                    stage_cost += cost
                    items_succeeded += 1
                except Exception as exc:
                    items_failed += 1
                    logger.warning("Search observation failed for question %s: %s", q.id, exc)

            # 2. Generative AI Engine Observation (Perplexity)
            if not request.provider or request.provider in ("perplexity", "ai_assistant"):
                items_processed += 1
                try:
                    obs, attempts, err = execute_with_retry(
                        geo_collector.collect,
                        question=q,
                        assistant=ProviderType.PERPLEXITY,
                        market=request.market,
                        max_retries=self.max_retries,
                        base_delay=self.retry_delay,
                        operation_name=f"PerplexityGEO:{q.id[:8]}",
                    )
                    cost = self.cost_tracker.record_call(
                        provider="perplexity",
                        operation="geo_synthesis",
                        stage="collection",
                    )
                    stage_cost += cost
                    items_succeeded += 1
                except Exception as exc:
                    items_failed += 1
                    logger.warning("GEO observation failed for question %s: %s", q.id, exc)

        duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        stage_status = (
            PipelineStageStatus.COMPLETED
            if items_failed == 0
            else (PipelineStageStatus.PARTIAL if items_succeeded > 0 else PipelineStageStatus.FAILED)
        )

        return PipelineStageResult(
            stage_name=stage_name,
            status=stage_status,
            duration_ms=duration_ms,
            items_processed=items_processed,
            items_succeeded=items_succeeded,
            items_failed=items_failed,
            cost_usd=round(stage_cost, 5),
            details={
                "items_processed": items_processed,
                "items_succeeded": items_succeeded,
                "items_failed": items_failed,
            },
        )

    def _run_scoring_stage(self, request: PipelineExecutionRequest) -> PipelineStageResult:
        """Stage 3: Visibility Scoring and Comparative Analytics."""
        stage_name = "scoring"
        t0 = time.perf_counter()
        logger.info("[Stage 3/6: Scoring] Calculating visibility metrics...")

        try:
            # Query valid observations
            observations = self.observation_repo.filter_observations(
                market=request.market,
                limit=500,
            )

            metrics = VisibilityMetricsCalculator.calculate_metrics(
                observations=observations,
                deduplicate=True,
            )

            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.COMPLETED,
                duration_ms=duration_ms,
                items_processed=len(observations),
                items_succeeded=len(observations),
                items_failed=0,
                cost_usd=0.0,
                details={
                    "total_observations_evaluated": metrics.valid_evaluated_observations,
                    "mean_visibility_score": metrics.average_visibility_score,
                    "top_10_rate_pct": metrics.seo_metrics.top_10_ranking_rate_pct,
                    "ai_mention_rate_pct": metrics.geo_metrics.ai_mention_rate_pct,
                    "ai_citation_rate_pct": metrics.geo_metrics.ai_citation_rate_pct,
                },
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.error("Stage 3 (Scoring) failed: %s", exc)
            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.FAILED,
                duration_ms=duration_ms,
                error_message=str(exc),
            )

    def _run_audit_stage(self, request: PipelineExecutionRequest) -> PipelineStageResult:
        """Stage 4: Technical SEO/AEO Audit."""
        stage_name = "audit"
        t0 = time.perf_counter()

        if request.skip_audit:
            logger.info("[Stage 4/6: Audit] Skipped per configuration.")
            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.SKIPPED,
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                details={"skipped": True},
            )

        logger.info("[Stage 4/6: Audit] Auditing target URL: %s", request.target_audit_url)
        try:
            audit_report = TechnicalAuditor.audit_page(
                target_url=request.target_audit_url,
                allow_polite_fetch=False,
            )
            self.audit_repo.record_batch(audit_report.findings)

            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.COMPLETED,
                duration_ms=duration_ms,
                items_processed=len(audit_report.findings),
                items_succeeded=len(audit_report.findings),
                items_failed=0,
                cost_usd=0.0,
                details={
                    "health_score": audit_report.health_score,
                    "total_findings": len(audit_report.findings),
                },
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.warning("Stage 4 (Audit) encountered non-fatal error: %s", exc)
            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.PARTIAL,
                duration_ms=duration_ms,
                items_failed=1,
                error_message=str(exc),
            )

    def _run_content_stage(self, request: PipelineExecutionRequest) -> PipelineStageResult:
        """Stage 5: Content Drafts & Citation Opportunities."""
        stage_name = "content"
        t0 = time.perf_counter()

        if request.skip_content or request.mode == "refresh":
            logger.info("[Stage 5/6: Content] Skipped for refresh or per configuration.")
            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.SKIPPED,
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
                details={"skipped": True},
            )

        logger.info("[Stage 5/6: Content] Seeding citations and generating drafts...")
        try:
            # Seed 30 specific real third-party citation opportunities
            seeded_targets = ContentCitationEngine.seed_thirty_citation_opportunities(self.db)

            # Generate publish-ready page drafts
            draft_results = ContentCitationEngine.generate_all_ten_drafts(
                session=self.db,
                use_llm=request.use_llm,
                limit=request.content_limit,
            )

            stage_cost = 0.0
            if request.use_llm:
                stage_cost = self.cost_tracker.record_call(
                    provider="content_generation_llm",
                    operation="draft_generation",
                    stage="content",
                ) * len(draft_results)

            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.COMPLETED,
                duration_ms=duration_ms,
                items_processed=len(draft_results) + len(seeded_targets),
                items_succeeded=len(draft_results) + len(seeded_targets),
                items_failed=0,
                cost_usd=round(stage_cost, 5),
                details={
                    "drafts_generated": len(draft_results),
                    "citation_targets_seeded": len(seeded_targets),
                },
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.warning("Stage 5 (Content) encountered error: %s", exc)
            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.PARTIAL,
                duration_ms=duration_ms,
                items_failed=1,
                error_message=str(exc),
            )

    def _run_reporting_stage(self, request: PipelineExecutionRequest) -> PipelineStageResult:
        """Stage 6: Reports & RFC 4180 CSV Exports."""
        stage_name = "reporting"
        t0 = time.perf_counter()
        logger.info("[Stage 6/6: Reporting] Exporting CSVs and generating executive weekly brief...")

        try:
            if self.outputs_dir:
                outputs_dir = self.outputs_dir
            elif os.environ.get("PYTEST_CURRENT_TEST"):
                outputs_dir = PROJECT_ROOT / "outputs" / ".test_tmp"
            else:
                outputs_dir = PROJECT_ROOT / "outputs"
            outputs_dir.mkdir(parents=True, exist_ok=True)

            # 1. Export visibility.csv
            vis_csv = ReportGenerator.export_visibility_csv(self.db, market=request.market)
            vis_path = outputs_dir / "visibility.csv"
            if len(vis_csv.strip().splitlines()) > 1 or not vis_path.exists():
                vis_path.write_text(vis_csv, encoding="utf-8")

            # 2. Export technical_fixes.csv
            tech_csv = ReportGenerator.export_technical_fixes_csv(self.db)
            tech_path = outputs_dir / "technical_fixes.csv"
            if len(tech_csv.strip().splitlines()) > 1 or not tech_path.exists():
                tech_path.write_text(tech_csv, encoding="utf-8")

            # 3. Export citation_targets.csv
            cite_csv = ReportGenerator.export_citation_targets_csv(self.db)
            cite_path = outputs_dir / "citation_targets.csv"
            if len(cite_csv.strip().splitlines()) > 1 or not cite_path.exists():
                cite_path.write_text(cite_csv, encoding="utf-8")

            # 4. Generate Weekly Executive Intelligence Report
            weekly_rep = ReportGenerator.generate_weekly_report(self.db, save_to_disk=True)

            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            paths = {
                "visibility_csv": str(vis_path),
                "technical_fixes_csv": str(tech_path),
                "citation_targets_csv": str(cite_path),
            }

            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.COMPLETED,
                duration_ms=duration_ms,
                items_processed=4,
                items_succeeded=4,
                items_failed=0,
                cost_usd=0.0,
                details={
                    "paths": paths,
                    "weekly_report_title": weekly_rep.report_title,
                },
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.error("Stage 6 (Reporting) failed: %s", exc)
            return PipelineStageResult(
                stage_name=stage_name,
                status=PipelineStageStatus.FAILED,
                duration_ms=duration_ms,
                error_message=str(exc),
            )
