from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.clinical_assessment import (
    ClinicalAssessmentClassifyOut,
    ClinicalAssessmentClassifyRequest,
)
from app.schemas.common import SuccessResponse
from app.services import clinical_assessment_service

router = APIRouter(tags=["clinical-assessment"])


@router.post("/clinical-assessment/classify", response_model=SuccessResponse[ClinicalAssessmentClassifyOut])
def classify(
    payload: ClinicalAssessmentClassifyRequest, db: Session = Depends(get_db)
) -> SuccessResponse[ClinicalAssessmentClassifyOut]:
    return SuccessResponse(data=clinical_assessment_service.classify(db, payload.assessment_id))
