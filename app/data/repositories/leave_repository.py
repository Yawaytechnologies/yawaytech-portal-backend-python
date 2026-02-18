# app/data/repositories/leave_repository.py
from __future__ import annotations
from datetime import date, datetime
from typing import Optional, List
from calendar import monthrange

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, or_
from sqlalchemy.types import Date

from app.data.models.leave import (
    LeaveType,
    LeaveRequest,
    LeaveBalance,
    LeaveStatus,
    LeaveReqUnit,
)
from app.data.models.attendance import AttendanceDay, DayStatus
from app.data.models.policy import HolidayCalendar

EIGHT_HOURS = 8.0


# ──────────────────────────────────────────────────────────────────────────────
# Leave Types
# ──────────────────────────────────────────────────────────────────────────────
class LeaveRepository:
    # --- Types ---
    def create_type(self, db: Session, payload: dict) -> LeaveType:
        row = LeaveType(**payload)
        db.add(row)
        db.commit()
        return row

    def list_types(self, db: Session) -> List[LeaveType]:
        return list(db.execute(select(LeaveType).order_by(LeaveType.code.asc())).scalars())

    def get_type(self, db: Session, code: str) -> Optional[LeaveType]:
        stmt = select(LeaveType).where(LeaveType.code == code)
        return db.execute(stmt).scalar_one_or_none()

    def update_type(self, db: Session, code: str, patch: dict) -> Optional[LeaveType]:
        lt = self.get_type(db, code)
        if not lt:
            return None
        for k, v in patch.items():
            if v is not None and hasattr(lt, k):
                setattr(lt, k, v)
        db.flush()
        return lt

    def delete_type(self, db: Session, code: str) -> bool:
        lt = self.get_type(db, code)
        if not lt:
            return False
        db.delete(lt)
        return True

    # --- Holidays ---
    def create_holiday(self, db: Session, payload: dict) -> HolidayCalendar:
        h = HolidayCalendar(**payload)
        db.add(h)
        db.commit()
        return h

    def list_holidays(
        self, db: Session, start: date, end: date, region: Optional[str]
    ) -> List[HolidayCalendar]:
        q = select(HolidayCalendar).where(HolidayCalendar.holiday_date.between(start, end))
        if region:
            q = q.where(or_(HolidayCalendar.region == region, HolidayCalendar.region.is_(None)))
        q = q.order_by(HolidayCalendar.holiday_date.asc())
        return list(db.execute(q).scalars())

    def get_holiday(self, db: Session, holiday_id: int) -> Optional[HolidayCalendar]:
        return db.get(HolidayCalendar, holiday_id)

    def update_holiday(
        self, db: Session, holiday_id: int, patch: dict
    ) -> Optional[HolidayCalendar]:
        h = self.get_holiday(db, holiday_id)
        if not h:
            return None
        for k, v in patch.items():
            if v is not None and hasattr(h, k):
                setattr(h, k, v)
        db.flush()
        return h

    def delete_holiday(self, db: Session, holiday_id: int) -> bool:
        h = self.get_holiday(db, holiday_id)
        if not h:
            return False
        db.delete(h)
        return True

    # --- Balances ---
    def get_balance(
        self, db: Session, employee_id: str, leave_type_id: int, year: int
    ) -> Optional[LeaveBalance]:
        stmt = select(LeaveBalance).where(
            and_(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.leave_type_id == leave_type_id,
                LeaveBalance.year == year,
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    def get_balance_by_code(
        self, db: Session, employee_id: str, type_code: str, year: int
    ) -> Optional[LeaveBalance]:
        stmt = (
            select(LeaveBalance)
            .join(LeaveType, LeaveType.id == LeaveBalance.leave_type_id)
            .where(
                and_(
                    LeaveBalance.employee_id == employee_id,
                    LeaveType.code == type_code,
                    LeaveBalance.year == year,
                )
            )
        )
        return db.execute(stmt).scalar_one_or_none()

    def seed_balance(
        self, db: Session, employee_id: str, year: int, lt: LeaveType, opening_hours: float
    ) -> LeaveBalance:
        row = self.get_balance(db, employee_id, lt.id, year)
        if row:
            # update opening/closing only if not yet initialized
            if row.opening is None or float(row.opening) == 0.0:
                row.opening = opening_hours
            row.closing = (
                (row.opening or 0) + (row.accrued or 0) + (row.adjusted or 0) - (row.used or 0)
            )
            db.commit()
            return row
        row = LeaveBalance(
            employee_id=employee_id,
            leave_type_id=lt.id,
            year=year,
            opening=opening_hours,
            accrued=0,
            used=0,
            adjusted=0,
            closing=opening_hours,
        )
        db.add(row)
        db.commit()
        return row

    def adjust_balance(self, db: Session, bal: LeaveBalance, delta_hours: float) -> LeaveBalance:
        bal.adjusted = (bal.adjusted or 0) + delta_hours
        bal.closing = (
            (bal.opening or 0) + (bal.accrued or 0) + (bal.adjusted or 0) - (bal.used or 0)
        )
        db.flush()
        return bal

    def accrue_balance(self, db: Session, bal: LeaveBalance, add_hours: float) -> LeaveBalance:
        bal.accrued = (bal.accrued or 0) + add_hours
        bal.closing = (
            (bal.opening or 0) + (bal.accrued or 0) + (bal.adjusted or 0) - (bal.used or 0)
        )
        db.flush()
        return bal

    def use_balance(self, db: Session, bal: LeaveBalance, use_hours: float) -> LeaveBalance:
        bal.used = (bal.used or 0) + use_hours
        bal.closing = (
            (bal.opening or 0) + (bal.accrued or 0) + (bal.adjusted or 0) - (bal.used or 0)
        )
        db.flush()
        return bal

    def list_balances(self, db: Session, employee_id: str, year: int) -> List[LeaveBalance]:
        stmt = (
            select(LeaveBalance)
            .where(
                and_(
                    LeaveBalance.employee_id == employee_id,
                    LeaveBalance.year == year,
                )
            )
            .order_by(LeaveBalance.leave_type_id.asc())
        )
        return list(db.execute(stmt).scalars())

    # --- Requests ---
    def create_request(self, db: Session, payload: dict) -> LeaveRequest:
        row = LeaveRequest(**payload)
        db.add(row)
        db.commit()
        return row

    def get_request(self, db: Session, req_id: int) -> Optional[LeaveRequest]:
        return db.get(LeaveRequest, req_id)

    def list_requests(
        self,
        db: Session,
        status: Optional[str] = None,
    ) -> List[dict]:
        from app.data.models.add_employee import Employee

        q = (
            select(
                LeaveRequest.id,
                LeaveRequest.employee_id,
                Employee.name.label("employee_name"),
                LeaveType.code.label("leave_type_code"),
                LeaveRequest.start_datetime.cast(Date).label("start_date"),
                LeaveRequest.end_datetime.cast(Date).label("end_date"),
                LeaveRequest.requested_unit,
                LeaveRequest.requested_hours,
                LeaveRequest.status,
                LeaveRequest.reason,
                LeaveRequest.created_at,
                LeaveRequest.approver_employee_id,
                LeaveRequest.decided_at,
            )
            .join(Employee, LeaveRequest.employee_id == Employee.employee_id)
            .join(LeaveType, LeaveRequest.leave_type_id == LeaveType.id)
            .order_by(LeaveRequest.start_datetime.desc())
        )
        if status:
            # Accept either a LeaveStatus enum or a raw string; validate and
            # convert strings to LeaveStatus with a helpful error message.
            if isinstance(status, str):
                try:
                    status_enum = LeaveStatus(status)
                except ValueError:
                    valid = ", ".join([s.value for s in LeaveStatus])
                    raise ValueError(f"Invalid leave status '{status}'. Valid values: {valid}")
            elif isinstance(status, LeaveStatus):
                status_enum = status
            else:
                raise ValueError("Invalid status type")

            q = q.where(LeaveRequest.status == status_enum)

        results = db.execute(q).all()

        # Calculate requested_days
        response = []
        for row in results:
            requested_days = self._calculate_requested_days(row)
            response.append(
                {
                    "id": row.id,
                    "employee_id": row.employee_id,
                    "employee_name": row.employee_name,
                    "leave_type_code": row.leave_type_code,
                    "start_date": row.start_date,
                    "end_date": row.end_date,
                    "requested_unit": row.requested_unit,
                    "requested_hours": row.requested_hours,
                    "requested_days": requested_days,
                    "status": row.status.value if hasattr(row.status, "value") else str(row.status),
                    "reason": row.reason,
                    "created_at": row.created_at,
                    "approver_employee_id": row.approver_employee_id,
                    "decided_at": row.decided_at,
                }
            )
        return response

    def _calculate_requested_days(self, row) -> float:
        """Calculate the number of days requested based on unit and dates/hours."""
        if row.requested_unit == "HOUR":
            # For hours, assume 8 hours per day
            return (row.requested_hours or 0) / 8.0
        elif row.requested_unit == "HALF_DAY":
            # Calculate number of days between start and end, inclusive
            days = (row.end_date - row.start_date).days + 1
            return days * 0.5
        else:  # DAY
            days = (row.end_date - row.start_date).days + 1
            return float(days)

    def set_request_status(
        self,
        db: Session,
        req: LeaveRequest,
        status: str,
        approver_id: Optional[str],
        note: Optional[str],
    ) -> LeaveRequest:
        # Convert string status to LeaveStatus enum (validate explicitly)
        try:
            req.status = LeaveStatus(status)
        except ValueError:
            valid = ", ".join([s.value for s in LeaveStatus])
            raise ValueError(f"Invalid leave status '{status}'. Valid values: {valid}")

        if approver_id:
            req.approver_employee_id = approver_id
            req.decided_at = datetime.utcnow()
        if note:
            req.reason = (req.reason or "") + f" | {note}"
        db.flush()
        return req

    # --- Attendance impact for approvals ---
    def upsert_attendance_leave(
        self,
        db: Session,
        employee_id: str,
        d: date,
        hours: float,
        is_paid: bool,
    ) -> AttendanceDay:
        """
        Write leave impact into attendance_days.
        """
        row = db.execute(
            select(AttendanceDay).where(
                and_(
                    AttendanceDay.employee_id == employee_id,
                    AttendanceDay.work_date_local == d,
                )
            )
        ).scalar_one_or_none()
        if not row:
            row = AttendanceDay(
                employee_id=employee_id,
                work_date_local=d,
                seconds_worked=0,
                expected_seconds=8 * 3600,
                paid_leave_seconds=0,
                overtime_seconds=0,
                underwork_seconds=0,
                unpaid_seconds=0,
                first_check_in_utc=None,
                last_check_out_utc=None,
                status=DayStatus.LEAVE,  # Enum (Title-case)
                lock_flag=False,
            )
            db.add(row)
            db.commit()
        else:
            # make sure status is harmonized
            row.status = DayStatus.LEAVE

        inc = int(round(hours * 3600))
        if is_paid:
            row.paid_leave_seconds = (row.paid_leave_seconds or 0) + inc
        else:
            row.unpaid_seconds = (row.unpaid_seconds or 0) + inc

        # Recompute simple under/over math against expected_seconds
        blended = (row.seconds_worked or 0) + (row.paid_leave_seconds or 0)
        exp = row.expected_seconds or (8 * 3600)
        row.overtime_seconds = max(0, blended - exp)
        row.underwork_seconds = max(0, exp - blended)
        db.commit()
        return row

    # --- Permission usage for a month (approved only) ---
    def month_permission_hours(
        self,
        db: Session,
        employee_id: str,
        type_code: str,
        year: int,
        month: int,
    ) -> float:
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])

        stmt = (
            select(func.coalesce(func.sum(LeaveRequest.requested_hours), 0.0))
            .join(LeaveType, LeaveType.id == LeaveRequest.leave_type_id)
            .where(
                and_(
                    LeaveRequest.employee_id == employee_id,
                    LeaveType.code == type_code,
                    LeaveRequest.status == LeaveStatus.APPROVED,
                    LeaveRequest.requested_unit == LeaveReqUnit.HOUR,
                    LeaveRequest.start_datetime >= datetime.combine(start, datetime.min.time()),
                    LeaveRequest.end_datetime <= datetime.combine(end, datetime.max.time()),
                )
            )
        )

        scalar = db.execute(stmt).scalar_one()
        # Explicitly guard None for mypy, even though COALESCE should prevent it
        if scalar is None:
            return 0.0
        return float(scalar)

    # --- Check if employee has approved leave in a month ---
    def has_approved_leave_in_month(
        self,
        db: Session,
        employee_id: str,
        leave_type_code: str,
        year: int,
        month: int,
    ) -> bool:
        start_of_month = date(year, month, 1)
        end_of_month = date(year, month, monthrange(year, month)[1])

        stmt = (
            select(LeaveRequest.id)
            .join(LeaveType, LeaveType.id == LeaveRequest.leave_type_id)
            .where(
                and_(
                    LeaveRequest.employee_id == employee_id,
                    LeaveType.code == leave_type_code,
                    LeaveRequest.status == LeaveStatus.APPROVED,
                    LeaveRequest.start_datetime.cast(Date) <= end_of_month,
                    LeaveRequest.end_datetime.cast(Date) >= start_of_month,
                )
            )
        )

        result = db.execute(stmt).first()
        return result is not None
