# app/data/models/shifts.py
from __future__ import annotations
from datetime import date, time
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.data.db import Base


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(30), nullable=False, unique=True, index=True
    )
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    total_hours: Mapped[int] = mapped_column(
        Integer, nullable=False, default=8
    )  # 8h baseline
    is_night: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint("total_hours BETWEEN 1 AND 24", name="ck_shift_total_hours"),
    )


class EmployeeShiftAssignment(Base):
    """
    Effective-dated mapping of employee -> shift.
    Prevent overlapping windows per employee (see Postgres note below).
    """

    __tablename__ = "employee_shift_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    employee_id: Mapped[str] = mapped_column(
        String(9),
        ForeignKey("employees.employee_id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    shift_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("shifts.id", ondelete="RESTRICT"), nullable=False
    )

    effective_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    __table_args__ = (
        Index("ix_shift_assign_emp_from", "employee_id", "effective_from"),
        CheckConstraint(
            "(effective_to IS NULL) OR (effective_to >= effective_from)",
            name="ck_shift_assign_range",
        ),
        UniqueConstraint(
            "employee_id", "shift_id", "effective_from", name="uq_shift_assign_start"
        ),
    )

    # Postgres overlap guard (migration):
    # ALTER TABLE employee_shift_assignments
    #   ADD COLUMN eff_range daterange
    #     GENERATED ALWAYS AS (daterange(effective_from, COALESCE(effective_to, 'infinity'::date), '[]')) STORED;
    # CREATE EXTENSION IF NOT EXISTS btree_gist;
    # ALTER TABLE employee_shift_assignments
    #   ADD CONSTRAINT ex_shift_assign_no_overlap
    #   EXCLUDE USING gist (employee_id WITH =, eff_range WITH &&);
