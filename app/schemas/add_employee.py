from __future__ import annotations
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
from fastapi import Form, File, UploadFile
import base64
import binascii

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
    pan_number: str = Field(..., min_length=10, max_length=10)
    aadhar_number: str = Field(..., min_length=12, max_length=12)
    marital_status: MaritalStatus
    permanent_address: str = Field(..., min_length=5)
    designation: str = Field(..., min_length=2, max_length=30)
    department: Department
    profile_picture: Optional[str] = None

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

    @field_validator("profile_picture")
    @classmethod
    def validate_base64_image(cls, v: Optional[str]):
        if v is None:
            return v
        try:
            # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
            if "," in v:
                v = v.split(",")[1]

            # Try to decode the base64 string
            base64.b64decode(v, validate=True)
            return v
        except (binascii.Error, ValueError):
            raise ValueError("Invalid base64 format for profile picture")


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

    pan_number: Optional[str] = Field(None, min_length=10, max_length=10)
    aadhar_number: Optional[str] = Field(None, min_length=12, max_length=12)

    marital_status: Optional[MaritalStatus] = None
    date_of_birth: Optional[date] = None

    # write-only on update too
    password: Optional[str] = Field(None, min_length=8, json_schema_extra={"writeOnly": True})

    permanent_address: Optional[str] = Field(None, min_length=5)
    designation: Optional[str] = Field(None, min_length=2, max_length=30)
    department: Optional[Department] = None
    profile_picture: Optional[str] = None

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
    pan_number: str
    aadhar_number: str
    marital_status: MaritalStatus
    permanent_address: str
    designation: str
    department: Department
    profile_picture: Optional[str] = None

    model_config = {"from_attributes": True}  # pydantic v2


# Form data models for file uploads
class EmployeeCreateForm:
    def __init__(
        self,
        name: str = Form(..., min_length=2, max_length=30),
        father_name: str = Form(..., min_length=2, max_length=30),
        date_of_birth: str = Form(...),  # Will be converted to date
        employee_id: str = Form(..., min_length=EMP_ID_LEN, max_length=EMP_ID_LEN),
        date_of_joining: str = Form(...),  # Will be converted to date
        date_of_leaving: Optional[str] = Form(None),
        email: str = Form(...),
        mobile_number: str = Form(..., min_length=10, max_length=10, pattern=r"^\d{10}$"),
        pan_number: str = Form(..., min_length=10, max_length=10),
        aadhar_number: str = Form(..., min_length=12, max_length=12),
        marital_status: str = Form(...),
        permanent_address: str = Form(..., min_length=5),
        designation: str = Form(..., min_length=2, max_length=30),
        department: str = Form(...),
        password: str = Form(..., min_length=8),
        profile_picture: Optional[UploadFile] = File(None),
    ):
        self.name = name
        self.father_name = father_name
        self.date_of_birth = date_of_birth
        self.employee_id = employee_id
        self.date_of_joining = date_of_joining
        self.date_of_leaving = date_of_leaving
        self.email = email
        self.mobile_number = mobile_number
        self.pan_number = pan_number
        self.aadhar_number = aadhar_number
        self.marital_status = marital_status
        self.permanent_address = permanent_address
        self.designation = designation
        self.department = department
        self.password = password
        self.profile_picture = profile_picture

    def to_employee_create(self) -> EmployeeCreate:
        """Convert form data to EmployeeCreate model"""
        # Convert date strings to date objects
        date_of_birth = date.fromisoformat(self.date_of_birth)
        date_of_joining = date.fromisoformat(self.date_of_joining)
        date_of_leaving = date.fromisoformat(self.date_of_leaving) if self.date_of_leaving else None

        # Convert uploaded file to base64 if present
        profile_picture_base64 = None
        if self.profile_picture and self.profile_picture.filename:
            # Read file content
            file_content = self.profile_picture.file.read()
            # Convert to base64
            profile_picture_base64 = f"data:{self.profile_picture.content_type};base64,{base64.b64encode(file_content).decode()}"

        return EmployeeCreate(
            name=self.name,
            father_name=self.father_name,
            date_of_birth=date_of_birth,
            employee_id=self.employee_id,
            date_of_joining=date_of_joining,
            date_of_leaving=date_of_leaving,
            email=self.email,
            mobile_number=self.mobile_number,
            pan_number=self.pan_number,
            aadhar_number=self.aadhar_number,
            marital_status=MaritalStatus(self.marital_status),
            permanent_address=self.permanent_address,
            designation=self.designation,
            department=Department(self.department),
            password=self.password,
            profile_picture=profile_picture_base64,
        )


class EmployeeUpdateForm:
    def __init__(
        self,
        name: Optional[str] = Form(None, min_length=2, max_length=30),
        father_name: Optional[str] = Form(None, min_length=2, max_length=30),
        employee_id: Optional[str] = Form(None, min_length=EMP_ID_LEN, max_length=EMP_ID_LEN),
        date_of_joining: Optional[str] = Form(None),
        date_of_leaving: Optional[str] = Form(None),
        email: Optional[str] = Form(None),
        mobile_number: Optional[str] = Form(
            None, min_length=10, max_length=10, pattern=r"^\d{10}$"
        ),
        pan_number: Optional[str] = Form(None, min_length=10, max_length=10),
        aadhar_number: Optional[str] = Form(None, min_length=12, max_length=12),
        marital_status: Optional[str] = Form(None),
        date_of_birth: Optional[str] = Form(None),
        password: Optional[str] = Form(None, min_length=8),
        permanent_address: Optional[str] = Form(None, min_length=5),
        designation: Optional[str] = Form(None, min_length=2, max_length=30),
        department: Optional[str] = Form(None),
        profile_picture: Optional[UploadFile] = File(None),
    ):
        self.name = name
        self.father_name = father_name
        self.employee_id = employee_id
        self.date_of_joining = date_of_joining
        self.date_of_leaving = date_of_leaving
        self.email = email
        self.mobile_number = mobile_number
        self.pan_number = pan_number
        self.aadhar_number = aadhar_number
        self.marital_status = marital_status
        self.date_of_birth = date_of_birth
        self.password = password
        self.permanent_address = permanent_address
        self.designation = designation
        self.department = department
        self.profile_picture = profile_picture

    def to_employee_update(self) -> EmployeeUpdate:
        """Convert form data to EmployeeUpdate model"""
        # Convert date strings to date objects
        date_of_birth = date.fromisoformat(self.date_of_birth) if self.date_of_birth else None
        date_of_joining = date.fromisoformat(self.date_of_joining) if self.date_of_joining else None
        date_of_leaving = date.fromisoformat(self.date_of_leaving) if self.date_of_leaving else None

        # Convert uploaded file to base64 if present
        profile_picture_base64 = None
        if self.profile_picture and self.profile_picture.filename:
            # Read file content
            file_content = self.profile_picture.file.read()
            # Convert to base64
            profile_picture_base64 = f"data:{self.profile_picture.content_type};base64,{base64.b64encode(file_content).decode()}"

        return EmployeeUpdate(
            name=self.name,
            father_name=self.father_name,
            employee_id=self.employee_id,
            date_of_joining=date_of_joining,
            date_of_leaving=date_of_leaving,
            email=self.email,
            mobile_number=self.mobile_number,
            pan_number=self.pan_number,
            aadhar_number=self.aadhar_number,
            marital_status=(MaritalStatus(self.marital_status) if self.marital_status else None),
            date_of_birth=date_of_birth,
            password=self.password,
            permanent_address=self.permanent_address,
            designation=self.designation,
            department=Department(self.department) if self.department else None,
            profile_picture=profile_picture_base64,
        )
