# app/data/models/policy.py
from __future__ import annotations
from datetime import date
from typing import Optional, Dict

from sqlalchemy import Boolean, Date, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.data.db import Base


class WorkweekPolicy(Base):
    __tablename__ = "workweek_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region: Mapped[str] = mapped_column(String(8), nullable=False, unique=True, index=True)
    # e.g. {"mon":true,"tue":true,"wed":true,"thu":true,"fri":true,"sat":"1st,3rd","sun":false}
    policy_json: Mapped[Dict] = mapped_column(JSONB, nullable=False, server_default="{}")


class HolidayCalendar(Base):
    __tablename__ = "holiday_calendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    holiday_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    region: Mapped[Optional[str]] = mapped_column(String(8), index=True)
    recurs_annually: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (Index("ix_holiday_region_date", "region", "holiday_date"),)
