import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, enum_values

class Sex(str, enum.Enum):
    MALE = "M"
    FEMALE = "F"


class Athlete(Base):
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(primary_key=True)
    coach_id: Mapped[int] = mapped_column(
        ForeignKey("coaches.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    birth_date: Mapped[date] = mapped_column(Date)
    sex: Mapped[Sex] = mapped_column(
    Enum(Sex, native_enum=False, length=1, values_callable=enum_values))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    coach: Mapped["Coach"] = relationship(back_populates="athletes")
    sessions: Mapped[list["TrainingSession"]] = relationship(
        back_populates="athlete", cascade="all, delete-orphan"
    )