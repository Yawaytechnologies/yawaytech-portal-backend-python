from __future__ import annotations
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from enum import Enum


# ---------- Leave Types ----------
class LeaveTypeCreate(BaseModel):
    code: str = Field(..., pattern=r"^[A-Z]{2,16}$")
    name: str
    unit: str = Field(..., pattern=r"^(DAY|HOUR)$")
    is_paid: bool = True
    allow_half_day: bool = False
    allow_permission_hours: bool = False
    duration_days: int = Field(..., ge=0)
    monthly_limit: int = Field(..., ge=0)
    yearly_limit: int = Field(..., ge=0)
    carry_forward_allowed: bool = False


class LeaveTypeUpdate(BaseModel):
    name: Optional[str] = None
    is_paid: Optional[bool] = None
    allow_half_day: Optional[bool] = None
    allow_permission_hours: Optional[bool] = None


# ---------- Holidays ----------
class HolidayCreate(BaseModel):
    holiday_date: date
    name: str
    is_paid: bool = True
    region: Optional[str] = None
    recurs_annually: bool = False


class HolidayUpdate(BaseModel):
    name: Optional[str] = None
    is_paid: Optional[bool] = None
    region: Optional[str] = None
    recurs_annually: Optional[bool] = None


class HolidayResponse(BaseModel):
    id: int
    holiday_date: date
    name: str
    is_paid: bool
    region: Optional[str] = None
    recurs_annually: bool


# ---------- Balances ----------
class BalanceSeedItem(BaseModel):
    leave_type_code: str
    opening_hours: float = 0.0


class BalanceSeedPayload(BaseModel):
    employee_id: str
    year: int
    items: List[BalanceSeedItem]


class BalanceAdjustPayload(BaseModel):
    employee_id: str
    year: int
    leave_type_code: str
    delta_hours: float
    reason: Optional[str] = None


class AccrualRunPayload(BaseModel):
    year: int
    month: int
    employee_ids: List[str]
    # Map leave_type_code -> hours to accrue this month (kept explicit so you don't need schema changes)
    per_type_hours: Dict[str, float] = Field(default_factory=dict)


# ---------- Requests ----------
class LeaveRequestCreate(BaseModel):
    employee_id: str
    leave_type_code: str
    start_datetime: datetime
    end_datetime: datetime
    requested_unit: str  # DAY | HALF_DAY | HOUR
    requested_hours: Optional[float] = None
    reason: Optional[str] = None

    @validator("requested_unit")
    def _unit_ok(cls, v):
        if v not in {"DAY", "HALF_DAY", "HOUR"}:
            raise ValueError("requested_unit must be DAY|HALF_DAY|HOUR")
        return v

    @validator("requested_hours")
    def _hours_needed_for_hour_unit(cls, v, values):
        if values.get("requested_unit") == "HOUR" and (v is None or v <= 0):
            raise ValueError("requested_hours required for HOUR unit")
        return v


class LeaveDecisionPayload(BaseModel):
    class Decision(str, Enum):
        APPROVED = "APPROVED"
        REJECTED = "REJECTED"

    decision: Decision
    approver_employee_id: str
    note: Optional[str] = None


# ---------- Queries ----------
class HolidaysQuery(BaseModel):
    start: date
    end: date
    region: Optional[str] = None


# ---------- Leave Request Response ----------
class LeaveRequestResponse(BaseModel):
    id: int
    employee_id: str
    employee_name: str
    leave_type_code: str
    start_date: date
    end_date: date
    requested_unit: str
    requested_hours: Optional[float] = None
    requested_days: float
    status: str
    reason: Optional[str] = None
    created_at: datetime
    approver_employee_id: Optional[str] = None
    decided_at: Optional[datetime] = None
