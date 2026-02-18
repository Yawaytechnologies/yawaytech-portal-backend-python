from __future__ import annotations
from datetime import datetime
from typing import Iterable
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
from app.data.models.leave import LeaveStatus
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
def _parse_flexible_datetime(value: str) -> datetime:
    """Parse a datetime value that may be ISO format or common date formats.

    Supported formats:
    - ISO (YYYY-MM-DD or full ISO datetimes)
    - DD-MM-YYYY and DD/MM/YYYY
    - YYYY/MM/DD
    """
    try:
        return datetime.fromisoformat(value)
    except Exception:
        # Try a few common human-friendly date formats
        fmts: Iterable[str] = (
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y-%m-%dT%H:%M:%S",
            "%d-%m-%YT%H:%M:%S",
        )
        for fmt in fmts:
            try:
                return datetime.strptime(value, fmt)
            except Exception:
                continue
    raise HTTPException(400, f"Invalid datetime: Unsupported format '{value}'")


def get_calendar(
    employeeId: str,
    start: str = Query(..., description="ISO datetime or DD-MM-YYYY"),
    end: str = Query(..., description="ISO datetime or DD-MM-YYYY"),
    db: Session = Depends(get_db),
):
    start_dt = _parse_flexible_datetime(start)
    end_dt = _parse_flexible_datetime(end)
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
    employeeId: str, status: Optional[LeaveStatus] = Query(None), db: Session = Depends(get_db)
) -> List[LeaveRequestOut]:
    # Let FastAPI validate the incoming `status` against the LeaveStatus enum.
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
