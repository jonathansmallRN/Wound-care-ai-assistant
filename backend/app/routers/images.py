import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.image import ImageUploadOut
from app.services import image_service

router = APIRouter(tags=["images"])


@router.post("/images", response_model=SuccessResponse[ImageUploadOut])
def upload_image(
    assessment_id: uuid.UUID = Form(...),
    image_file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> SuccessResponse[ImageUploadOut]:
    image = image_service.save_image(db, assessment_id, image_file)
    return SuccessResponse(
        data=ImageUploadOut(
            image_id=image.id,
            storage_url=image.storage_url,
            filename=image.filename,
            file_size_bytes=image.file_size_bytes,
        )
    )
