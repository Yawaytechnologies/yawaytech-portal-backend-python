# app/schemas/add_employee.py
from __future__ import annotations
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator

from app.data.models.add_employee import MaritalStatus, Department


# Base fields shared by create/update/read
class EmployeeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    father_name: str = Field(..., min_length=2, max_length=120)
    employee_id: str = Field(..., min_length=2, max_length=50)

    date_of_joining: date
    date_of_leaving: Optional[date] = None

    email: EmailStr
    mobile_number: str = Field(..., min_length=7, max_length=20)

    marital_status: MaritalStatus
    date_of_birth: date

    permanent_address: str = Field(..., min_length=5)
    designation: str = Field(..., min_length=2, max_length=120)
    department: Department

    @validator("date_of_leaving")
    def leaving_not_before_joining(cls, v, values):
        doj = values.get("date_of_joining")
        if v and doj and v < doj:
            raise ValueError("Date of Leaving cannot be earlier than Date of Joining")
        return v

    @validator("date_of_birth")
    def dob_before_joining(cls, v, values):
        doj = values.get("date_of_joining")
        if doj and v >= doj:
            raise ValueError("Date of Birth must be earlier than Date of Joining")
        return v


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    # All fields optional for PATCH-like update
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    father_name: Optional[str] = Field(None, min_length=2, max_length=120)
    employee_id: Optional[str] = Field(None, min_length=2, max_length=50)

    date_of_joining: Optional[date] = None
    date_of_leaving: Optional[date] = None

    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = Field(None, min_length=7, max_length=20)

    marital_status: Optional[MaritalStatus] = None
    date_of_birth: Optional[date] = None

    permanent_address: Optional[str] = Field(None, min_length=5)
    designation: Optional[str] = Field(None, min_length=2, max_length=120)
    department: Optional[Department] = None

    @validator("date_of_leaving")
    def leaving_not_before_joining(cls, v, values):
        doj = values.get("date_of_joining")
        if v and doj and v < doj:
            raise ValueError("Date of Leaving cannot be earlier than Date of Joining")
        return v

    @validator("date_of_birth")
    def dob_before_joining(cls, v, values):
        doj = values.get("date_of_joining")
        if doj and v and v >= doj:
            raise ValueError("Date of Birth must be earlier than Date of Joining")
        return v


class EmployeeRead(EmployeeBase):
    id: int

    class Config:
        from_attributes = True  # Pydantic v2 (or orm_mode=True for v1)
