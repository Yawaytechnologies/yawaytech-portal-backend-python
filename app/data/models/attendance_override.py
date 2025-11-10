# app/data/models/attendance_override.py
from __future__ import annotations
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.data.db import Base


class AttendanceOverride(Base):
    """
    Admin-issued corrections for a specific day. Your rollup can apply these
    values instead of directly editing attendance_days, keeping a full audit trail.
    """

    __tablename__ = "attendance_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[str] = mapped_column(
        String(9),
        ForeignKey("employees.employee_id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    work_date_local: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # sparse fields; any provided key overrides the computed value in rollup
    patch_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    note: Mapped[Optional[str]] = mapped_column(Text)

    acted_by: Mapped[str] = mapped_column(
        String(40), nullable=False
    )  # admin user id/email
    acted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
