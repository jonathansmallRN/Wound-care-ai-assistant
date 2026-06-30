import uuid

from sqlalchemy.orm import Session

from app.common.errors import ValidationFailedError
from app.schemas.longitudinal import LongitudinalAnalyzeOut
from app.services import assessment_service


def analyze(db: Session, assessment_id: uuid.UUID) -> LongitudinalAnalyzeOut:
    assessment = assessment_service.get_assessment(db, assessment_id)
    if assessment.is_baseline:
        raise ValidationFailedError("Longitudinal analysis does not apply to baseline assessments.")

    previous = assessment_service.get_previous_assessment(db, assessment)
    if previous is None:
        raise ValidationFailedError("No prior assessment found for longitudinal comparison.")

    finding = assessment.ai_finding
    if finding is None:
        raise ValidationFailedError("Run vision analysis before longitudinal analysis.")

    # Positive = area reduced (improvement); negative = area increased.
    area_delta_pct = round((previous.area_cm2 - assessment.area_cm2) / previous.area_cm2 * 100, 1)

    finding.area_delta_pct = area_delta_pct
    db.commit()
    db.refresh(finding)

    return LongitudinalAnalyzeOut(
        previous_assessment_id=previous.id,
        previous_area_cm2=previous.area_cm2,
        current_area_cm2=assessment.area_cm2,
        area_delta_pct=area_delta_pct,
        tissue_change=finding.tissue_change,
        drainage_change=finding.drainage_change,
    )
