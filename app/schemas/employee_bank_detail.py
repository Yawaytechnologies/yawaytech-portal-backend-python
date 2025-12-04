# app/schemas/employee_bank_detail.py
from pydantic import BaseModel
from typing import Optional


class EmployeeBankDetailBase(BaseModel):
    employee_id: int
    bank_name: str
    account_number: str
    ifsc_code: str
    branch_name: Optional[str] = None


class EmployeeBankDetailCreate(EmployeeBankDetailBase):
    pass


class EmployeeBankDetailUpdate(BaseModel):
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    branch_name: Optional[str] = None


class EmployeeBankDetailRead(EmployeeBankDetailBase):
    id: int

    class Config:
        from_attributes = True
