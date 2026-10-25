"""Repository for technical audit findings."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.audit import AuditFindingModel
from app.database.repositories.base import BaseRepository
from app.schemas.audit import AuditFindingCreate


class AuditFindingRepository(BaseRepository[AuditFindingModel]):
    """Repository managing Technical SEO/AEO Audit Findings."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, AuditFindingModel)

    def record_finding(self, data: AuditFindingCreate) -> AuditFindingModel:
        """Record an audit finding."""
        val_status = (
            data.validation_status.value
            if hasattr(data.validation_status, "value")
            else str(data.validation_status)
        )
        entity = AuditFindingModel(
            target_url=data.target_url,
            audit_category=data.audit_category,
            issue_code=data.issue_code,
            severity=data.severity.value if hasattr(data.severity, "value") else str(data.severity),
            status=data.status.value if hasattr(data.status, "value") else str(data.status),
            confidence=data.confidence,
            description=data.description,
            recommendation=data.recommendation,
            patch=data.patch,
            validation_status=val_status,
            raw_metrics=data.raw_metrics,
            evaluated_at=data.evaluated_at,
        )
        return self.create(entity)

    def record_batch(self, findings: List[AuditFindingCreate]) -> List[AuditFindingModel]:
        """Record a list of audit findings in a single transaction."""
        entities = []
        for data in findings:
            val_status = (
                data.validation_status.value
                if hasattr(data.validation_status, "value")
                else str(data.validation_status)
            )
            entity = AuditFindingModel(
                target_url=data.target_url,
                audit_category=data.audit_category,
                issue_code=data.issue_code,
                severity=data.severity.value if hasattr(data.severity, "value") else str(data.severity),
                status=data.status.value if hasattr(data.status, "value") else str(data.status),
                confidence=data.confidence,
                description=data.description,
                recommendation=data.recommendation,
                patch=data.patch,
                validation_status=val_status,
                raw_metrics=data.raw_metrics,
                evaluated_at=data.evaluated_at,
            )
            self.db.add(entity)
            entities.append(entity)
        self.db.commit()
        for e in entities:
            self.db.refresh(e)
        return entities

    def get_by_id(self, finding_id: str) -> Optional[AuditFindingModel]:
        """Get an audit finding by ID."""
        return super().get_by_id(finding_id)

    def update_validation_status(
        self,
        finding_id: str,
        validation_status: str,
        notes: Optional[str] = None,
    ) -> Optional[AuditFindingModel]:
        """Update the fix validation status for an audit finding."""
        finding = self.get_by_id(finding_id)
        if not finding:
            return None
        finding.validation_status = validation_status
        if notes:
            metrics = dict(finding.raw_metrics) if finding.raw_metrics else {}
            metrics["validation_notes"] = notes
            finding.raw_metrics = metrics
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def list_by_url(self, target_url: str) -> List[AuditFindingModel]:
        """List findings for a specific target URL."""
        stmt = (
            select(AuditFindingModel)
            .where(AuditFindingModel.target_url == target_url)
            .order_by(AuditFindingModel.evaluated_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_by_category(self, category: str) -> List[AuditFindingModel]:
        """List findings within an audit category."""
        stmt = (
            select(AuditFindingModel)
            .where(AuditFindingModel.audit_category == category)
            .order_by(AuditFindingModel.evaluated_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_by_validation_status(self, validation_status: str) -> List[AuditFindingModel]:
        """List findings by validation status."""
        stmt = (
            select(AuditFindingModel)
            .where(AuditFindingModel.validation_status == validation_status)
            .order_by(AuditFindingModel.evaluated_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def filter_findings(
        self,
        target_url: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status_val: Optional[str] = None,
        validation_status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditFindingModel]:
        """Filter audit findings by multiple criteria."""
        stmt = select(AuditFindingModel)
        if target_url:
            stmt = stmt.where(AuditFindingModel.target_url == target_url)
        if category:
            stmt = stmt.where(AuditFindingModel.audit_category == category)
        if severity:
            stmt = stmt.where(AuditFindingModel.severity == severity)
        if status_val:
            stmt = stmt.where(AuditFindingModel.status == status_val)
        if validation_status:
            stmt = stmt.where(AuditFindingModel.validation_status == validation_status)

        stmt = stmt.order_by(AuditFindingModel.evaluated_at.desc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
