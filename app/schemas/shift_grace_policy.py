from pydantic import BaseModel
from datetime import date
from typing import Optional


class ShiftGracePolicyBase(BaseModel):
    shift_id: int
    grace_type: str
    applies_to: str
    excused_minutes: int
    effective_from: date
    effective_to: Optional[date] = None
    is_active: bool = True


class ShiftGracePolicyCreate(ShiftGracePolicyBase):
    pass


class ShiftGracePolicyUpdate(BaseModel):
    excused_minutes: Optional[int] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None


class ShiftGracePolicyResponse(ShiftGracePolicyBase):
    id: int

    class Config:
        orm_mode = True
