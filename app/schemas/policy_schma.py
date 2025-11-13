# app/schemas/policy_schemas.py
from __future__ import annotations

from datetime import date
from typing import Optional, Dict, Literal

from pydantic import BaseModel, Field, validator

# ── Workweek ───────────────────────────────────────────────────────────────────

WeekdayKey = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class WorkweekUpsertRequest(BaseModel):
    region: str = Field(
        ...,
        min_length=2,
        max_length=8,
        description="Region code (e.g. IN-TN, HQ)",
        examples=["IN-TN", "HQ"],
    )

    policy: Dict[WeekdayKey, object] = Field(
        ...,
        description="mon..sun -> bool (working?) or '1st,3rd' style string for Saturday patterns",
        json_schema_extra={
            "example": {
                "mon": True,
                "tue": True,
                "wed": True,
                "thu": True,
                "fri": True,
                "sat": "2nd,4th",
                "sun": False,
            }
        },
    )

    @validator("policy")
    def validate_keys(cls, v: Dict[str, object]) -> Dict[str, object]:
        allowed = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
        extra = set(v.keys()) - allowed
        if extra:
            raise ValueError(f"Invalid weekday keys: {sorted(extra)}")
        # sat can be bool or comma string; others must be bool
        for k, val in v.items():
            if k == "sat":
                if not (isinstance(val, bool) or isinstance(val, str)):
                    raise ValueError("sat must be bool or '1st,3rd' style string")
            else:
                if not isinstance(val, bool):
                    raise ValueError(f"{k} must be boolean")
        return v


class WorkweekPolicyOut(BaseModel):
    id: int
    region: str
    policy_json: Dict[str, object]


# ── Holidays ───────────────────────────────────────────────────────────────────


class HolidayCreateRequest(BaseModel):
    holiday_date: date
    name: str = Field(..., min_length=2, max_length=80)
    is_paid: bool = True
    region: Optional[str] = Field(None, max_length=8, description="Null = global")
    recurs_annually: bool = False


class HolidayOut(BaseModel):
    id: int
    holiday_date: date
    name: str
    is_paid: bool
    region: Optional[str]
    recurs_annually: bool


class HolidayListQuery(BaseModel):
    date_from: date
    date_to: date
    region: Optional[str] = None
