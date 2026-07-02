import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import FitzpatrickScale, HealingClassification, ReviewerVerdict, enum_values


class ValidationReview(Base):
    __tablename__ = "validation_reviews"

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
    # Nullable in V1 — records still write without clinician login; populates as login is added.
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinicians.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ai_classification: Mapped[HealingClassification | None] = mapped_column(
        Enum(HealingClassification, values_callable=enum_values, name="healing_classification"),
        nullable=True,
    )
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    clinician_classification: Mapped[HealingClassification] = mapped_column(
        Enum(HealingClassification, values_callable=enum_values, name="healing_classification"),
        nullable=False,
    )
    match: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ai_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    fitzpatrick_scale: Mapped[FitzpatrickScale | None] = mapped_column(
        Enum(FitzpatrickScale, values_callable=enum_values, name="fitzpatrick_scale"),
        nullable=True,
    )
    reviewer_verdict: Mapped[ReviewerVerdict | None] = mapped_column(
        Enum(ReviewerVerdict, values_callable=enum_values, name="reviewer_verdict"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    assessment: Mapped["Assessment"] = relationship(back_populates="validation_review")
    reviewer: Mapped["Clinician | None"] = relationship(back_populates="validation_reviews")
