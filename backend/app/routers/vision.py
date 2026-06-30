from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.vision import VisionAnalyzeOut, VisionAnalyzeRequest
from app.services import vision_service

router = APIRouter(tags=["vision"])


@router.post("/vision/analyze", response_model=SuccessResponse[VisionAnalyzeOut])
def analyze(payload: VisionAnalyzeRequest, db: Session = Depends(get_db)) -> SuccessResponse[VisionAnalyzeOut]:
    return SuccessResponse(data=vision_service.analyze(db, payload.assessment_id))
