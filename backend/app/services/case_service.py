import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.errors import NotFoundError
from app.models.assessment import Assessment
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseDetailOut, CaseListItemOut


def create_case(db: Session, payload: CaseCreate) -> Case:
    case = Case(case_ref=payload.case_ref)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: uuid.UUID) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise NotFoundError(f"Case {case_id} not found")
    return case


def get_case_detail(db: Session, case_id: uuid.UUID) -> CaseDetailOut:
    case = get_case(db, case_id)
    count = (
        db.scalar(select(func.count()).select_from(Assessment).where(Assessment.case_id == case_id))
        or 0
    )
    return CaseDetailOut(id=case.id, case_ref=case.case_ref, status=case.status, assessment_count=count)


def list_cases(db: Session) -> list[CaseListItemOut]:
    rows = db.execute(
        select(Case, func.count(Assessment.id))
        .outerjoin(Assessment, Assessment.case_id == Case.id)
        .group_by(Case.id)
        .order_by(Case.created_at.desc())
    ).all()
    return [
        CaseListItemOut(
            id=case.id,
            case_ref=case.case_ref,
            status=case.status,
            created_at=case.created_at,
            assessment_count=count,
        )
        for case, count in rows
    ]
