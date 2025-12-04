# app/schemas/employee_salary.py
from pydantic import BaseModel
from typing import Optional, List
from app.schemas.salary_breakdown import SalaryBreakdownRead


class EmployeeSalaryBase(BaseModel):
    employee_id: int
    base_salary: float
    payroll_policy_id: Optional[int] = None


class EmployeeSalaryCreate(EmployeeSalaryBase):
    pass


class EmployeeSalaryUpdate(BaseModel):
    base_salary: Optional[float] = None
    payroll_policy_id: Optional[int] = None


class EmployeeSalaryRead(EmployeeSalaryBase):
    id: int
    gross_salary: float
    breakdowns: List[SalaryBreakdownRead] = []

    class Config:
        from_attributes = True
