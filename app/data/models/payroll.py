# app/data/models/payroll.py
from __future__ import annotations
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.db import Base
# We use the business key "employees.employee_id" (string) just like your attendance module.

# ──────────────────────────────────────────────────────────────────────────────
# Salary (versioned per employee)
# ──────────────────────────────────────────────────────────────────────────────

class EmployeeSalary(Base):
    """
    Versioned salary for an employee. Use effective dates so payroll for any
    past month can pick the correct rate.
    """
    __tablename__ = "employee_salary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # FK to business key (YTP000003). If you prefer int PK, change to employees.id.
    employee_id: Mapped[str] = mapped_column(
        String(9), ForeignKey("employees.employee_id", ondelete="RESTRICT"), index=True, nullable=False
    )

    # MONTHLY or HOURLY
    salary_type: Mapped[str] = mapped_column(String(8), nullable=False, default="MONTHLY")
    base_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)  # e.g., 57000.00
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")

    effective_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_emp_salary_emp_from", "employee_id", "effective_from"),
        CheckConstraint("salary_type IN ('MONTHLY','HOURLY')", name="ck_emp_salary_type"),
    )

    # RECOMMENDED (migration note):
    # For Postgres, prevent overlapping versions per employee with a daterange exclude:
    #   ALTER TABLE employee_salary
    #     ADD COLUMN eff_range daterange
    #       GENERATED ALWAYS AS (daterange(effective_from, COALESCE(effective_to, 'infinity'::date), '[]')) STORED;
    #   CREATE EXTENSION IF NOT EXISTS btree_gist;
    #   ALTER TABLE employee_salary
    #     ADD CONSTRAINT ex_emp_salary_no_overlap
    #     EXCLUDE USING gist (employee_id WITH =, eff_range WITH &&);


# ──────────────────────────────────────────────────────────────────────────────
# Pay periods (usually one per month)
# ──────────────────────────────────────────────────────────────────────────────

class PayPeriod(Base):
    """
    A payroll window (typically one calendar month). Locking a period prevents
    retro changes in attendance_days and further recomputes.
    """
    __tablename__ = "pay_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(7), nullable=False, unique=True, index=True)  # e.g., "2025-09"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("start_date <= end_date", name="ck_period_range"),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Payroll runs (you can have multiple drafts, then finalize one)
# ──────────────────────────────────────────────────────────────────────────────

class PayrollRun(Base):
    """
    A calculation event for a period. You may keep multiple DRAFT runs,
    then finalize one. Items are linked to a run.
    """
    __tablename__ = "payroll_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    pay_period_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pay_periods.id", ondelete="CASCADE"), index=True, nullable=False
    )
    run_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # e.g., 1,2,3...
    run_status: Mapped[str] = mapped_column(String(16), nullable=False, default="Draft")  # Draft/Finalized
    created_by: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    period: Mapped["PayPeriod"] = relationship("PayPeriod", viewonly=True)

    __table_args__ = (
        UniqueConstraint("pay_period_id", "run_no", name="uq_payroll_run_period_no"),
        CheckConstraint("run_status IN ('Draft','Finalized')", name="ck_run_status"),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Payroll items (one per employee in a run)
# ──────────────────────────────────────────────────────────────────────────────

class PayrollItem(Base):
    """
    Final (or draft) computed money for one employee in a given run.
    Cache rates & counts here so historical payslips survive policy/salary edits.
    """
    __tablename__ = "payroll_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    payroll_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payroll_runs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    employee_id: Mapped[str] = mapped_column(
        String(9), ForeignKey("employees.employee_id", ondelete="RESTRICT"), index=True, nullable=False
    )

    # Cached context for audit/replay
    salary_type: Mapped[str] = mapped_column(String(8), nullable=False)          # MONTHLY|HOURLY
    base_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)   # the version used
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")

    # Rates derived during calculation (cache them)
    standard_workdays: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # working weekdays minus paid holidays
    per_day_rate: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    per_hour_rate: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    ot_multiplier: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=1.50)

    # Summaries taken from attendance_days rollups
    paid_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unpaid_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    underwork_hours: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    overtime_hours: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0)

    # Money
    gross_earnings: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)    # components + OT
    total_deductions: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)  # underwork/unpaid/others
    net_pay: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Human-readable split (OT ₹, Unpaid ₹, Underwork ₹, Bonus, Advance, etc.)
    breakdown_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    run: Mapped["PayrollRun"] = relationship("PayrollRun", viewonly=True)

    __table_args__ = (
        UniqueConstraint("payroll_run_id", "employee_id", name="uq_payroll_items_run_emp"),
        CheckConstraint("gross_earnings >= 0", name="ck_payroll_items_gross_nonneg"),
        CheckConstraint("total_deductions >= 0", name="ck_payroll_items_ded_nonneg"),
        CheckConstraint("net_pay >= 0", name="ck_payroll_items_net_nonneg"),
    )
