import uuid

from sqlalchemy.orm import Session

from app.common.errors import ValidationFailedError
from app.models.enums import ReviewStatus
from app.schemas.notes import NotesGenerateOut
from app.services import assessment_service, audit_service
from app.services.ai_client import ai_client
from app.services.clinical_assessment_service import confidence_tier


def _assessment_summary(assessment) -> str:
    return (
        f"Assessment date: {assessment.assessment_date.isoformat()}. "
        f"Measurements: Length {assessment.length_cm} cm x Width {assessment.width_cm} cm x "
        f"Depth {assessment.depth_cm} cm. Area {assessment.area_cm2} cm2. "
        f"Volume {assessment.volume_cm3} cm3. Tissue: {assessment.tissue_type}. "
        f"Drainage: {assessment.drainage_amount} {assessment.drainage_type}. "
        f"Periwound: {assessment.periwound}."
    )


def generate(db: Session, assessment_id: uuid.UUID) -> NotesGenerateOut:
    assessment = assessment_service.get_assessment(db, assessment_id)
    if assessment.is_baseline:
        raise ValidationFailedError(
            "Note generation does not apply to baseline assessments; baseline notes are auto-generated on save."
        )
    if assessment.review_status not in (ReviewStatus.ACCEPTED, ReviewStatus.OVERRIDDEN):
        raise ValidationFailedError(
            "Assessment must be reviewed (accepted or overridden) before generating a note."
        )

    finding = assessment.ai_finding
    ai_classification = finding.classification if finding else None
    tier = confidence_tier(ai_classification.confidence_score) if ai_classification else None

    result = ai_client.generate_progress_note(
        assessment_summary=_assessment_summary(assessment),
        classification=assessment.clinician_classification.value if assessment.clinician_classification else None,
        confidence_tier=tier,
        vision_output=finding.vision_output if finding else None,
        override_reason=assessment.override_reason,
    )
    note_draft = (result.data or {}).get("note_draft", "")
    assessment.note_draft = note_draft
    db.flush()

    audit_service.log_call(
        db,
        assessment_id=assessment_id,
        service_name="notes",
        prompt_sent=result.prompt_sent,
        response_received=result.response_received,
        model_version=result.model_version,
        latency_ms=result.latency_ms,
        success=result.success,
        error_message=result.error_message,
    )
    db.refresh(assessment)

    return NotesGenerateOut(
        note_id=assessment.id,
        note_draft=assessment.note_draft,
        classification=assessment.clinician_classification,
        confidence_tier=tier,
    )
