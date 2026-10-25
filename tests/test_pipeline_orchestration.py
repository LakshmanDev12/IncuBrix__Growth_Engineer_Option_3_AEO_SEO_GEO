"""Integration tests for Module 9: Pipeline Orchestration.

Tests verify:
- Complete end-to-end run across ingestion, collection, scoring, audit, content, and reporting.
- Refresh run for new measurements without re-running content drafts.
- Bounded retries on transient network/timeout errors with error discrimination.
- Provider failure recovery (pipeline continues gracefully when individual provider queries fail).
- Idempotency (repeated runs do not create duplicate observation fingerprints).
- Cost tracking (financial telemetry accurately estimates/computes API costs).
- Small new input set for live review (processes data/live_review_sample.csv).
- Strict non-success reporting if required stages fail (marked FAILED, never COMPLETED).
- CLI commands execution (complete and refresh subcommands, exit codes).
- REST API endpoints (/v1/pipeline/run, /v1/pipeline/refresh, /v1/pipeline/cost-rates).
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models.observation import ObservationModel
from app.database.models.pipeline import PipelineRunModel
from app.database.models.question import QuestionModel
from app.database.repositories.pipeline_repo import PipelineRunRepository
from app.database.repositories.question_repo import QuestionRepository
from app.pipeline.cli import main as cli_main
from app.pipeline.cost_tracker import RATE_CARDS, CostTracker
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.retry import execute_with_retry, is_transient_error
from app.schemas.common import (
    CollectionStatus,
    ObservationType,
    PipelineRunStatus,
    ProviderType,
    ReviewStatus,
)
from app.schemas.observations import ObservationCreate
from app.schemas.pipeline import (
    PipelineExecutionRequest,
    PipelineExecutionResponse,
    PipelineStageStatus,
)
from app.schemas.questions import QuestionCreate


# ==============================================================================
# 1. Bounded Retries & Error Discrimination Tests
# ==============================================================================


def test_retry_transient_error_eventual_success():
    """Verify bounded retry recovers from transient errors on subsequent attempts."""
    mock_fn = MagicMock()
    # Attempt 1: TimeoutException (transient), Attempt 2: Success
    mock_fn.side_effect = [httpx.TimeoutException("Connection timed out"), {"status": "ok"}]

    result, attempts, err = execute_with_retry(
        mock_fn,
        max_retries=2,
        base_delay=0.001,
        operation_name="test_timeout",
    )

    assert result == {"status": "ok"}
    assert attempts == 2
    assert err is None
    assert mock_fn.call_count == 2


def test_retry_permanent_error_fails_immediately():
    """Verify bounded retry does not loop on permanent non-transient errors."""
    mock_fn = MagicMock()
    mock_fn.side_effect = ValueError("Invalid parameter value")

    with pytest.raises(ValueError, match="Invalid parameter value"):
        execute_with_retry(
            mock_fn,
            max_retries=3,
            base_delay=0.001,
            operation_name="test_value_error",
        )

    # Should fail on first attempt without retrying
    assert mock_fn.call_count == 1


def test_retry_exhausted_raises_last_error():
    """Verify bounded retry raises exception once max_retries are exhausted."""
    mock_fn = MagicMock()
    mock_fn.side_effect = httpx.ConnectError("Connection refused")

    with pytest.raises(httpx.ConnectError):
        execute_with_retry(
            mock_fn,
            max_retries=2,
            base_delay=0.001,
            operation_name="test_connect_error",
        )

    assert mock_fn.call_count == 3  # Initial + 2 retries


def test_is_transient_error_classification():
    """Verify transient error discriminator distinguishes recoverable from permanent errors."""
    assert is_transient_error(httpx.TimeoutException("timeout")) is True
    assert is_transient_error(httpx.ConnectError("refused")) is True
    assert is_transient_error(ConnectionError("network reset")) is True

    # HTTP Status Errors
    req = httpx.Request("GET", "https://api.example.com")
    resp_429 = httpx.Response(429, request=req)
    assert is_transient_error(httpx.HTTPStatusError("Rate limited", request=req, response=resp_429)) is True

    resp_401 = httpx.Response(401, request=req)
    assert is_transient_error(httpx.HTTPStatusError("Unauthorized", request=req, response=resp_401)) is False

    assert is_transient_error(ValueError("bad arg")) is False


# ==============================================================================
# 2. Cost Tracking Telemetry Tests
# ==============================================================================


def test_cost_tracker_calculation_and_rate_cards():
    """Verify cost tracker computes estimated costs based on published rate cards."""
    tracker = CostTracker()

    c1 = tracker.record_call(provider="google_search", operation="search_serp", stage="collection")
    assert c1 == RATE_CARDS["google_search"]["unit_cost_usd"]

    c2 = tracker.record_call(provider="perplexity", operation="geo_synthesis", stage="collection")
    assert c2 == RATE_CARDS["perplexity"]["unit_cost_usd"]

    c3 = tracker.record_call(
        provider="custom_api",
        operation="custom_op",
        stage="collection",
        actual_cost_usd=0.025,
    )
    assert c3 == 0.025

    summary = tracker.get_summary()
    assert summary.total_calls == 3
    assert summary.total_cost_usd == round(c1 + c2 + 0.025, 5)
    assert "google_search" in summary.by_provider
    assert "perplexity" in summary.by_provider
    assert "collection" in summary.by_stage
    assert len(summary.items) == 3


# ==============================================================================
# 3. Complete End-to-End Pipeline Execution Tests
# ==============================================================================


def test_pipeline_complete_run_end_to_end(db_session: Session):
    """Verify a complete pipeline run executes all 6 stages and persists results."""
    orchestrator = PipelineOrchestrator(
        db=db_session,
        cost_tracker=CostTracker(),
        max_retries=1,
        retry_delay=0.001,
    )

    request = PipelineExecutionRequest(
        mode="complete",
        market="US",
        content_limit=2,  # Fast run for tests
        max_retries=1,
        skip_audit=False,
        skip_content=False,
    )

    response = orchestrator.run(request)

    assert isinstance(response, PipelineExecutionResponse)
    assert response.status in (PipelineRunStatus.COMPLETED.value, PipelineRunStatus.PARTIAL.value)
    assert response.total_duration_seconds > 0.0
    assert len(response.stages) == 6

    stage_names = [s.stage_name for s in response.stages]
    assert stage_names == ["ingestion", "collection", "scoring", "audit", "content", "reporting"]

    # Verify Stage 1: Ingestion
    ingestion_stage = response.stages[0]
    assert ingestion_stage.status == PipelineStageStatus.COMPLETED
    assert ingestion_stage.items_processed > 0

    # Verify Stage 2: Collection
    collection_stage = response.stages[1]
    assert collection_stage.status in (PipelineStageStatus.COMPLETED, PipelineStageStatus.PARTIAL)
    assert collection_stage.items_processed > 0

    # Verify Stage 3: Scoring
    scoring_stage = response.stages[2]
    assert scoring_stage.status == PipelineStageStatus.COMPLETED

    # Verify Stage 4: Audit
    audit_stage = response.stages[3]
    assert audit_stage.status == PipelineStageStatus.COMPLETED
    assert "health_score" in audit_stage.details

    # Verify Stage 5: Content
    content_stage = response.stages[4]
    assert content_stage.status == PipelineStageStatus.COMPLETED
    assert content_stage.details["drafts_generated"] == 2
    assert content_stage.details["citation_targets_seeded"] == 30

    # Verify Stage 6: Reporting
    reporting_stage = response.stages[5]
    assert reporting_stage.status == PipelineStageStatus.COMPLETED
    assert "visibility_csv" in reporting_stage.details["paths"]

    # Verify database persistence of the PipelineRunModel
    run_repo = PipelineRunRepository(db_session)
    stored_run = run_repo.get_by_id(response.run_id)
    assert stored_run is not None
    assert stored_run.status == response.status
    assert "stages" in stored_run.parameters
    assert "cost_summary" in stored_run.parameters


# ==============================================================================
# 4. Refresh Pipeline Execution Tests
# ==============================================================================


def test_pipeline_refresh_run(db_session: Session):
    """Verify refresh run re-measures and updates scoring/reports while skipping content drafts."""
    # Seed an approved question
    q_repo = QuestionRepository(db_session)
    q = q_repo.create_strict(QuestionCreate(
        text="How do creators optimize visibility on ChatGPT search?",
        target_audience="Creators",
        creator_intent="AEO Optimization",
        target_market="US",
        review_status=ReviewStatus.APPROVED,
    ))

    orchestrator = PipelineOrchestrator(
        db=db_session,
        cost_tracker=CostTracker(),
        max_retries=1,
        retry_delay=0.001,
    )

    request = PipelineExecutionRequest(
        mode="refresh",
        market="US",
        skip_audit=True,
    )

    response = orchestrator.run(request)

    assert response.status in (PipelineRunStatus.COMPLETED.value, PipelineRunStatus.PARTIAL.value)
    stage_statuses = {s.stage_name: s.status for s in response.stages}

    assert stage_statuses["ingestion"] == PipelineStageStatus.COMPLETED
    assert stage_statuses["collection"] in (PipelineStageStatus.COMPLETED, PipelineStageStatus.PARTIAL)
    assert stage_statuses["scoring"] == PipelineStageStatus.COMPLETED
    assert stage_statuses["audit"] == PipelineStageStatus.SKIPPED
    assert stage_statuses["content"] == PipelineStageStatus.SKIPPED
    assert stage_statuses["reporting"] == PipelineStageStatus.COMPLETED


# ==============================================================================
# 5. Idempotency Tests
# ==============================================================================


def test_pipeline_idempotency_daily_fingerprint(db_session: Session):
    """Verify executing the pipeline twice on the same day reuses observation fingerprints without duplication."""
    q_repo = QuestionRepository(db_session)
    q = q_repo.create_strict(QuestionCreate(
        text="What are the best AI B-roll matching tools for creators?",
        target_audience="Video Creators",
        creator_intent="Tool Comparison",
        target_market="US",
        review_status=ReviewStatus.APPROVED,
    ))

    orchestrator = PipelineOrchestrator(
        db=db_session,
        max_retries=1,
        retry_delay=0.001,
    )

    req = PipelineExecutionRequest(
        mode="refresh",
        market="US",
        skip_audit=True,
    )

    # First run
    resp1 = orchestrator.run(req)
    obs_count_1 = db_session.query(ObservationModel).count()
    assert obs_count_1 > 0

    # Second run on same day
    resp2 = orchestrator.run(req)
    obs_count_2 = db_session.query(ObservationModel).count()

    # Fingerprints ensure count remains identical without duplicate key crashes
    assert obs_count_2 == obs_count_1


# ==============================================================================
# 6. Provider Failure Recovery Tests
# ==============================================================================


def test_pipeline_provider_failure_recovery(db_session: Session):
    """Verify pipeline continues and records stage telemetry when a provider fails."""
    q_repo = QuestionRepository(db_session)
    q = q_repo.create_strict(QuestionCreate(
        text="Can creators monetize automated video editing workflows?",
        target_audience="Creators",
        creator_intent="Monetization",
        target_market="US",
        review_status=ReviewStatus.APPROVED,
    ))

    orchestrator = PipelineOrchestrator(
        db=db_session,
        max_retries=1,
        retry_delay=0.001,
    )

    # Patch SearchProvider.execute_query to raise an unhandled exception
    with patch("app.providers.search_provider.SearchProvider.execute_query") as mock_exec:
        mock_exec.side_effect = RuntimeError("External Google API simulated crash")

        request = PipelineExecutionRequest(
            mode="complete",
            market="US",
            provider="google_search",
            skip_audit=True,
            skip_content=True,
        )

        response = orchestrator.run(request)

        # Pipeline must not crash; stage 2 tracks items_failed
        assert response is not None
        collection_stage = next(s for s in response.stages if s.stage_name == "collection")
        assert collection_stage.items_failed > 0
        assert collection_stage.status in (PipelineStageStatus.PARTIAL, PipelineStageStatus.FAILED)


# ==============================================================================
# 7. Strict Non-Success on Required Stage Failure Tests
# ==============================================================================


def test_pipeline_required_stage_failure_marks_run_failed(db_session: Session):
    """Verify pipeline does not report success if a required stage encounters a fatal error."""
    orchestrator = PipelineOrchestrator(
        db=db_session,
        max_retries=1,
        retry_delay=0.001,
    )

    # Patch Scoring stage to fail catastrophically
    with patch(
        "app.engine.visibility_metrics.VisibilityMetricsCalculator.calculate_metrics"
    ) as mock_metrics:
        mock_metrics.side_effect = RuntimeError("Fatal scoring computation crash")

        request = PipelineExecutionRequest(
            mode="complete",
            skip_audit=True,
            skip_content=True,
        )

        response = orchestrator.run(request)

        # Must be marked FAILED (never COMPLETED)
        assert response.status == PipelineRunStatus.FAILED.value
        scoring_stage = next(s for s in response.stages if s.stage_name == "scoring")
        assert scoring_stage.status == PipelineStageStatus.FAILED
        assert "Fatal scoring computation crash" in (response.error_summary or "")

        # Verify database record also marked as failed
        run_repo = PipelineRunRepository(db_session)
        stored_run = run_repo.get_by_id(response.run_id)
        assert stored_run.status == PipelineRunStatus.FAILED.value


# ==============================================================================
# 8. Small New Input Set for Live Review Tests
# ==============================================================================


def test_pipeline_sample_input_set_live_review(db_session: Session, tmp_path: Path):
    """Verify pipeline ingests and executes the live review sample input set."""
    # Create sample CSV
    sample_csv = tmp_path / "test_sample.csv"
    sample_csv.write_text(
        'text,target_audience,creator_intent,target_market,source_platform,source_url\n'
        '"How do creators optimize visibility on ChatGPT search?",Creators,AEO Optimization,US,YouTube,https://youtube.com/watch?v=sample-1\n'
        '"What are the best AI B-roll matching tools in 2026?",Video Creators,Tool Comparison,US,Reddit,https://reddit.com/r/sample-2\n',
        encoding="utf-8",
    )

    orchestrator = PipelineOrchestrator(
        db=db_session,
        max_retries=1,
        retry_delay=0.001,
    )

    request = PipelineExecutionRequest(
        mode="complete",
        input_file=str(sample_csv),
        content_limit=2,
        skip_audit=True,
    )

    response = orchestrator.run(request)

    assert response.status in (PipelineRunStatus.COMPLETED.value, PipelineRunStatus.PARTIAL.value)
    ingestion_stage = next(s for s in response.stages if s.stage_name == "ingestion")
    assert ingestion_stage.status == PipelineStageStatus.COMPLETED
    assert ingestion_stage.details["ingested_count"] >= 2

    # Questions should be stored in database and marked approved
    q_repo = QuestionRepository(db_session)
    q1 = q_repo.get_by_text("How do creators optimize visibility on ChatGPT search?")
    assert q1 is not None
    assert q1.review_status == ReviewStatus.APPROVED.value


# ==============================================================================
# 9. CLI Commands Tests
# ==============================================================================


def test_cli_complete_and_refresh_commands(db_session: Session, monkeypatch):
    """Verify CLI complete and refresh commands execute with exit code 0."""
    # Monkeypatch SessionLocal in CLI to use in-memory db_session
    from app.database import session as db_session_module
    monkeypatch.setattr(db_session_module, "SessionLocal", lambda: db_session)

    # 1. Test complete run with fast flags
    ret_complete = cli_main(["complete", "--skip-audit", "--skip-content", "--max-retries", "1"])
    assert ret_complete == 0

    # 2. Test refresh run
    ret_refresh = cli_main(["refresh", "--max-retries", "1"])
    assert ret_refresh == 0


def test_cli_failing_run_returns_exit_code_1(db_session: Session, monkeypatch):
    """Verify CLI returns exit code 1 if a required stage fails."""
    from app.database import session as db_session_module
    monkeypatch.setattr(db_session_module, "SessionLocal", lambda: db_session)

    # Pass nonexistent input file so ingestion stage fails
    ret = cli_main(["complete", "--input-file", "nonexistent_file_path_123.csv"])
    assert ret == 1


# ==============================================================================
# 10. REST API Endpoints Tests
# ==============================================================================


def test_api_pipeline_run_endpoint(client: TestClient, db_session: Session):
    """Test POST /v1/pipeline/run endpoint."""
    payload = {
        "mode": "complete",
        "market": "US",
        "skip_audit": True,
        "skip_content": True,
        "max_retries": 1,
    }
    resp = client.post("/v1/pipeline/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert "status" in data
    assert "stages" in data
    assert "cost_summary" in data
    assert len(data["stages"]) == 6


def test_api_pipeline_refresh_endpoint(client: TestClient, db_session: Session):
    """Test POST /v1/pipeline/refresh endpoint."""
    resp = client.post("/v1/pipeline/refresh?market=US")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pipeline_type"] == "pipeline_refresh"
    assert "run_id" in data


def test_api_pipeline_cost_rates(client: TestClient):
    """Test GET /v1/pipeline/cost-rates endpoint."""
    resp = client.get("/v1/pipeline/cost-rates")
    assert resp.status_code == 200
    rates = resp.json()
    assert "google_search" in rates
    assert "perplexity" in rates
    assert "unit_cost_usd" in rates["google_search"]


def test_api_pipeline_runs_lifecycle(client: TestClient, db_session: Session):
    """Test GET /v1/pipeline/runs and GET /v1/pipeline/runs/{id}."""
    # Create a pipeline run
    create_resp = client.post(
        "/v1/pipeline/runs",
        json={"pipeline_type": "pipeline_test", "total_items": 10},
    )
    assert create_resp.status_code == 201
    created_id = create_resp.json()["id"]

    # List runs
    list_resp = client.get("/v1/pipeline/runs")
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert isinstance(runs, list)
    assert len(runs) >= 1

    # Fetch by ID
    get_resp = client.get(f"/v1/pipeline/runs/{created_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == created_id
