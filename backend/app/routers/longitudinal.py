from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.longitudinal import LongitudinalAnalyzeOut, LongitudinalAnalyzeRequest
from app.services import longitudinal_service

router = APIRouter(tags=["longitudinal"])


@router.post("/longitudinal/analyze", response_model=SuccessResponse[LongitudinalAnalyzeOut])
def analyze(
    payload: LongitudinalAnalyzeRequest, db: Session = Depends(get_db)
) -> SuccessResponse[LongitudinalAnalyzeOut]:
    return SuccessResponse(data=longitudinal_service.analyze(db, payload.assessment_id))
