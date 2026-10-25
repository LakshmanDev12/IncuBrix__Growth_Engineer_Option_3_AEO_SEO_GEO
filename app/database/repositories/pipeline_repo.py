"""Repository for Pipeline Runs."""

from typing import Optional

from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.database.models.pipeline import PipelineRunModel
from app.database.repositories.base import BaseRepository
from app.schemas.common import PipelineRunStatus
from app.schemas.pipeline import PipelineRunCreate


class PipelineRunRepository(BaseRepository[PipelineRunModel]):
    """Repository managing pipeline executions and telemetry."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, PipelineRunModel)

    def start_run(self, data: PipelineRunCreate) -> PipelineRunModel:
        """Initialize and record a new pipeline run."""
        entity = PipelineRunModel(
            pipeline_type=data.pipeline_type,
            status=PipelineRunStatus.RUNNING.value,
            total_items=data.total_items,
            processed_items=0,
            successful_items=0,
            failed_items=0,
            error_summary=None,
            parameters=data.parameters,
            started_at=utc_now(),
        )
        return self.create(entity)

    def complete_run(
        self,
        run_id: str,
        processed_items: int,
        successful_items: int,
        failed_items: int,
        error_summary: Optional[str] = None,
        status: Optional[str] = None,
        parameters: Optional[dict] = None,
    ) -> Optional[PipelineRunModel]:
        """Mark a pipeline run as completed, partial, or failed with optional execution telemetry."""
        run = self.get_by_id(run_id)
        if not run:
            return None

        run.processed_items = processed_items
        run.successful_items = successful_items
        run.failed_items = failed_items
        run.error_summary = error_summary

        if status:
            run.status = status
        else:
            if failed_items > 0 and successful_items == 0:
                run.status = PipelineRunStatus.FAILED.value
            elif failed_items > 0:
                run.status = PipelineRunStatus.PARTIAL.value
            else:
                run.status = PipelineRunStatus.COMPLETED.value

        if parameters is not None:
            updated_params = dict(run.parameters or {})
            updated_params.update(parameters)
            run.parameters = updated_params

        run.completed_at = utc_now()
        return self.update(run)
