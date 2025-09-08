# app/schemas/employee.py
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Enums (for dropdowns/radios) ---

class MaritalStatus(str, Enum):
    SINGLE = "Single"
    MARRIED = "Married"
    


class GuardianType(str, Enum):
    PARENT = "Parent"
    GUARDIAN = "Guardian"


# --- Base (shared fields) ---

class EmployeeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    parent_name: str = Field(..., min_length=2, max_length=120)
    guardian_type: GuardianType = Field(default=GuardianType.PARENT)

    employee_id: str = Field(..., min_length=3, max_length=30)  # display id/code
    email: EmailStr
    mobile_number: str = Field(..., min_length=8, max_length=15, description="Digits with optional +country code")
    alternative_number: Optional[str] = Field(None, min_length=8, max_length=15)

    designation: str = Field(..., min_length=2, max_length=80)
    permanent_address: str = Field(..., min_length=5, max_length=500)

    marital_status: MaritalStatus
    date_of_birth: date
    date_of_joining: date
    date_of_leaving: Optional[date] = None

    uan_number: Optional[str] = Field(None, min_length=8, max_length=20, description="Typically 12-digit in India")

    @field_validator("mobile_number", "alternative_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]):
        if v is None:
            return v
        import re
        # Simple allow: +, digits, spaces, dashes. Ensure at least 10 digits total.
        cleaned = re.sub(r"[^\d]", "", v)
        if len(cleaned) < 10:
            raise ValueError("Phone number must contain at least 10 digits")
        return v

    @field_validator("uan_number")
    @classmethod
    def validate_uan(cls, v: Optional[str]):
        if v is None:
            return v
        # Not all UANs are exactly 12 digits in old data; enforce numeric & 8-20 len
        if not v.isdigit():
            raise ValueError("UAN must be numeric")
        if not (8 <= len(v) <= 20):
            raise ValueError("UAN must be between 8 and 20 digits")
        return v

    @field_validator("date_of_leaving")
    @classmethod
    def leaving_after_join(cls, leaving: Optional[date], info):
        if not leaving:
            return leaving
        joining = info.data.get('date_of_joining')
        if joining and leaving < joining:
            raise ValueError("Date of leaving must be after date of joining")
        return leaving


# --- Create ---

class EmployeeCreate(EmployeeBase):
    pass


# --- Update ---

class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    parent_name: Optional[str] = Field(None, min_length=2, max_length=120)
    guardian_type: Optional[GuardianType] = None
    employee_id: Optional[str] = Field(None, min_length=3, max_length=30)
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = Field(None, min_length=8, max_length=15)
    alternative_number: Optional[str] = Field(None, min_length=8, max_length=15)
    designation: Optional[str] = Field(None, min_length=2, max_length=80)
    permanent_address: Optional[str] = Field(None, min_length=5, max_length=500)
    marital_status: Optional[MaritalStatus] = None
    date_of_birth: Optional[date] = None
    date_of_joining: Optional[date] = None
    date_of_leaving: Optional[date] = None
    uan_number: Optional[str] = Field(None, min_length=8, max_length=20)


# --- Read ---

class EmployeeRead(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime
