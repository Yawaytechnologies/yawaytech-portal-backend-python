from __future__ import annotations
from datetime import datetime, date
from pydantic import BaseModel, Field

from typing import List, Optional

from app.data.models.attendance import DayStatus


class CheckInResponse(BaseModel):
    sessionId: int
    employeeId: str
    checkInUtc: datetime
    workDateLocal: date


class CheckOutResponse(BaseModel):
    sessionId: int
    employeeId: str
    checkInUtc: datetime
    checkOutUtc: datetime
    workedSeconds: int


class TodayStatus(BaseModel):
    employeeId: str
    workDateLocal: date
    openSessionId: int | None
    openSinceUtc: datetime | None
    secondsWorkedSoFar: int
    present: bool


class MonthDay(BaseModel):
    date: date
    secondsWorked: int
    present: bool


class AttendanceDayItem(BaseModel):
    work_date_local: date
    seconds_worked: int = 0
    hours_worked: str = Field(..., description="HH:MM")
    status: DayStatus
    first_check_in_utc: Optional[datetime] = None
    last_check_out_utc: Optional[datetime] = None


class EmployeeAttendanceResponse(BaseModel):
    employee_id: str
    employee_name: str | None = None
    date_from: date
    date_to: date
    total_days: int
    present_days: int
    absent_days: int
    items: List[AttendanceDayItem]


class MonthlyAttendanceItem(BaseModel):
    month: int  # 1..12
    month_name: str
    seconds_worked: int
    hours_worked: str = Field(..., description="HH:MM")
    present_days: int
    absent_days: int
    days_counted: int  # how many calendar days considered for this month


class EmployeeYearlyAttendanceResponse(BaseModel):
    employee_id: str
    employee_name: str | None = None
    year: int
    total_seconds_worked: int
    total_hours_worked: str
    total_present_days: int
    total_absent_days: int
    months: List[MonthlyAttendanceItem]


class EmployeeMonthlyAttendanceResponse(BaseModel):
    employee_id: str
    employee_name: str | None = None
    year: int
    month: int  # 1..12
    month_name: str
    days_counted: int
    present_days: int
    absent_days: int
    total_seconds_worked: int
    total_hours_worked: str = Field(..., description="HH:MM")
    avg_hours_per_present_day: str = Field(..., description="HH:MM")
    items: List[AttendanceDayItem]


class VisitedSite(BaseModel):
    url: str
    title: str
    visited_at: str  # ISO format datetime string


class CheckInMonitoringItem(BaseModel):
    id: int
    session_id: int
    monitored_at_utc: datetime
    cpu_percent: float | None = None
    memory_percent: float | None = None
    active_apps: List[str]
    visited_sites: List[VisitedSite]


class EmployeeCheckInMonitoringResponse(BaseModel):
    employee_id: str
    employee_name: str | None = None
    items: List[CheckInMonitoringItem]
