# app/data/models/monthly_summary.py
from __future__ import annotations
from datetime import date, datetime
from sqlalchemy import (
    Integer, String, Date, DateTime, Numeric, Index, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.data.db import Base

class MonthlyEmployeeSummary(Base):
    __tablename__ = "monthly_employee_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(9), index=True, nullable=False)
    month_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Attendance counts
    total_work_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    present_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    holiday_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    weekend_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    leave_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Leave breakdown (normalized to hours)
    paid_leave_hours: Mapped[float] = mapped_column(Numeric(8,2), default=0, nullable=False)
    unpaid_leave_hours: Mapped[float] = mapped_column(Numeric(8,2), default=0, nullable=False)
    pending_leave_hours: Mapped[float] = mapped_column(Numeric(8,2), default=0, nullable=False)
    paid_leave_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unpaid_leave_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pending_leave_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


    # Work metrics
    total_worked_hours: Mapped[float] = mapped_column(Numeric(10,2), default=0, nullable=False)
    expected_hours: Mapped[float] = mapped_column(Numeric(10,2), default=0, nullable=False)
    overtime_hours: Mapped[float] = mapped_column(Numeric(10,2), default=0, nullable=False)
    underwork_hours: Mapped[float] = mapped_column(Numeric(10,2), default=0, nullable=False)

    # Optional JSON breakdown for audit/reporting
    leave_type_breakdown: Mapped[dict] = mapped_column(JSONB, server_default="{}", nullable=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("employee_id", "month_start", name="uq_monthly_summary_emp_month"),
        Index("ix_monthly_summary_emp_month", "employee_id", "month_start"),
    )