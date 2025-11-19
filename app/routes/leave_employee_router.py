from __future__ import annotations
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.schemas.leave_employee_schema import (
    LeaveTypeOut,
    LeaveBalanceOut,
    LeaveApplyIn,
    LeaveRequestOut,
    LeaveSummaryOut,
)
from app.controllers.leave_employee_controller import LeaveMeController
from app.data.db import SessionLocal


router = APIRouter(prefix="/api/leave", tags=["Leave"])
ctl = LeaveMeController()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/types")
def list_types(db: Session = Depends(get_db)) -> List[LeaveTypeOut]:
    return ctl.list_types(db)


@router.get("/balances")
def list_balances(
    employeeId: str, year: int, month: Optional[int] = Query(None), db: Session = Depends(get_db)
) -> List[LeaveBalanceOut]:
    return ctl.list_balances(db, employeeId, year, month)


@router.get("/calendar")
def get_calendar(
    employeeId: str,
    start: str = Query(..., description="ISO datetime"),
    end: str = Query(..., description="ISO datetime"),
    db: Session = Depends(get_db),
):
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except Exception as e:
        raise HTTPException(400, f"Invalid datetime: {e}")
    return ctl.get_calendar(db, employeeId, start_dt, end_dt)


@router.post("/apply")
def apply_leave(
    payload: LeaveApplyIn = Body(...), employeeId: str = Query(...), db: Session = Depends(get_db)
) -> LeaveRequestOut:
    result = ctl.apply(db, employeeId, payload)
    # Ensure transaction is committed at the route level
    db.commit()
    return result


@router.get("/requests")
def list_requests(
    employeeId: str, status: Optional[str] = Query(None), db: Session = Depends(get_db)
) -> List[LeaveRequestOut]:
    return ctl.list_requests(db, employeeId, status)


@router.post("/requests/{req_id}/cancel")
def cancel_request(req_id: int, employeeId: str = Query(...), db: Session = Depends(get_db)):
    try:
        result = ctl.cancel(db, employeeId, req_id)
        db.commit()
        return result
    except ValueError as e:
        db.rollback()
        raise HTTPException(400, str(e))


@router.get("/summary")
def get_summary(
    employeeId: str, year: int, month: int, db: Session = Depends(get_db)
) -> LeaveSummaryOut:
    return ctl.get_summary(db, employeeId, year, month)
