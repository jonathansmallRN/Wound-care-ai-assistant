"""
Idempotent demo seed data.

Runs automatically on container start (entrypoint.sh). Checks for a seed
marker (case_ref="SEED-CASE-001") before inserting anything — safe to call
on every restart.

Five cases are seeded to cover the full clinical workflow:
  SEED-CASE-001  Improving trajectory (3 assessments, Fitzpatrick III)
  SEED-CASE-002  Stable trajectory    (3 assessments, Fitzpatrick II)
  SEED-CASE-003  Deteriorating        (2 assessments, Fitzpatrick VI)
  SEED-CASE-004  Low-confidence → forced override (2 assessments, Fitzpatrick I)
  SEED-CASE-005  Stable, no change    (2 assessments, Fitzpatrick IV)
"""

import sys
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (  # noqa: F401 — ensures all models are mapped before any query
    AIClassification,
    AIFinding,
    Assessment,
    AuditLog,
    Case,
    Clinician,
    Image,
    ValidationReview,
)
from app.schemas.assessment import AssessmentCreate
from app.schemas.case import CaseCreate
from app.schemas.review import ReviewRequest
from app.services import (
    assessment_service,
    case_service,
    clinical_assessment_service,
    explainability_service,
    longitudinal_service,
    notes_service,
    review_service,
    vision_service,
)

SEED_MARKER = "SEED-CASE-001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _already_seeded(db: Session) -> bool:
    return db.scalar(select(Case).where(Case.case_ref == SEED_MARKER).limit(1)) is not None


def _get_or_create_clinician(db: Session, name: str, role: str, email: str) -> Clinician:
    existing = db.scalar(select(Clinician).where(Clinician.email == email))
    if existing:
        return existing
    c = Clinician(name=name, role=role, email=email)
    db.add(c)
    db.flush()
    return c


def _run_pipeline(
    db: Session,
    assessment_id,
    reviewer_id,
    review_status: str,
    fitzpatrick: str,
    clinician_classification: str | None = None,
    override_reason: str | None = None,
) -> None:
    """Run the full follow-up pipeline for a single assessment."""
    vision_service.analyze(db, assessment_id)
    longitudinal_service.analyze(db, assessment_id)
    clinical_assessment_service.classify(db, assessment_id)
    explainability_service.generate(db, assessment_id)
    review_service.submit_review(
        db,
        ReviewRequest(
            assessment_id=assessment_id,
            reviewer_id=reviewer_id,
            review_status=review_status,
            clinician_classification=clinician_classification,
            override_reason=override_reason,
            fitzpatrick_scale=fitzpatrick,
        ),
    )
    notes_service.generate(db, assessment_id)


