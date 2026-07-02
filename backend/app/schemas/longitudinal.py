import uuid

from pydantic import BaseModel


class LongitudinalAnalyzeRequest(BaseModel):
    assessment_id: uuid.UUID


class LongitudinalAnalyzeOut(BaseModel):
    previous_assessment_id: uuid.UUID
    previous_area_cm2: float
    current_area_cm2: float
    area_delta_pct: float
    tissue_change: str | None
    drainage_change: str | None
