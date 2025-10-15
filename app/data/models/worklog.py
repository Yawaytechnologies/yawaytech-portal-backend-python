from __future__ import annotations
from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.data.db import Base
from app.data.models.add_employee import Employee


class WorkType(str, Enum):
    FEATURE = "Feature"
    BUG_FIX = "Bug Fix"
    MEETING = "Meeting"
    TRAINING = "Training"
    SUPPORT = "Support"
    OTHER = "Other"


class WorklogStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class Worklog(Base):
    __tablename__ = "worklogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    employee_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    work_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    task: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)  # Auto-calculated

    work_type: Mapped[WorkType | None] = mapped_column(SAEnum(WorkType), nullable=True)

    status: Mapped[WorklogStatus] = mapped_column(
        SAEnum(WorklogStatus), default=WorklogStatus.TODO, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", foreign_keys=[employee_id])
