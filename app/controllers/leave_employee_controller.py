# app/controllers/leave_me_controller.py
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from app.data.models.leave import LeaveStatus
from sqlalchemy.orm import Session

from app.schemas.leave_employee_schema import (
    LeaveTypeOut,
    LeaveBalanceOut,
    CalendarOut,
    LeaveApplyIn,
    LeaveRequestOut,
    LeaveSummaryOut,
)
from app.services.leave_employee_service import LeaveMeService


class LeaveMeController:
    def __init__(self, service: Optional[LeaveMeService] = None):
        self.service = service or LeaveMeService()

    def list_types(self, db: Session) -> List[LeaveTypeOut]:
        return self.service.list_types(db)

    def list_balances(
        self, db: Session, employee_id: str, year: int, month: Optional[int] = None
    ) -> List[LeaveBalanceOut]:
        return self.service.list_balances(db, employee_id, year, month)

    def get_calendar(
        self, db: Session, employee_id: str, start_dt: datetime, end_dt: datetime
    ) -> CalendarOut:
        return self.service.get_calendar(db, employee_id, start_dt, end_dt)

    def apply(self, db: Session, employee_id: str, payload: LeaveApplyIn) -> LeaveRequestOut:
        return self.service.apply(db, employee_id, payload)

    def list_requests(
        self, db: Session, employee_id: str, status: Optional[LeaveStatus]
    ) -> List[LeaveRequestOut]:
        return self.service.list_requests(db, employee_id, status)

    def cancel(self, db: Session, employee_id: str, req_id: int) -> dict:
        return self.service.cancel_my_request(db, employee_id, req_id)

    def get_summary(self, db: Session, employee_id: str, year: int, month: int) -> LeaveSummaryOut:
        return self.service.get_summary(db, employee_id, year, month)