def _assessment(case_id, assessment_date, length, width, depth, tissue, drain_amount, drain_type, periwound, notes=None):
    return AssessmentCreate(
        case_id=case_id,
        assessment_date=assessment_date,
        length_cm=length,
        width_cm=width,
        depth_cm=depth,
        tissue_type=tissue,
        drainage_amount=drain_amount,
        drainage_type=drain_type,
        periwound=periwound,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------


def seed(db: Session) -> None:
    if _already_seeded(db):
        print("Seed data already present — skipping.")
        return

    print("Seeding demo data…")

    # -- Clinicians -----------------------------------------------------------
    sarah = _get_or_create_clinician(db, "Dr. Sarah Chen", "WOCN", "sarah.chen@clinic.example")
    james = _get_or_create_clinician(db, "Dr. James Park", "wound_specialist", "james.park@clinic.example")
    maria = _get_or_create_clinician(db, "Maria Santos RN", "home_health", "maria.santos@clinic.example")
    db.commit()

    # -------------------------------------------------------------------------
    # SEED-CASE-001 — Improving trajectory
    # Baseline area=20.0 → f/u-1 area=12.0 (delta +40%) → f/u-2 area=7.5 (delta +37.5%)
    # tissue=granulation→improved, drainage hashed ≥ 0.6, confidence HIGH each time
    # Reviewer: Sarah  Fitzpatrick: III
    # -------------------------------------------------------------------------
    c1 = case_service.create_case(db, CaseCreate(case_ref=SEED_MARKER))

    assessment_service.create_assessment(
        db,
        _assessment(c1.id, date(2026, 5, 1), 5.0, 4.0, 0.5, "granulation", "moderate", "serous", "intact", "Initial baseline visit"),
    )

    f1a = assessment_service.create_assessment(
        db,
        _assessment(c1.id, date(2026, 5, 14), 4.0, 3.0, 0.4, "granulation", "minimal", "serous", "intact", "2-week follow-up"),
    )
    _run_pipeline(db, f1a.assessment_id, sarah.id, "accepted", "III")

    f1b = assessment_service.create_assessment(
        db,
        _assessment(c1.id, date(2026, 5, 28), 3.0, 2.5, 0.2, "epithelial", "none", "serous", "intact", "4-week follow-up"),
    )
    _run_pipeline(db, f1b.assessment_id, sarah.id, "accepted", "III")

    # -------------------------------------------------------------------------
    # SEED-CASE-002 — Stable trajectory
    # Baseline area=15.75 → f/u-1 area=14.96 (delta +5.0%) → f/u-2 area=14.19 (delta +5.1%)
    # granulation→improved, moderate/serous→stable, confidence ~0.61 (MEDIUM, above 0.60)
    # Reviewer: James  Fitzpatrick: II
    # -------------------------------------------------------------------------
    c2 = case_service.create_case(db, CaseCreate(case_ref="SEED-CASE-002"))

    assessment_service.create_assessment(
        db,
        _assessment(c2.id, date(2026, 5, 3), 4.5, 3.5, 0.6, "mixed", "moderate", "serous", "intact"),
    )

    f2a = assessment_service.create_assessment(
        db,
        _assessment(c2.id, date(2026, 5, 17), 4.4, 3.4, 0.5, "granulation", "moderate", "serous", "intact", "Wound bed appears unchanged"),
    )
    _run_pipeline(db, f2a.assessment_id, james.id, "accepted", "II")

    f2b = assessment_service.create_assessment(
        db,
        _assessment(c2.id, date(2026, 5, 31), 4.3, 3.3, 0.5, "granulation", "moderate", "serous", "intact", "Minimal change from prior visit"),
    )
    _run_pipeline(db, f2b.assessment_id, james.id, "accepted", "II")

    # -------------------------------------------------------------------------
    # SEED-CASE-003 — Deteriorating wound
    # Baseline area=7.5 → f/u area=12.0 (delta -60%), slough→worsened, heavy/purulent→worsened
    # All three signals fire → DETERIORATING, confidence 0.90 (HIGH)
    # Reviewer: Maria  Fitzpatrick: VI
    # -------------------------------------------------------------------------
    c3 = case_service.create_case(db, CaseCreate(case_ref="SEED-CASE-003"))

    assessment_service.create_assessment(
        db,
        _assessment(c3.id, date(2026, 5, 5), 3.0, 2.5, 0.3, "granulation", "moderate", "serous", "intact"),
    )

    f3a = assessment_service.create_assessment(
        db,
        _assessment(c3.id, date(2026, 5, 19), 4.0, 3.0, 0.5, "slough", "heavy", "purulent", "erythema", "Wound appears significantly larger with increased exudate"),
    )
    _run_pipeline(db, f3a.assessment_id, maria.id, "accepted", "VI")

    # -------------------------------------------------------------------------
    # SEED-CASE-004 — Low confidence → forced clinician override
    # Baseline area=16.0 → f/u area=14.44 (delta +9.75%)
    # epithelial→improved, minimal/serous→hashed, but area_signal=0.025 → confidence ~0.37 (LOW)
    # Cannot accept; seed uses override directly, demonstrating that path.
    # Reviewer: Sarah  Fitzpatrick: I
    # -------------------------------------------------------------------------
    c4 = case_service.create_case(db, CaseCreate(case_ref="SEED-CASE-004"))

    assessment_service.create_assessment(
        db,
        _assessment(c4.id, date(2026, 5, 7), 4.0, 4.0, 0.5, "epithelial", "minimal", "serous", "intact"),
    )

    f4a = assessment_service.create_assessment(
        db,
        _assessment(c4.id, date(2026, 5, 21), 3.8, 3.8, 0.4, "epithelial", "minimal", "serous", "intact", "Near-threshold area change — low AI confidence expected"),
    )
    # Run AI pipeline but use override because confidence will be < 0.60
    vision_service.analyze(db, f4a.assessment_id)
    longitudinal_service.analyze(db, f4a.assessment_id)
    clinical_assessment_service.classify(db, f4a.assessment_id)
    explainability_service.generate(db, f4a.assessment_id)
    review_service.submit_review(
        db,
        ReviewRequest(
            assessment_id=f4a.assessment_id,
            reviewer_id=sarah.id,
            review_status="overridden",
            clinician_classification="improving",  # AI said stable; clinician overrides to improving
            override_reason=(
                "Clinical examination shows active wound epithelialization consistent with improvement. "
                "Area reduction is at the threshold boundary — direct observation and tissue quality "
                "support an improving classification. AI confidence score below 60%."
            ),
            fitzpatrick_scale="I",
        ),
    )
    notes_service.generate(db, f4a.assessment_id)

    # -------------------------------------------------------------------------
    # SEED-CASE-005 — Stable, no measurable change
    # Baseline area=30.0 → f/u area=30.0 (delta 0%)
    # granulation→improved, moderate/serous→stable, area_signal=1.0 → confidence 0.86 (HIGH)
    # Reviewer: James  Fitzpatrick: IV
    # -------------------------------------------------------------------------
    c5 = case_service.create_case(db, CaseCreate(case_ref="SEED-CASE-005"))

    assessment_service.create_assessment(
        db,
        _assessment(c5.id, date(2026, 6, 1), 6.0, 5.0, 0.7, "granulation", "moderate", "serous", "macerated"),
    )

    f5a = assessment_service.create_assessment(
        db,
        _assessment(c5.id, date(2026, 6, 14), 6.0, 5.0, 0.7, "granulation", "moderate", "serous", "intact", "Periwound improved; dimensions unchanged"),
    )
    _run_pipeline(db, f5a.assessment_id, james.id, "accepted", "IV")

    print(
        "Seed complete. Created 3 clinicians, 5 cases, 12 assessments "
        "(5 baselines + 7 follow-ups with full AI pipeline)."
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    db = SessionLocal()
    try:
        seed(db)
    except Exception as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
