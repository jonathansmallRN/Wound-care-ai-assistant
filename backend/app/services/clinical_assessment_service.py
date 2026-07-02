import time
import uuid

from sqlalchemy.orm import Session

from app.common.errors import ValidationFailedError
from app.models.ai_classification import AIClassification
from app.models.enums import HealingClassification
from app.schemas.clinical_assessment import ClinicalAssessmentClassifyOut, ConfidenceTier
from app.services import assessment_service, audit_service


def confidence_tier(score: float) -> ConfidenceTier:
    if score >= 0.80:
        return "high"
    if score >= 0.60:
        return "medium"
    return "low"


def _signal_score(value: str) -> float:
    """0.0-1.0 strength of a signal, independent of direction.

    A directional reading (improved/worsened) is a strong, decisive signal
    (0.8); a stable/neutral reading is a weaker, neutral signal (0.6).
    Direction-vs-classification alignment is captured separately by
    supports_classification in the explainability evidence list.
    """
    return 0.8 if value in ("improved", "worsened") else 0.6


def classify(db: Session, assessment_id: uuid.UUID) -> ClinicalAssessmentClassifyOut:
    assessment = assessment_service.get_assessment(db, assessment_id)
    if assessment.is_baseline:
        raise ValidationFailedError("Classification does not apply to baseline assessments.")

    finding = assessment.ai_finding
    if finding is None or finding.area_delta_pct is None:
        raise ValidationFailedError("Run vision and longitudinal analysis before classification.")

    start = time.monotonic()
    area_delta_pct = finding.area_delta_pct
    tissue_change = finding.tissue_change or "stable"
    drainage_change = finding.drainage_change or "stable"

    # §4 healing classification rules + §11 edge case: deteriorating signals
    # are checked in area -> tissue -> drainage order before the improving
    # rule, so e.g. 0% area change with worsening tissue is Deteriorating via
    # the tissue rule, not the area rule. First rule to fire wins.
    if area_delta_pct < 0:
        classification = HealingClassification.DETERIORATING
    elif tissue_change == "worsened":
        classification = HealingClassification.DETERIORATING
    elif drainage_change == "worsened":
        classification = HealingClassification.DETERIORATING
    elif (
        area_delta_pct > 10
        and tissue_change in ("improved", "stable")
        and drainage_change in ("improved", "stable")
    ):
        classification = HealingClassification.IMPROVING
    else:
        classification = HealingClassification.STABLE

    if classification == HealingClassification.STABLE:
        area_signal_score = round(1.0 - min(abs(area_delta_pct) / 10.0, 1.0), 2)
    else:
        area_signal_score = round(min(abs(area_delta_pct) / 20.0, 1.0), 2)

    tissue_signal_score = _signal_score(tissue_change)
    drainage_signal_score = _signal_score(drainage_change)

    confidence_score = round(
        area_signal_score * 0.50 + tissue_signal_score * 0.30 + drainage_signal_score * 0.20, 2
    )

    ai_classification = finding.classification
    if ai_classification is None:
        # evidence_json is NOT NULL; explainability/generate overwrites this
        # placeholder with the real evidence trail per the service mapping.
        ai_classification = AIClassification(ai_finding_id=finding.id, evidence_json={})
        db.add(ai_classification)

    ai_classification.classification = classification
    ai_classification.confidence_score = confidence_score
    ai_classification.area_signal_score = area_signal_score
    ai_classification.tissue_signal_score = tissue_signal_score
    ai_classification.drainage_signal_score = drainage_signal_score

    latency_ms = int((time.monotonic() - start) * 1000)
    db.commit()
    db.refresh(ai_classification)

    audit_service.log_call(
        db,
        assessment_id=assessment_id,
        service_name="clinical_assessment",
        prompt_sent=None,
        response_received=(
            f"classification={classification.value}, confidence={confidence_score}, "
            f"area_signal={area_signal_score}, tissue_signal={tissue_signal_score}, "
            f"drainage_signal={drainage_signal_score}"
        ),
        model_version=None,
        latency_ms=latency_ms,
        success=True,
    )

    return ClinicalAssessmentClassifyOut(
        classification=classification,
        confidence_score=confidence_score,
        confidence_tier=confidence_tier(confidence_score),
        area_signal_score=area_signal_score,
        tissue_signal_score=tissue_signal_score,
        drainage_signal_score=drainage_signal_score,
    )
