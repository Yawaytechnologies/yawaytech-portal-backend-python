# app/data/models/shift_grace_policy.py
from __future__ import annotations
from datetime import date
from typing import Optional
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SAEnum

from app.data.db import Base


# Enum definitions for clarity
class GraceType(str, Enum):
    BEFORE_START = "BEFORE_START"
    AFTER_END = "AFTER_END"
    BOTH = "BOTH"


class AppliesTo(str, Enum):
    LATE_ARRIVAL = "LATE_ARRIVAL"
    EARLY_EXIT = "EARLY_EXIT"
    UNDERWORK = "UNDERWORK"


class ShiftGracePolicy(Base):
    __tablename__ = "shift_grace_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    shift_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("shifts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    grace_type: Mapped[GraceType] = mapped_column(
        SAEnum(GraceType, name="grace_type_enum"), nullable=False
    )

    applies_to: Mapped[AppliesTo] = mapped_column(
        SAEnum(AppliesTo, name="applies_to_enum"), nullable=False
    )

    excused_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("excused_minutes BETWEEN 0 AND 120", name="ck_grace_minutes"),
        UniqueConstraint("shift_id", "applies_to", "effective_from", name="uq_grace_policy"),
        Index("ix_grace_policy_shift", "shift_id", "effective_from"),
    )
