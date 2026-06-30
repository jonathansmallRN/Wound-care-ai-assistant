import uuid

from pydantic import BaseModel

from app.models.enums import FitzpatrickScale


class ValidationSummaryOut(BaseModel):
    total_reviews: int
    ai_available_count: int
    accuracy_rate: float | None
    override_rate: float | None
    hallucination_rate: float | None


class ValidationByReviewerOut(BaseModel):
    reviewer_id: uuid.UUID
    reviewer_name: str
    role: str
    review_count: int
    accuracy_rate: float | None
    override_rate: float | None


class ValidationBySkinToneOut(BaseModel):
    fitzpatrick_scale: FitzpatrickScale
    review_count: int
    accuracy_rate: float | None
