import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.services import assessment_service


def log_call(
    db: Session,
    *,
    assessment_id: uuid.UUID,
    service_name: str,
    prompt_sent: str | None,
    response_received: str | None,
    model_version: str | None,
    latency_ms: int | None,
    success: bool,
    error_message: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        assessment_id=assessment_id,
        service_name=service_name,
        prompt_sent=prompt_sent,
        response_received=response_received,
        model_version=model_version,
        latency_ms=latency_ms,
        success=success,
        error_message=error_message,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_for_assessment(db: Session, assessment_id: uuid.UUID) -> list[AuditLog]:
    assessment_service.get_assessment(db, assessment_id)
    return list(
        db.scalars(
            select(AuditLog)
            .where(AuditLog.assessment_id == assessment_id)
            .order_by(AuditLog.created_at.asc())
        )
    )
