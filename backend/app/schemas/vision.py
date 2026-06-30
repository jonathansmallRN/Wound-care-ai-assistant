import uuid

from pydantic import BaseModel


class VisionAnalyzeRequest(BaseModel):
    assessment_id: uuid.UUID


class VisionAnalyzeOut(BaseModel):
    ai_finding_id: uuid.UUID
    model_version: str
    vision_output: str | None
    tissue_change: str | None
    drainage_change: str | None
    ai_available: bool
