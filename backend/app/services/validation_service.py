from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.clinician import Clinician
from app.models.enums import ReviewerVerdict
from app.models.validation_review import ValidationReview
from app.schemas.validation import ValidationBySkinToneOut, ValidationByReviewerOut, ValidationSummaryOut


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 2)


def summary(db: Session) -> ValidationSummaryOut:
    total_reviews = db.scalar(select(func.count(ValidationReview.id))) or 0
    ai_available_count = (
        db.scalar(select(func.count(ValidationReview.id)).where(ValidationReview.ai_available.is_(True))) or 0
    )
    matched_count = (
        db.scalar(select(func.count(ValidationReview.id)).where(ValidationReview.match.is_(True))) or 0
    )
    # A mismatch or an unavailable AI (no classification to compare against)
    # both count as the clinician's final answer diverging from the AI.
    overridden_count = (
        db.scalar(
            select(func.count(ValidationReview.id)).where(
                ValidationReview.match.is_(False) | ValidationReview.match.is_(None)
            )
        )
        or 0
    )
    verdicts_recorded = (
        db.scalar(select(func.count(ValidationReview.id)).where(ValidationReview.reviewer_verdict.isnot(None)))
        or 0
    )
    incorrect_count = (
        db.scalar(
            select(func.count(ValidationReview.id)).where(
                ValidationReview.reviewer_verdict == ReviewerVerdict.INCORRECT
            )
        )
        or 0
    )

    return ValidationSummaryOut(
        total_reviews=total_reviews,
        ai_available_count=ai_available_count,
        accuracy_rate=_rate(matched_count, ai_available_count),
        override_rate=_rate(overridden_count, total_reviews),
        hallucination_rate=_rate(incorrect_count, verdicts_recorded),
    )


def by_reviewer(db: Session) -> list[ValidationByReviewerOut]:
    rows = db.execute(
        select(
            ValidationReview.reviewer_id,
            Clinician.name,
            Clinician.role,
            func.count(ValidationReview.id).label("review_count"),
            func.sum(case((ValidationReview.match.is_(True), 1), else_=0)).label("matched"),
            func.sum(case((ValidationReview.ai_available.is_(True), 1), else_=0)).label("ai_available_count"),
            func.sum(
                case((ValidationReview.match.is_(False) | ValidationReview.match.is_(None), 1), else_=0)
            ).label("overridden"),
        )
        .join(Clinician, Clinician.id == ValidationReview.reviewer_id)
        .where(ValidationReview.reviewer_id.isnot(None))
        .group_by(ValidationReview.reviewer_id, Clinician.name, Clinician.role)
        .order_by(Clinician.name.asc())
    ).all()

    return [
        ValidationByReviewerOut(
            reviewer_id=row.reviewer_id,
            reviewer_name=row.name,
            role=row.role,
            review_count=row.review_count,
            accuracy_rate=_rate(row.matched, row.ai_available_count),
            override_rate=_rate(row.overridden, row.review_count),
        )
        for row in rows
    ]


def by_skin_tone(db: Session) -> list[ValidationBySkinToneOut]:
    rows = db.execute(
        select(
            ValidationReview.fitzpatrick_scale,
            func.count(ValidationReview.id).label("review_count"),
            func.sum(case((ValidationReview.match.is_(True), 1), else_=0)).label("matched"),
            func.sum(case((ValidationReview.ai_available.is_(True), 1), else_=0)).label("ai_available_count"),
        )
        .where(ValidationReview.fitzpatrick_scale.isnot(None))
        .group_by(ValidationReview.fitzpatrick_scale)
        .order_by(ValidationReview.fitzpatrick_scale.asc())
    ).all()

    return [
        ValidationBySkinToneOut(
            fitzpatrick_scale=row.fitzpatrick_scale,
            review_count=row.review_count,
            accuracy_rate=_rate(row.matched, row.ai_available_count),
        )
        for row in rows
    ]
