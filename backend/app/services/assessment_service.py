import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.errors import NotFoundError
from app.models.assessment import Assessment
from app.models.enums import ReviewStatus
from app.schemas.assessment import AssessmentCreate, AssessmentCreateOut, AssessmentDetailOut
from app.services import case_service


def _round2(value: float) -> float:
    return round(value, 2)


def _build_baseline_note(a: Assessment) -> str:
    return (
        f"Baseline wound assessment recorded on {a.assessment_date.isoformat()}.\n"
        f"Initial measurements: Length {a.length_cm} cm x Width {a.width_cm} cm x "
        f"Depth {a.depth_cm} cm. Area {a.area_cm2} cm2. Volume {a.volume_cm3} cm3.\n"
        f"Tissue: {a.tissue_type}. Drainage: {a.drainage_amount} {a.drainage_type}. "
        f"Periwound: {a.periwound}.\n"
        "No prior assessment is available for comparison; no healing classification "
        "is generated for baseline assessments.\n"
        "This note reflects observations only and does not constitute a diagnosis, "
        "treatment plan, or prognosis."
    )


def create_assessment(db: Session, payload: AssessmentCreate) -> AssessmentCreateOut:
    case_service.get_case(db, payload.case_id)

    is_baseline = (
        db.scalar(select(Assessment.id).where(Assessment.case_id == payload.case_id).limit(1))
        is None
    )

    area_cm2 = _round2(payload.length_cm * payload.width_cm)
    volume_cm3 = _round2(area_cm2 * payload.depth_cm)

    assessment = Assessment(
        case_id=payload.case_id,
        assessment_date=payload.assessment_date,
        is_baseline=is_baseline,
        length_cm=payload.length_cm,
        width_cm=payload.width_cm,
        depth_cm=payload.depth_cm,
        area_cm2=area_cm2,
        volume_cm3=volume_cm3,
        tissue_type=payload.tissue_type,
        drainage_amount=payload.drainage_amount,
        drainage_type=payload.drainage_type,
        periwound=payload.periwound,
        notes=payload.notes,
    )

    if is_baseline:
        # §2: baseline assessments skip the AI pipeline and review gate
        # entirely — auto-save documentation now, no classification.
        assessment.review_status = ReviewStatus.ACCEPTED

    db.add(assessment)
    db.flush()

    if is_baseline:
        assessment.note_draft = _build_baseline_note(assessment)

    db.commit()
    db.refresh(assessment)

    return AssessmentCreateOut(
        assessment_id=assessment.id,
        is_baseline=assessment.is_baseline,
        area_cm2=assessment.area_cm2,
        volume_cm3=assessment.volume_cm3,
        review_status=assessment.review_status,
    )


def get_assessment(db: Session, assessment_id: uuid.UUID) -> Assessment:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise NotFoundError(f"Assessment {assessment_id} not found")
    return assessment


def _to_detail_out(a: Assessment) -> AssessmentDetailOut:
    return AssessmentDetailOut(
        assessment_id=a.id,
        case_id=a.case_id,
        assessment_date=a.assessment_date,
        is_baseline=a.is_baseline,
        length_cm=a.length_cm,
        width_cm=a.width_cm,
        depth_cm=a.depth_cm,
        area_cm2=a.area_cm2,
        volume_cm3=a.volume_cm3,
        tissue_type=a.tissue_type,
        drainage_amount=a.drainage_amount,
        drainage_type=a.drainage_type,
        periwound=a.periwound,
        notes=a.notes,
        review_status=a.review_status,
        clinician_classification=a.clinician_classification,
        override_reason=a.override_reason,
        note_draft=a.note_draft,
        created_at=a.created_at,
    )


def get_assessment_detail(db: Session, assessment_id: uuid.UUID) -> AssessmentDetailOut:
    return _to_detail_out(get_assessment(db, assessment_id))


def list_assessments_for_case(db: Session, case_id: uuid.UUID) -> list[AssessmentDetailOut]:
    case_service.get_case(db, case_id)
    assessments = db.scalars(
        select(Assessment)
        .where(Assessment.case_id == case_id)
        .order_by(Assessment.assessment_date.asc(), Assessment.created_at.asc())
    )
    return [_to_detail_out(a) for a in assessments]


def get_previous_assessment(db: Session, assessment: Assessment) -> Assessment | None:
    # Use assessment_date (clinician-entered) as the primary comparator.
    # created_at cannot be used here because within a single DB transaction both
    # savepointed commits share the same now() timestamp (e.g., in tests), which
    # would make Assessment.created_at == assessment.created_at and return None.
    return db.scalar(
        select(Assessment)
        .where(
            Assessment.case_id == assessment.case_id,
            Assessment.assessment_date < assessment.assessment_date,
        )
        .order_by(Assessment.assessment_date.desc(), Assessment.created_at.desc())
        .limit(1)
    )
