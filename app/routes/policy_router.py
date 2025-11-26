# app/routes/admin_policy_router.py
from __future__ import annotations
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session

from app.data.db import SessionLocal
from app.schemas.policy_schma import (
    WorkweekUpsertRequest,
    WorkweekPolicyOut,
    HolidayCreateRequest,
    HolidayOut,
)
from app.controllers.policy_controller import AdminPolicyController

router = APIRouter(prefix="/api", tags=["Policy"])
controller = AdminPolicyController()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Workweek ───────────────────────────────────────────────────────────────────


@router.get("/workweek", response_model=List[WorkweekPolicyOut], summary="List all workweek policies")
def list_workweeks(db: Session = Depends(get_db)):
    return controller.list_workweeks(db)


@router.post("/workweek", response_model=WorkweekPolicyOut, summary="Create workweek rules")
def create_workweek(payload: WorkweekUpsertRequest = Body(...), db: Session = Depends(get_db)):
    return controller.create_workweek(db, payload)


# ── Holidays ───────────────────────────────────────────────────────────────────


@router.post("/holidays", response_model=HolidayOut, summary="Add a holiday (paid/unpaid)")
def create_holiday(payload: HolidayCreateRequest = Body(...), db: Session = Depends(get_db)):
    return controller.create_holiday(db, payload)


@router.get(
    "/holidays",
    response_model=List[HolidayOut],
    summary="List holidays in range (includes global and region-specific)",
)
def list_holidays(
    date_from: date = Query(..., alias="from"),
    date_to: date = Query(..., alias="to"),
    region: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return controller.list_holidays(db, date_from, date_to, region)


@router.delete("/holidays/{holiday_id}", summary="Delete a holiday if period not locked")
def delete_holiday(holiday_id: int, db: Session = Depends(get_db)):
    return controller.delete_holiday(db, holiday_id)
