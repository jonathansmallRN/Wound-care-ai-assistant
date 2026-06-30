import uuid
from typing import Literal

from pydantic import BaseModel

from app.models.enums import FitzpatrickScale, HealingClassification

ReviewDecision = Literal["accepted", "overridden"]


class ReviewRequest(BaseModel):
    assessment_id: uuid.UUID
    reviewer_id: uuid.UUID | None = None
    review_status: ReviewDecision
    clinician_classification: HealingClassification | None = None
    override_reason: str | None = None
    # Not in 05_api_contract.md's literal request schema, but
    # validation_reviews.fitzpatrick_scale is required for the Validation
    # Dashboard's skin-tone bias tracking (§9) and the contract is silent
    # on where it's captured — added here as an optional field.
    fitzpatrick_scale: FitzpatrickScale | None = None

    # Override-required-fields are enforced in review_service (not here) so a
    # missing override_reason maps to the spec's OVERRIDE_INCOMPLETE error
    # code rather than a generic Pydantic VALIDATION_ERROR.


class ReviewOut(BaseModel):
    assessment_id: uuid.UUID
    review_status: str
    final_classification: HealingClassification | None
    ai_classification: HealingClassification | None
    override_reason: str | None
    validation_record_id: uuid.UUID
