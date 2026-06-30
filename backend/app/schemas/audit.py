from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    service_name: str
    model_version: str | None
    latency_ms: int | None
    success: bool
    created_at: datetime

    model_config = {"from_attributes": True}
