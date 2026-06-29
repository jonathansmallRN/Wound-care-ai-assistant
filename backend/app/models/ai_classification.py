import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import HealingClassification, enum_values


class AIClassification(Base):
    __tablename__ = "ai_classifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ai_finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_findings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    classification: Mapped[HealingClassification] = mapped_column(
        Enum(HealingClassification, values_callable=enum_values, name="healing_classification"),
        nullable=False,
    )
    # Weighted sum: (area_signal_score * 0.50) + (tissue_signal_score * 0.30) + (drainage_signal_score * 0.20)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    area_signal_score: Mapped[float] = mapped_column(Float, nullable=False)
    tissue_signal_score: Mapped[float] = mapped_column(Float, nullable=False)
    drainage_signal_score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    ai_finding: Mapped["AIFinding"] = relationship(back_populates="classification")
