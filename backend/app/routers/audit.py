import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.audit import AuditLogOut
from app.schemas.common import SuccessResponse
from app.services import audit_service

router = APIRouter(tags=["audit"])


@router.get("/audit/{assessment_id}", response_model=SuccessResponse[list[AuditLogOut]])
def list_for_assessment(
    assessment_id: uuid.UUID, db: Session = Depends(get_db)
) -> SuccessResponse[list[AuditLogOut]]:
    logs = audit_service.list_for_assessment(db, assessment_id)
    return SuccessResponse(data=[AuditLogOut.model_validate(log) for log in logs])
