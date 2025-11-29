from datetime import date, time
from typing import Optional
from pydantic import BaseModel

class ShiftBase(BaseModel):
    name: str
    start_time: time
    end_time: time
    total_hours: int
    is_night: bool = False

class ShiftCreate(ShiftBase):
    pass

class ShiftSchema(ShiftBase):
    id: int
    class Config: orm_mode = True

class EmployeeShiftAssignmentBase(BaseModel):
    employee_id: str
    shift_id: int
    effective_from: date
    effective_to: Optional[date] = None

class EmployeeShiftAssignmentCreate(EmployeeShiftAssignmentBase):
    pass

class EmployeeShiftAssignmentSchema(EmployeeShiftAssignmentBase):
    id: int
    class Config: orm_mode = True