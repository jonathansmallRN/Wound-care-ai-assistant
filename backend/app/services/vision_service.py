import uuid

from sqlalchemy.orm import Session

from app.common.errors import AppError, ErrorCode, ValidationFailedError
from app.models.ai_finding import AIFinding
from app.schemas.vision import VisionAnalyzeOut
from app.services import assessment_service, audit_service, image_service
from app.services.ai_client import ai_client


def analyze(db: Session, assessment_id: uuid.UUID) -> VisionAnalyzeOut:
    assessment = assessment_service.get_assessment(db, assessment_id)
    if assessment.is_baseline:
        raise ValidationFailedError("Vision analysis does not apply to baseline assessments.")

    image_path = image_service.get_latest_image_path(db, assessment_id)

    result = ai_client.analyze_wound_image(
        assessment_id=str(assessment_id),
        image_path=image_path,
        tissue_type=assessment.tissue_type,
        drainage_amount=assessment.drainage_amount,
        drainage_type=assessment.drainage_type,
        periwound=assessment.periwound,
    )

    finding = assessment.ai_finding
    if finding is None:
        finding = AIFinding(assessment_id=assessment_id)
        db.add(finding)

    finding.model_version = result.model_version
    finding.ai_available = result.success

    if result.success and result.data:
        finding.vision_output = result.data.get("vision_output")
        finding.tissue_change = result.data.get("tissue_change")
        finding.drainage_change = result.data.get("drainage_change")
        finding.failure_reason = None
    else:
        finding.vision_output = None
        finding.tissue_change = None
        finding.drainage_change = None
        finding.failure_reason = result.error_message

    db.flush()

    audit_service.log_call(
        db,
        assessment_id=assessment_id,
        service_name="vision",
        prompt_sent=result.prompt_sent,
        response_received=result.response_received,
        model_version=result.model_version,
        latency_ms=result.latency_ms,
        success=result.success,
        error_message=result.error_message,
    )
    db.refresh(finding)

    if not result.success:
        # §7: an AI failure must not block the clinician — surface a
        # structured error so the frontend can route to manual entry.
        raise AppError(
            503,
            ErrorCode.AI_UNAVAILABLE,
            "Vision service unavailable — please complete assessment manually",
        )

    return VisionAnalyzeOut(
        ai_finding_id=finding.id,
        model_version=finding.model_version,
        vision_output=finding.vision_output,
        tissue_change=finding.tissue_change,
        drainage_change=finding.drainage_change,
        ai_available=finding.ai_available,
    )
