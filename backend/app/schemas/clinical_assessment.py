import uuid
from typing import Literal

from pydantic import BaseModel

from app.models.enums import HealingClassification

ConfidenceTier = Literal["high", "medium", "low"]


class ClinicalAssessmentClassifyRequest(BaseModel):
    assessment_id: uuid.UUID


class ClinicalAssessmentClassifyOut(BaseModel):
    classification: HealingClassification
    confidence_score: float
    confidence_tier: ConfidenceTier
    area_signal_score: float
    tissue_signal_score: float
    drainage_signal_score: float
