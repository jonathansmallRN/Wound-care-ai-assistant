import uuid

from sqlalchemy.orm import Session

from app.common.errors import ValidationFailedError
from app.models.enums import HealingClassification
from app.schemas.explainability import EvidenceItem, ExplainabilityGenerateOut
from app.services import assessment_service, audit_service
from app.services.ai_client import ai_client
from app.services.clinical_assessment_service import confidence_tier


def _area_supports(area_delta_pct: float, classification: HealingClassification) -> bool:
    if classification == HealingClassification.IMPROVING:
        return area_delta_pct > 10
    if classification == HealingClassification.DETERIORATING:
        return area_delta_pct < 0
    return -10 <= area_delta_pct <= 10


def _categorical_supports(value: str, classification: HealingClassification) -> bool | None:
    if value == "stable":
        return None
    if classification == HealingClassification.IMPROVING:
        return value == "improved"
    if classification == HealingClassification.DETERIORATING:
        return value == "worsened"
    return False


def generate(db: Session, assessment_id: uuid.UUID) -> ExplainabilityGenerateOut:
    assessment = assessment_service.get_assessment(db, assessment_id)
    if assessment.is_baseline:
        raise ValidationFailedError("Explainability does not apply to baseline assessments.")

    finding = assessment.ai_finding
    if finding is None or finding.area_delta_pct is None:
        raise ValidationFailedError("Run vision and longitudinal analysis before explainability.")

    ai_classification = finding.classification
    if ai_classification is None:
        raise ValidationFailedError("Run clinical-assessment/classify before explainability.")

    area_delta_pct = finding.area_delta_pct
    tissue_change = finding.tissue_change or "stable"
    drainage_change = finding.drainage_change or "stable"
    classification = ai_classification.classification

    result = ai_client.generate_evidence_narrative(
        area_delta_pct=area_delta_pct,
        tissue_change=tissue_change,
        drainage_change=drainage_change,
    )
    narrative = result.data or {}

    evidence = [
        EvidenceItem(
            finding=narrative.get("area_finding", f"Area changed {area_delta_pct}%"),
            score=ai_classification.area_signal_score,
            weight=0.50,
            supports_classification=_area_supports(area_delta_pct, classification),
        ),
        EvidenceItem(
            finding=narrative.get("tissue_finding", "Tissue appearance unchanged"),
            score=ai_classification.tissue_signal_score,
            weight=0.30,
            supports_classification=_categorical_supports(tissue_change, classification),
        ),
        EvidenceItem(
            finding=narrative.get("drainage_finding", "Drainage unchanged"),
            score=ai_classification.drainage_signal_score,
            weight=0.20,
            supports_classification=_categorical_supports(drainage_change, classification),
        ),
    ]

    # Overwrites the {} placeholder written by clinical-assessment/classify
    # with the real evidence trail, per the spec's split-write design.
    ai_classification.evidence_json = {"evidence": [item.model_dump() for item in evidence]}
    db.flush()

    audit_service.log_call(
        db,
        assessment_id=assessment_id,
        service_name="explainability",
        prompt_sent=result.prompt_sent,
        response_received=result.response_received,
        model_version=result.model_version,
        latency_ms=result.latency_ms,
        success=result.success,
        error_message=result.error_message,
    )
    db.refresh(ai_classification)

    return ExplainabilityGenerateOut(
        classification=classification,
        confidence_score=ai_classification.confidence_score,
        confidence_tier=confidence_tier(ai_classification.confidence_score),
        evidence=evidence,
    )
