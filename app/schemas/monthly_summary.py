from datetime import date, datetime
from typing import Optional, Dict
from pydantic import BaseModel

class MonthlySummaryBase(BaseModel):
    employee_id: str
    month_start: date
    total_work_days: int
    present_days: int
    holiday_days: int
    weekend_days: int
    leave_days: int
    paid_leave_hours: float
    unpaid_leave_hours: float
    pending_leave_hours: float
    total_worked_hours: float
    expected_hours: float
    overtime_hours: float
    underwork_hours: float
    leave_type_breakdown: Optional[Dict[str, float]] = {}

class MonthlySummarySchema(MonthlySummaryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True   # replaces orm_mode in Pydantic v2