from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.review import ReviewOut, ReviewRequest
from app.services import review_service

router = APIRouter(tags=["review"])


@router.post("/review", response_model=SuccessResponse[ReviewOut])
def submit_review(payload: ReviewRequest, db: Session = Depends(get_db)) -> SuccessResponse[ReviewOut]:
    return SuccessResponse(data=review_service.submit_review(db, payload))
