# app/services/leave_me_service.py
from __future__ import annotations
from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.data.repositories.leave_employee_repository import LeaveMeRepository
from app.data.models.leave import LeaveReqUnit, LeaveStatus
from app.schemas.leave_employee_schema import (
    LeaveTypeOut,
    LeaveBalanceOut,
    CalendarOut,
    CalendarHolidayOut,
    CalendarLeaveOut,
    LeaveApplyIn,
    LeaveRequestOut,
)


class LeaveMeService:
    def __init__(self, repo: Optional[LeaveMeRepository] = None):
        self.repo = repo or LeaveMeRepository()

    # --------- Types ----------
    def list_types(self, db: Session) -> List[LeaveTypeOut]:
        types = self.repo.list_leave_types(db)
        return [
            LeaveTypeOut(
                id=t.id,
                code=t.code,
                name=t.name,
                unit=t.unit.value if hasattr(t.unit, "value") else str(t.unit),
                is_paid=bool(t.is_paid),
                allow_half_day=bool(t.allow_half_day),
                allow_permission_hours=bool(t.allow_permission_hours),
            )
            for t in types
        ]

    # --------- Balances ----------
    def list_balances(self, db: Session, employee_id: str, year: int) -> List[LeaveBalanceOut]:
        rows = self.repo.list_balances_for_employee_year(db, employee_id, year)
        return [
            LeaveBalanceOut(
                leave_type_id=lt.id,
                leave_type_code=lt.code,
                leave_type_name=lt.name,
                year=bal.year,
                opening=float(bal.opening),
                accrued=float(bal.accrued),
                used=float(bal.used),
                adjusted=float(bal.adjusted),
                closing=float(bal.closing),
            )
            for bal, lt in rows
        ]

    # --------- Calendar ----------
    def get_calendar(
        self, db: Session, employee_id: str, start_dt: datetime, end_dt: datetime
    ) -> CalendarOut:
        if start_dt > end_dt:
            raise HTTPException(400, "start > end")

        region = self.repo.get_employee_region(db, employee_id)

        # holidays (by date range)
        holidays = self.repo.list_holidays_in_range(db, start_dt.date(), end_dt.date(), region)
        h_out = [
            CalendarHolidayOut(date=h.holiday_date, name=h.name, is_paid=bool(h.is_paid))
            for h in holidays
        ]

        # approved leaves in range
        leaves = self.repo.list_my_approved_leaves_in_range(db, employee_id, start_dt, end_dt)
        l_out = [
            CalendarLeaveOut(
                id=r.id,
                leave_type_code=lt.code,
                start=r.start_datetime,
                end=r.end_datetime,
                requested_unit=(
                    r.requested_unit.value
                    if hasattr(r.requested_unit, "value")
                    else str(r.requested_unit)
                ),
                approved=(r.status == LeaveStatus.APPROVED),
            )
            for r, lt in leaves
        ]
        return CalendarOut(holidays=h_out, leaves=l_out)

    # --------- Requests ----------
    def apply(self, db: Session, employee_id: str, payload: LeaveApplyIn) -> LeaveRequestOut:
        lt = self.repo.get_leave_type_by_code(db, payload.leave_type_code)
        if not lt:
            raise HTTPException(status_code=404, detail="Leave type not found")

        # Validate unit vs type rules
        req_unit = LeaveReqUnit(payload.requested_unit)
        if req_unit == LeaveReqUnit.HALF_DAY:
            if not bool(lt.allow_half_day):
                raise HTTPException(400, "Half-day not allowed for this leave type")
        if req_unit == LeaveReqUnit.HOUR:
            if not bool(lt.allow_permission_hours):
                raise HTTPException(400, "Permission-hours not allowed for this leave type")
            if payload.requested_hours is None or payload.requested_hours <= 0:
                raise HTTPException(400, "requested_hours must be > 0 for HOUR requests")

        # Overlap guard
        if self.repo.any_overlapping_request(
            db, employee_id, payload.start_datetime, payload.end_datetime
        ):
            raise HTTPException(
                status_code=409, detail="Overlapping request exists (PENDING/APPROVED)"
            )

        r = self.repo.create_request(
            db=db,
            employee_id=employee_id,
            leave_type_id=lt.id,
            requested_unit=req_unit,
            start_dt=payload.start_datetime,
            end_dt=payload.end_datetime,
            requested_hours=payload.requested_hours,
            reason=payload.reason,
        )
        return LeaveRequestOut(
            id=r.id,
            leave_type_code=lt.code,
            requested_unit=req_unit.value,
            start_datetime=r.start_datetime,
            end_datetime=r.end_datetime,
            requested_hours=r.requested_hours,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            reason=r.reason,
            created_at=r.created_at,
        )

    def list_requests(
        self, db: Session, employee_id: str, status_str: Optional[str]
    ) -> List[LeaveRequestOut]:
        status_enum = LeaveStatus(status_str) if status_str else None
        rows = self.repo.list_my_requests(db, employee_id, status_enum)
        out: List[LeaveRequestOut] = []
        for r, lt in rows:
            out.append(
                LeaveRequestOut(
                    id=r.id,
                    leave_type_code=lt.code,
                    requested_unit=(
                        r.requested_unit.value
                        if hasattr(r.requested_unit, "value")
                        else str(r.requested_unit)
                    ),
                    start_datetime=r.start_datetime,
                    end_datetime=r.end_datetime,
                    requested_hours=r.requested_hours,
                    status=r.status.value if hasattr(r.status, "value") else str(r.status),
                    reason=r.reason,
                    created_at=r.created_at,
                )
            )
        return out

    def cancel_my_request(self, db: Session, employee_id: str, req_id: int) -> dict:
        r = self.repo.get_request_by_id(db, req_id)
        if not r:
            raise HTTPException(404, "Request not found")
        if r.employee_id != employee_id:
            raise HTTPException(403, "Not your request")
        if r.status != LeaveStatus.PENDING:
            raise HTTPException(409, "Only PENDING requests can be cancelled")

        self.repo.cancel_request(db, r)
        return {"ok": True}
