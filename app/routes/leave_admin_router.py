from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
import logging
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.schemas.leave_schma import (
    LeaveTypeCreate,
    LeaveTypeUpdate,
    HolidayCreate,
    HolidayUpdate,
    HolidayResponse,
    HolidaysQuery,
    LeaveRequestCreate,
    LeaveDecisionPayload,
    LeaveRequestResponse,
    BalanceSeedPayload,
    BalanceAdjustPayload,
    AccrualRunPayload,
)
from app.controllers.leave_admin_controller import LeaveAdminController
from app.data.db import SessionLocal

router = APIRouter(prefix="/api/admin/leave", tags=["Admin Leave"])
ctl = LeaveAdminController()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---- Leave Types ----
@router.post("/types")
def create_type(payload: LeaveTypeCreate, db: Session = Depends(get_db)):
    try:
        result = ctl.create_type(db, payload.dict())
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/types")
def list_types(db: Session = Depends(get_db)):
    return ctl.list_types(db)


@router.patch("/types/{code}")
def update_type(code: str, payload: LeaveTypeUpdate, db: Session = Depends(get_db)):
    try:
        result = ctl.update_type(db, code, payload.dict(exclude_unset=True))
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/types/{code}")
def delete_type(code: str, db: Session = Depends(get_db)):
    try:
        result = ctl.delete_type(db, code)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


# ---- Balances ----
@router.post("/balances/seed")
def seed_balances(payload: BalanceSeedPayload, db: Session = Depends(get_db)):
    try:
        result = ctl.seed_balances(db, payload.employee_id, payload.year, payload.items)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/balances/adjust")
def adjust_balance(payload: BalanceAdjustPayload, db: Session = Depends(get_db)):
    try:
        result = ctl.adjust_balance(db, payload.employee_id, payload.year, payload.leave_type_code, payload.delta_hours)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/balances/accrue")
def run_accrual(payload: AccrualRunPayload, db: Session = Depends(get_db)):
    try:
        result = ctl.run_monthly_accrual(db, payload.year, payload.month, payload.employee_ids, payload.per_type_hours)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


# ---- Holidays ----
@router.post("/holidays")
def create_holiday(payload: HolidayCreate, db: Session = Depends(get_db)):
    result = ctl.create_holiday(db, payload.dict())
    db.commit()
    return result


@router.get("/holidays")
def list_holidays(
    start: str = Query(..., description="YYYY-MM-DD"),
    end: str = Query(..., description="YYYY-MM-DD"),
    region: str | None = Query(None),
    db: Session = Depends(get_db),
):
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
        q = HolidaysQuery(start=start_date, end=end_date, region=region)
    except Exception as e:
        raise HTTPException(400, f"Invalid dates: {e}")
    return ctl.list_holidays(db, q.start, q.end, q.region)


@router.patch("/holidays/{holiday_id}", response_model=HolidayResponse)
def update_holiday(holiday_id: int, payload: HolidayUpdate, db: Session = Depends(get_db)):
    try:
        result = ctl.update_holiday(db, holiday_id, payload.dict(exclude_unset=True))
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/holidays/{holiday_id}")
def delete_holiday(holiday_id: int, db: Session = Depends(get_db)):
    try:
        result = ctl.delete_holiday(db, holiday_id)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


# ---- Requests (admin) ----
@router.post("/requests")
def create_request_admin(payload: LeaveRequestCreate, db: Session = Depends(get_db)):
    try:
        result = ctl.create_request_admin(db, payload.dict())
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/requests", response_model=List[LeaveRequestResponse])
def list_requests(status: str | None = Query(None), db: Session = Depends(get_db)):
    return ctl.list_requests(db, status)


@router.post("/requests/{req_id}/decision")
def decide_request(req_id: int, payload: LeaveDecisionPayload, db: Session = Depends(get_db)):
    try:
        result = ctl.decide_request(
            db, req_id, payload.decision, payload.approver_employee_id, payload.note
        )
        db.commit()
        return result
    except ValueError as e:
        # Log the error server-side so the cause is visible in logs (helps diagnose 400s)
        logging.exception("Error deciding leave request %s: %s", req_id, e)
        raise HTTPException(400, str(e))


# Helper: fetch a single request (useful for debugging failing decisions)
@router.get("/requests/{req_id}")
def get_request(req_id: int, db: Session = Depends(get_db)):
    r = ctl.repo.get_request(db, req_id)
    if not r:
        raise HTTPException(404, f"Request {req_id} not found")
    return r


# ---- Permission usage debugging ----
@router.get("/permission-usage")
def permission_usage(
    employeeId: str, code: str, year: int, month: int, db: Session = Depends(get_db)
):
    return {"hours": ctl.month_permission_usage(db, employeeId, code, year, month)}
