import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import CaseStatus


class CaseCreate(BaseModel):
    case_ref: str


class CaseOut(BaseModel):
    id: uuid.UUID
    case_ref: str
    status: CaseStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseDetailOut(BaseModel):
    id: uuid.UUID
    case_ref: str
    status: CaseStatus
    assessment_count: int

    model_config = {"from_attributes": True}


class CaseListItemOut(BaseModel):
    id: uuid.UUID
    case_ref: str
    status: CaseStatus
    created_at: datetime
    assessment_count: int

    model_config = {"from_attributes": True}
