# app/schemas/salary_breakdown.py
from pydantic import BaseModel
from enum import Enum


class Ruletypes(str, Enum):
    ALLOWANCE = "ALLOWANCE"
    DEDUCTION = "DEDUCTION"


class SalaryBreakdownRead(BaseModel):
    id: int
    rule_name: str
    rule_type: Ruletypes
    applies_to: str
    amount: float

    class Config:
        from_attributes = True
