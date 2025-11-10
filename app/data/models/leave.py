# app/data/models/leave.py
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
from app.data.db import Base


class LeaveUnit(str, Enum):
    DAY = "DAY"
    HOUR = "HOUR"  # used for Permission


class LeaveRequestUnit(str, Enum):
    DAY = "DAY"
    HALF_DAY = "HALF_DAY"
    HOUR = "HOUR"


class LeaveStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"


class LeaveType(Base):
    __tablename__ = "leave_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(
        String(16), unique=True, nullable=False, index=True
    )  # CL/SL/PL/PM
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    unit: Mapped[LeaveUnit] = mapped_column(
        SAEnum(LeaveUnit, name="leave_unit_enum"), nullable=False
    )
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_half_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_permission_hours: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    __table_args__ = (
        CheckConstraint("code ~ '^[A-Z]{2,16}$'", name="ck_leave_type_code"),
    )


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    employee_id: Mapped[str] = mapped_column(
        String(9),
        ForeignKey("employees.employee_id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    leave_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("leave_types.id", ondelete="RESTRICT"), nullable=False
    )

    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    requested_unit: Mapped[LeaveRequestUnit] = mapped_column(
        SAEnum(LeaveRequestUnit, name="leave_req_unit_enum"), nullable=False
    )
    requested_hours: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # for HOUR

    status: Mapped[LeaveStatus] = mapped_column(
        SAEnum(LeaveStatus, name="leave_status_enum"),
        nullable=False,
        default=LeaveStatus.PENDING,
    )
    approver_employee_id: Mapped[Optional[str]] = mapped_column(
        String(9), ForeignKey("employees.employee_id"), nullable=True
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reason: Mapped[Optional[str]] = mapped_column(String(200))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("end_datetime >= start_datetime", name="ck_leave_req_range"),
    )


class LeaveBalance(Base):
    """
    Optional but recommended. Tracks annual leave accounting.
    """

    __tablename__ = "leave_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    employee_id: Mapped[str] = mapped_column(
        String(9),
        ForeignKey("employees.employee_id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    leave_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("leave_types.id", ondelete="RESTRICT"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    opening: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    accrued: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    used: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    adjusted: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    closing: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "leave_type_id",
            "year",
            name="uq_leave_balance_emp_type_year",
        ),
        Index("ix_leave_balance_emp_year", "employee_id", "year"),
        CheckConstraint("year BETWEEN 1970 AND 2100", name="ck_leave_balance_year"),
    )
