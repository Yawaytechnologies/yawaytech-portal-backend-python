from __future__ import annotations
from datetime import datetime, date
from sqlalchemy import (
    Integer,
    String,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.data.db import Base
from app.data.models.add_employee import Employee


# Raw punches (each check-in/out pair); timestamps are stored in UTC (tz-aware).
class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # FK to your add_employee.Employee.business key (employee_id)
    employee_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    check_in_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    check_out_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Local IST date at check-in moment (for calendar grouping)
    work_date_local: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    # optional ORM relation (no cyclic import required)
    employee: Mapped["Employee"] = relationship("Employee", viewonly=True)

    __table_args__ = (
        Index("ix_session_emp_open", "employee_id", "check_out_utc"),
        CheckConstraint(
            "(check_out_utc IS NULL) OR (check_out_utc >= check_in_utc)",
            name="ck_session_chronology",
        ),
    )


# Daily rollup (one row per employee per local day)
class AttendanceDay(Base):
    __tablename__ = "attendance_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    employee_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    work_date_local: Mapped[date] = mapped_column(Date, nullable=False)

    seconds_worked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_check_in_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_check_out_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    status: Mapped[str] = mapped_column(String(20), default="PRESENT", nullable=False)

    employee: Mapped["Employee"] = relationship("Employee", viewonly=True)

    __table_args__ = (
        UniqueConstraint("employee_id", "work_date_local", name="uq_attendance_day"),
        Index("ix_attendance_day_emp_month", "employee_id", "work_date_local"),
        CheckConstraint("seconds_worked >= 0", name="ck_day_nonnegative"),
    )
