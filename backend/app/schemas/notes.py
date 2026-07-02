import uuid

from pydantic import BaseModel

from app.models.enums import HealingClassification
from app.schemas.clinical_assessment import ConfidenceTier


class NotesGenerateRequest(BaseModel):
    assessment_id: uuid.UUID


class NotesGenerateOut(BaseModel):
    note_id: uuid.UUID
    note_draft: str
    classification: HealingClassification | None
    confidence_tier: ConfidenceTier | None


class NoteUpdateRequest(BaseModel):
    note_draft: str


class NoteUpdateOut(BaseModel):
    note_id: uuid.UUID
    note_draft: str
