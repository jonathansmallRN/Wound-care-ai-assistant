import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.common.errors import AppError, ErrorCode
from app.config import settings
from app.models.image import Image
from app.services import assessment_service

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/heic", "image/heif"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024


def save_image(db: Session, assessment_id: uuid.UUID, upload: UploadFile) -> Image:
    assessment = assessment_service.get_assessment(db, assessment_id)

    if upload.content_type not in ALLOWED_MIME_TYPES:
        raise AppError(415, ErrorCode.UPLOAD_FAILED, "Image must be JPG, PNG, or HEIC")

    contents = upload.file.read()
    if not contents:
        raise AppError(400, ErrorCode.UPLOAD_FAILED, "Uploaded file is empty")
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise AppError(413, ErrorCode.UPLOAD_FAILED, "Image exceeds the 20 MB limit")

    assessment_dir = Path(settings.media_root) / str(assessment_id)
    assessment_dir.mkdir(parents=True, exist_ok=True)

    filename = upload.filename or f"{uuid.uuid4()}.jpg"
    (assessment_dir / filename).write_bytes(contents)

    image = Image(
        assessment_id=assessment.id,
        storage_url=f"{settings.media_base_url}/{assessment_id}/{filename}",
        filename=filename,
        mime_type=upload.content_type,
        file_size_bytes=len(contents),
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def get_latest_image_path(db: Session, assessment_id: uuid.UUID) -> str | None:
    assessment = assessment_service.get_assessment(db, assessment_id)
    if not assessment.images:
        return None
    latest = max(assessment.images, key=lambda img: img.uploaded_at)
    return str(Path(settings.media_root) / str(assessment_id) / latest.filename)
