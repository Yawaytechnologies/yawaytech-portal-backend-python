from datetime import date
from pydantic import BaseModel
from typing import List, Optional
from app.schemas.payroll_policy_rule import PayrollPolicyRuleCreate, PayrollPolicyRuleRead


class PayrollPolicyBase(BaseModel):
    name: str
    description: Optional[str] = None
    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool = True


class PayrollPolicyCreate(PayrollPolicyBase):
    rules: List[PayrollPolicyRuleCreate]


class PayrollPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None
    rules: Optional[List[PayrollPolicyRuleCreate]] = None


class PayrollPolicyRead(PayrollPolicyBase):
    id: int
    rules: List[PayrollPolicyRuleRead]

    class Config:
        from_attributes = True
