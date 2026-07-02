import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.assessment import AssessmentCreate, AssessmentCreateOut, AssessmentDetailOut
from app.schemas.common import SuccessResponse
from app.services import assessment_service

router = APIRouter(tags=["assessments"])


@router.post("/assessments", response_model=SuccessResponse[AssessmentCreateOut])
def create_assessment(
    payload: AssessmentCreate, db: Session = Depends(get_db)
) -> SuccessResponse[AssessmentCreateOut]:
    return SuccessResponse(data=assessment_service.create_assessment(db, payload))


@router.get("/assessments/{assessment_id}", response_model=SuccessResponse[AssessmentDetailOut])
def get_assessment(
    assessment_id: uuid.UUID, db: Session = Depends(get_db)
) -> SuccessResponse[AssessmentDetailOut]:
    return SuccessResponse(data=assessment_service.get_assessment_detail(db, assessment_id))


@router.get("/cases/{case_id}/assessments", response_model=SuccessResponse[list[AssessmentDetailOut]])
def list_assessments_for_case(
    case_id: uuid.UUID, db: Session = Depends(get_db)
) -> SuccessResponse[list[AssessmentDetailOut]]:
    return SuccessResponse(data=assessment_service.list_assessments_for_case(db, case_id))
