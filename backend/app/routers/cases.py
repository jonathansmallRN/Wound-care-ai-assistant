import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.case import CaseCreate, CaseDetailOut, CaseListItemOut, CaseOut
from app.schemas.common import SuccessResponse
from app.services import case_service

router = APIRouter(tags=["cases"])


@router.post("/cases", response_model=SuccessResponse[CaseOut])
def create_case(payload: CaseCreate, db: Session = Depends(get_db)) -> SuccessResponse[CaseOut]:
    case = case_service.create_case(db, payload)
    return SuccessResponse(data=CaseOut.model_validate(case))


@router.get("/cases", response_model=SuccessResponse[list[CaseListItemOut]])
def list_cases(db: Session = Depends(get_db)) -> SuccessResponse[list[CaseListItemOut]]:
    return SuccessResponse(data=case_service.list_cases(db))


@router.get("/cases/{case_id}", response_model=SuccessResponse[CaseDetailOut])
def get_case(case_id: uuid.UUID, db: Session = Depends(get_db)) -> SuccessResponse[CaseDetailOut]:
    return SuccessResponse(data=case_service.get_case_detail(db, case_id))
