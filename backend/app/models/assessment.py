import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import HealingClassification, ReviewStatus, enum_values


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_baseline: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    length_cm: Mapped[float] = mapped_column(Float, nullable=False)
    width_cm: Mapped[float] = mapped_column(Float, nullable=False)
    depth_cm: Mapped[float] = mapped_column(Float, nullable=False)
    # Computed once on save (length_cm * width_cm and length_cm * width_cm * depth_cm) — never recalculated at query time.
    area_cm2: Mapped[float] = mapped_column(Float, nullable=False)
    volume_cm3: Mapped[float] = mapped_column(Float, nullable=False)

    tissue_type: Mapped[str] = mapped_column(String, nullable=False)
    drainage_amount: Mapped[str] = mapped_column(String, nullable=False)
    drainage_type: Mapped[str] = mapped_column(String, nullable=False)
    periwound: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, values_callable=enum_values, name="review_status"),
        nullable=False,
        server_default=ReviewStatus.PENDING.value,
    )
    clinician_classification: Mapped[HealingClassification | None] = mapped_column(
        Enum(HealingClassification, values_callable=enum_values, name="healing_classification"),
        nullable=True,
    )
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    note_draft: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    case: Mapped["Case"] = relationship(back_populates="assessments")
    images: Mapped[list["Image"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    ai_finding: Mapped["AIFinding | None"] = relationship(
        back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )
    validation_review: Mapped["ValidationReview | None"] = relationship(
        back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
