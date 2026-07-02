import re
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

_MIME_TO_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/heic": ".heic",
    "image/heif": ".heif",
}


def _storage_filename(original: str | None, mime_type: str) -> str:
    """Return a UUID-based storage filename with a safe extension.

    The UUID prefix prevents both path traversal (no ../ ever reaches the
    filesystem) and silent overwrite (unique key per upload regardless of the
    original filename). The caller-supplied filename is never used as a storage
    path component — only its extension (after sanitization) is considered.
    """
    ext = _MIME_TO_EXT.get(mime_type)
    if ext is None and original:
        # Collapse backslash separators then take only the final component
        # so that "../../evil.jpg" → "evil.jpg" → ".jpg".
        safe_name = Path(original.replace("\\", "/")).name
        candidate = Path(safe_name).suffix.lower()
        # Accept only simple alphanumeric extensions ≤ 10 chars.
        if re.match(r"^\.[a-z0-9]{1,10}$", candidate):
            ext = candidate
    return f"{uuid.uuid4()}{ext or '.jpg'}"


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

    # UUID-based storage key — the original filename never touches the filesystem.
    storage_name = _storage_filename(upload.filename, upload.content_type)
    (assessment_dir / storage_name).write_bytes(contents)

    image = Image(
        assessment_id=assessment.id,
        storage_url=f"{settings.media_base_url}/{assessment_id}/{storage_name}",
        filename=storage_name,
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
