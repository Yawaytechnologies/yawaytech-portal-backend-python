from __future__ import annotations
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator

from app.data.models.add_employee import MaritalStatus, Department


EMP_ID_LEN = 9


# Shared base (no read/write-only tricks here)
class EmployeeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=30)
    father_name: str = Field(..., min_length=2, max_length=30)
    date_of_birth: date
    employee_id: str = Field(..., min_length=EMP_ID_LEN, max_length=EMP_ID_LEN)
    date_of_joining: date
    date_of_leaving: Optional[date] = None
    email: EmailStr
    mobile_number: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{10}$")
    marital_status: MaritalStatus
    permanent_address: str = Field(..., min_length=5)
    designation: str = Field(..., min_length=2, max_length=30)
    department: Department

    @field_validator("date_of_leaving")
    @classmethod
    def leaving_not_before_joining(cls, v: Optional[date], info):
        doj = info.data.get("date_of_joining")
        if v and doj and v < doj:
            raise ValueError("Date of Leaving cannot be earlier than Date of Joining")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def dob_before_joining(cls, v: date, info):
        doj = info.data.get("date_of_joining")
        if doj and v >= doj:
            raise ValueError("Date of Birth must be earlier than Date of Joining")
        return v


class EmployeeCreate(EmployeeBase):
    # password is write-only: accepted on input, never returned
    password: str = Field(
        ...,
        min_length=8,
        json_schema_extra={"writeOnly": True},
    )


class EmployeeUpdate(BaseModel):
    # All optional (PATCH semantics)
    name: Optional[str] = Field(None, min_length=2, max_length=30)
    father_name: Optional[str] = Field(None, min_length=2, max_length=30)
    employee_id: Optional[str] = Field(None, min_length=EMP_ID_LEN, max_length=EMP_ID_LEN)

    date_of_joining: Optional[date] = None
    date_of_leaving: Optional[date] = None

    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = Field(None, min_length=10, max_length=10, pattern=r"^\d{10}$")

    marital_status: Optional[MaritalStatus] = None
    date_of_birth: Optional[date] = None

    # write-only on update too
    password: Optional[str] = Field(
        None, min_length=8, json_schema_extra={"writeOnly": True}
    )

    permanent_address: Optional[str] = Field(None, min_length=5)
    designation: Optional[str] = Field(None, min_length=2, max_length=30)
    department: Optional[Department] = None

    @field_validator("date_of_leaving")
    @classmethod
    def leaving_not_before_joining(cls, v: Optional[date], info):
        doj = info.data.get("date_of_joining")
        if v and doj and v < doj:
            raise ValueError("Date of Leaving cannot be earlier than Date of Joining")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def dob_before_joining(cls, v: Optional[date], info):
        doj = info.data.get("date_of_joining")
        if doj and v and v >= doj:
            raise ValueError("Date of Birth must be earlier than Date of Joining")
        return v


class EmployeeRead(BaseModel):
    id: int
    name: str
    father_name: str
    date_of_birth: date
    employee_id: str
    date_of_joining: date
    date_of_leaving: Optional[date] = None
    email: EmailStr
    mobile_number: str
    marital_status: MaritalStatus
    permanent_address: str
    designation: str
    department: Department

    model_config = {"from_attributes": True}  # pydantic v2
