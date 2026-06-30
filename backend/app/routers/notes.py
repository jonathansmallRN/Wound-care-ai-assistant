from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.notes import NotesGenerateOut, NotesGenerateRequest
from app.services import notes_service

router = APIRouter(tags=["notes"])


@router.post("/notes/generate", response_model=SuccessResponse[NotesGenerateOut])
def generate(payload: NotesGenerateRequest, db: Session = Depends(get_db)) -> SuccessResponse[NotesGenerateOut]:
    return SuccessResponse(data=notes_service.generate(db, payload.assessment_id))
