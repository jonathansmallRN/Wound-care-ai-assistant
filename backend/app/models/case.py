import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import CaseStatus, enum_values


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    case_ref: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, values_callable=enum_values, name="case_status"),
        nullable=False,
        server_default=CaseStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
