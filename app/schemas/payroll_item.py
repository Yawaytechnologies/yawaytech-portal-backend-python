from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel


class PayrollItemBase(BaseModel):
    payroll_run_id: int
    employee_id: str
    salary_type: str
    base_amount: float
    currency: str = "INR"
    standard_workdays: int = 0
    per_day_rate: float = 0.0
    per_hour_rate: float = 0.0
    ot_multiplier: float = 1.50
    paid_days: int = 0
    unpaid_days: int = 0
    underwork_hours: float = 0.0
    overtime_hours: float = 0.0
    gross_earnings: float
    total_deductions: float
    net_pay: float
    breakdown_json: Dict[str, Any] = {}


class PayrollItemCreate(PayrollItemBase):
    pass


class PayrollItemUpdate(BaseModel):
    gross_earnings: float | None = None
    total_deductions: float | None = None
    net_pay: float | None = None
    breakdown_json: Dict[str, Any] | None = None


class PayrollItemResponse(PayrollItemBase):
    id: int
    generated_at: datetime

    class Config:
        from_attributes = True
