import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AIFinding(Base):
    __tablename__ = "ai_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    model_version: Mapped[str] = mapped_column(String, nullable=False)
    vision_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Null for baseline assessments (no prior assessment to compare) and when ai_available is False.
    area_delta_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    tissue_change: Mapped[str | None] = mapped_column(String, nullable=True)
    drainage_change: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    assessment: Mapped["Assessment"] = relationship(back_populates="ai_finding")
    classification: Mapped["AIClassification | None"] = relationship(
        back_populates="ai_finding", uselist=False, cascade="all, delete-orphan"
    )
