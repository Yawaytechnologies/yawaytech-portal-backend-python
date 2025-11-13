# app/schemas/leave_me_schemas.py
from __future__ import annotations
from datetime import date, datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, validator


# ---------- TYPES (read-only for the employee) ----------
class LeaveTypeOut(BaseModel):
    id: int
    code: str
    name: str
    unit: str  # "DAY" | "HOUR"
    is_paid: bool
    allow_half_day: bool
    allow_permission_hours: bool


# ---------- BALANCES ----------
class LeaveBalanceOut(BaseModel):
    leave_type_id: int
    leave_type_code: str
    leave_type_name: str
    year: int
    opening: float
    accrued: float
    used: float
    adjusted: float
    closing: float


# ---------- CALENDAR ----------
class CalendarHolidayOut(BaseModel):
    kind: Literal["HOLIDAY"] = "HOLIDAY"
    date: date
    name: str
    is_paid: bool


class CalendarLeaveOut(BaseModel):
    kind: Literal["LEAVE"] = "LEAVE"
    id: int
    leave_type_code: str
    start: datetime
    end: datetime
    requested_unit: str  # "DAY" | "HALF_DAY" | "HOUR"
    approved: bool


class CalendarOut(BaseModel):
    holidays: List[CalendarHolidayOut]
    leaves: List[CalendarLeaveOut]


# ---------- REQUEST CRUD ----------
class LeaveApplyIn(BaseModel):
    leave_type_code: str = Field(..., min_length=2, max_length=16)
    requested_unit: str = Field(..., pattern="^(DAY|HALF_DAY|HOUR)$")
    start_datetime: datetime
    end_datetime: datetime
    requested_hours: Optional[float] = Field(
        None, description="Required when requested_unit=HOUR (permission)."
    )
    reason: Optional[str] = Field(None, max_length=200)

    @validator("end_datetime")
    def _validate_range(cls, v, values):
        start = values.get("start_datetime")
        if start and v < start:
            raise ValueError("end_datetime must be >= start_datetime")
        return v

    @validator("requested_hours")
    def _validate_hours(cls, v, values):
        unit = values.get("requested_unit")
        if unit == "HOUR":
            if v is None or v <= 0:
                raise ValueError("requested_hours is required and must be > 0 for HOUR requests")
        return v


class LeaveRequestOut(BaseModel):
    id: int
    leave_type_code: str
    requested_unit: str
    start_datetime: datetime
    end_datetime: datetime
    requested_hours: Optional[float]
    status: str
    reason: Optional[str]
    created_at: datetime
