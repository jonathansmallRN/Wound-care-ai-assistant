import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.notes import NoteUpdateOut, NoteUpdateRequest, NotesGenerateOut, NotesGenerateRequest
from app.services import notes_service

router = APIRouter(tags=["notes"])


@router.post("/notes/generate", response_model=SuccessResponse[NotesGenerateOut])
def generate(payload: NotesGenerateRequest, db: Session = Depends(get_db)) -> SuccessResponse[NotesGenerateOut]:
    return SuccessResponse(data=notes_service.generate(db, payload.assessment_id))


@router.patch("/assessments/{assessment_id}/note", response_model=SuccessResponse[NoteUpdateOut])
def update_note(
    assessment_id: uuid.UUID,
    payload: NoteUpdateRequest,
    db: Session = Depends(get_db),
) -> SuccessResponse[NoteUpdateOut]:
    return SuccessResponse(data=notes_service.update_note(db, assessment_id, payload.note_draft))
