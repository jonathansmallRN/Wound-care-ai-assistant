import uuid

from pydantic import BaseModel


class ImageUploadOut(BaseModel):
    image_id: uuid.UUID
    storage_url: str
    filename: str
    file_size_bytes: int
