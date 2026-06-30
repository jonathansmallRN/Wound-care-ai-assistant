from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.validation import ValidationBySkinToneOut, ValidationByReviewerOut, ValidationSummaryOut
from app.services import validation_service

router = APIRouter(tags=["validation"])


@router.get("/validation/summary", response_model=SuccessResponse[ValidationSummaryOut])
def summary(db: Session = Depends(get_db)) -> SuccessResponse[ValidationSummaryOut]:
    return SuccessResponse(data=validation_service.summary(db))


@router.get("/validation/by-reviewer", response_model=SuccessResponse[list[ValidationByReviewerOut]])
def by_reviewer(db: Session = Depends(get_db)) -> SuccessResponse[list[ValidationByReviewerOut]]:
    return SuccessResponse(data=validation_service.by_reviewer(db))


@router.get("/validation/by-skin-tone", response_model=SuccessResponse[list[ValidationBySkinToneOut]])
def by_skin_tone(db: Session = Depends(get_db)) -> SuccessResponse[list[ValidationBySkinToneOut]]:
    return SuccessResponse(data=validation_service.by_skin_tone(db))
