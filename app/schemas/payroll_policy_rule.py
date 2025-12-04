from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class Ruletypes(str, Enum):
    ALLOWANCE = "ALLOWANCE"
    DEDUCTION = "DEDUCTION"


class PayrollPolicyRuleBase(BaseModel):
    rule_name: str
    rule_type: Ruletypes
    is_enabled: bool = True
    is_percentage: bool = True
    value: float
    applies_to: str


class PayrollPolicyRuleCreate(PayrollPolicyRuleBase):
    pass


class PayrollPolicyRuleRead(PayrollPolicyRuleBase):
    id: int

    class Config:
        orm_mode = True


class PayrollPolicyRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    rule_type: Optional[Ruletypes] = None
    is_enabled: Optional[bool] = None
    is_percentage: Optional[bool] = None
    value: Optional[float] = None
    applies_to: Optional[str] = None
    rules: Optional[List["PayrollPolicyRuleUpdate"]] = None


# Update forward references
PayrollPolicyRuleUpdate.update_forward_refs()
