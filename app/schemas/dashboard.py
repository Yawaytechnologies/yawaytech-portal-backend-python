from __future__ import annotations
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, ConfigDict
from app.data.models.add_employee import Department


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    father_name: str
    date_of_birth: date
    employee_id: str
    date_of_joining: date
    date_of_leaving: Optional[date] = None
    email: str
    mobile_number: str
    marital_status: str
    permanent_address: str
    designation: str
    department: Department

    profile_picture: Optional[str] = None


class EmployeesPage(BaseModel):
    items: List[EmployeeOut]
    total: int
    limit: int
    offset: int
