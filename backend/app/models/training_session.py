import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint, Date, DateTime, Enum, ForeignKey, Integer, Numeric, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, enum_values

class SessionType(str, enum.Enum):
    TRAINING = "training"
    COMPETITION = "competition"


class Stroke(str, enum.Enum):
    FREESTYLE = "freestyle"
    BACKSTROKE = "backstroke"
    BREASTSTROKE = "breaststroke"
    BUTTERFLY = "butterfly"
    MEDLEY = "medley"


class TrainingSession(Base):
    __tablename__ = "training_sessions"
    __table_args__ = (
        CheckConstraint("pool_length_m IN (25, 50)", name="ck_pool_length"),
        CheckConstraint("distance_m > 0", name="ck_distance_positive"),
        CheckConstraint("total_time_s > 0", name="ck_total_time_positive"),
        CheckConstraint("stroke_count >= 0", name="ck_stroke_count_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(
        ForeignKey("athletes.id", ondelete="CASCADE"), index=True
    )
    session_date: Mapped[date] = mapped_column(Date, index=True)
    session_type: Mapped[SessionType] = mapped_column(
    Enum(SessionType, native_enum=False, length=20, values_callable=enum_values)
    )
    stroke: Mapped[Stroke] = mapped_column(
        Enum(Stroke, native_enum=False, length=20, values_callable=enum_values)
    )
    
    pool_length_m: Mapped[int] = mapped_column(Integer)
    distance_m: Mapped[int] = mapped_column(Integer)
    total_time_s: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    stroke_count: Mapped[int] = mapped_column(Integer)
    # Trecho de nado puro (sem saída e viradas), usado em VN e Cadência
    swim_distance_m: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    swim_time_s: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    athlete: Mapped["Athlete"] = relationship(back_populates="sessions")