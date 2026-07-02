import uuid

from sqlalchemy.orm import Session

from app.common.errors import AppError, ErrorCode, ValidationFailedError
from app.models.enums import ReviewStatus
from app.models.validation_review import ValidationReview
from app.schemas.review import ReviewOut, ReviewRequest
from app.services import assessment_service

LOW_CONFIDENCE_THRESHOLD = 0.60


def submit_review(db: Session, payload: ReviewRequest) -> ReviewOut:
    assessment = assessment_service.get_assessment(db, payload.assessment_id)
    if assessment.is_baseline:
        raise ValidationFailedError("Review does not apply to baseline assessments.")

    finding = assessment.ai_finding
    ai_classification = finding.classification if finding else None

    if payload.fitzpatrick_scale is None:
        raise ValidationFailedError(
            "fitzpatrick_scale is required for skin-tone bias tracking in the validation dashboard."
        )

    if payload.review_status == "overridden":
        if payload.clinician_classification is None or not payload.override_reason:
            raise AppError(
                422,
                ErrorCode.OVERRIDE_INCOMPLETE,
                "clinician_classification and override_reason are required when overriding.",
            )
        final_classification = payload.clinician_classification
        assessment.review_status = ReviewStatus.OVERRIDDEN
        assessment.override_reason = payload.override_reason
    else:
        if ai_classification is None:
            raise ValidationFailedError(
                "No AI classification available to accept — override with a manual classification instead."
            )
        if ai_classification.confidence_score < LOW_CONFIDENCE_THRESHOLD:
            raise AppError(
                422,
                ErrorCode.AI_LOW_CONFIDENCE,
                "Confidence below 60% — manual review required before note generation. "
                "Override with your own classification.",
            )
        final_classification = ai_classification.classification
        assessment.review_status = ReviewStatus.ACCEPTED
        assessment.override_reason = None

    assessment.clinician_classification = final_classification
    db.flush()

    ai_available = finding.ai_available if finding else False
    match = (
        ai_classification.classification == final_classification
        if ai_available and ai_classification is not None
        else None
    )

    validation_review = assessment.validation_review
    if validation_review is None:
        validation_review = ValidationReview(assessment_id=assessment.id)
        db.add(validation_review)

    validation_review.reviewer_id = payload.reviewer_id
    validation_review.ai_classification = ai_classification.classification if ai_classification else None
    validation_review.ai_confidence = ai_classification.confidence_score if ai_classification else None
    validation_review.clinician_classification = final_classification
    validation_review.match = match
    validation_review.ai_available = ai_available
    validation_review.fitzpatrick_scale = payload.fitzpatrick_scale

    db.commit()
    db.refresh(assessment)
    db.refresh(validation_review)

    return ReviewOut(
        assessment_id=assessment.id,
        review_status=assessment.review_status,
        final_classification=final_classification,
        ai_classification=ai_classification.classification if ai_classification else None,
        override_reason=assessment.override_reason,
        validation_record_id=validation_review.id,
    )
