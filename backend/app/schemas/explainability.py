import uuid

from pydantic import BaseModel

from app.models.enums import HealingClassification
from app.schemas.clinical_assessment import ConfidenceTier


class ExplainabilityGenerateRequest(BaseModel):
    assessment_id: uuid.UUID


class EvidenceItem(BaseModel):
    finding: str
    score: float
    weight: float
    supports_classification: bool | None


class ExplainabilityGenerateOut(BaseModel):
    classification: HealingClassification
    confidence_score: float
    confidence_tier: ConfidenceTier
    evidence: list[EvidenceItem]
