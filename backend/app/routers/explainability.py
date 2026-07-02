from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.explainability import ExplainabilityGenerateOut, ExplainabilityGenerateRequest
from app.services import explainability_service

router = APIRouter(tags=["explainability"])


@router.post("/explainability/generate", response_model=SuccessResponse[ExplainabilityGenerateOut])
def generate(
    payload: ExplainabilityGenerateRequest, db: Session = Depends(get_db)
) -> SuccessResponse[ExplainabilityGenerateOut]:
    return SuccessResponse(data=explainability_service.generate(db, payload.assessment_id))
