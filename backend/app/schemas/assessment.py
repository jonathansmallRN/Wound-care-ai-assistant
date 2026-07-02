import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.models.enums import HealingClassification, ReviewStatus

TissueType = Literal["granulation", "slough", "eschar", "epithelial", "mixed"]
DrainageAmount = Literal["none", "minimal", "moderate", "heavy"]
DrainageType = Literal["serous", "serosanguineous", "sanguineous", "purulent"]
Periwound = Literal["intact", "macerated", "erythema", "induration"]


class AssessmentCreate(BaseModel):
    case_id: uuid.UUID
    assessment_date: date
    length_cm: float
    width_cm: float
    depth_cm: float
    tissue_type: TissueType
    drainage_amount: DrainageAmount
    drainage_type: DrainageType
    periwound: Periwound
    notes: str | None = None


class AssessmentCreateOut(BaseModel):
    assessment_id: uuid.UUID
    is_baseline: bool
    area_cm2: float
    volume_cm3: float
    review_status: ReviewStatus

    model_config = {"from_attributes": True}


class AssessmentDetailOut(BaseModel):
    assessment_id: uuid.UUID
    case_id: uuid.UUID
    assessment_date: date
    is_baseline: bool
    length_cm: float
    width_cm: float
    depth_cm: float
    area_cm2: float
    volume_cm3: float
    tissue_type: str
    drainage_amount: str
    drainage_type: str
    periwound: str
    notes: str | None
    review_status: ReviewStatus
    clinician_classification: HealingClassification | None
    override_reason: str | None
    note_draft: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
