# app/data/repositories/leave_me_repository.py
from __future__ import annotations
from datetime import date, datetime
from typing import Optional, List, Tuple

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.data.models.leave import (
    LeaveType,
    LeaveBalance,
    LeaveRequest,
    LeaveStatus,
    LeaveReqUnit,
)
from app.data.models.policy import HolidayCalendar
from app.data.models.add_employee import Employee


class LeaveMeRepository:
    # --------- Identity helpers ----------
    def get_employee_region(self, db: Session, employee_id: str) -> Optional[str]:
        stmt = select(Employee.region).where(Employee.employee_id == employee_id)
        row = db.execute(stmt).first()
        return row[0] if row else None

    def get_leave_type_by_code(self, db: Session, code: str) -> Optional[LeaveType]:
        stmt = select(LeaveType).where(LeaveType.code == code)
        return db.execute(stmt).scalar_one_or_none()

    # --------- Types ----------
    def list_leave_types(self, db: Session) -> List[LeaveType]:
        stmt = select(LeaveType).order_by(LeaveType.code.asc())
        return list(db.execute(stmt).scalars().all())

    # --------- Balances ----------
    def list_balances_for_employee_year(
        self, db: Session, employee_id: str, year: int
    ) -> List[Tuple[LeaveBalance, LeaveType]]:
        stmt = (
            select(LeaveBalance, LeaveType)
            .join(LeaveType, LeaveType.id == LeaveBalance.leave_type_id)
            .where(
                and_(
                    LeaveBalance.employee_id == employee_id,
                    LeaveBalance.year == year,
                )
            )
            .order_by(LeaveType.code.asc())
        )
        rows = db.execute(stmt).all()
        # rows are Row[tuple[LeaveBalance, LeaveType]] → unpack to plain tuples
        return [(row[0], row[1]) for row in rows]

    # --------- Holidays ----------
    def list_holidays_in_range(
        self, db: Session, date_from: date, date_to: date, region: Optional[str]
    ) -> List[HolidayCalendar]:
        stmt = select(HolidayCalendar).where(
            and_(
                HolidayCalendar.holiday_date >= date_from,
                HolidayCalendar.holiday_date <= date_to,
            )
        )
        if region:
            stmt = stmt.where(
                or_(
                    HolidayCalendar.region == region,
                    HolidayCalendar.region.is_(None),
                )
            )
        else:
            # only global
            stmt = stmt.where(HolidayCalendar.region.is_(None))
        stmt = stmt.order_by(HolidayCalendar.holiday_date.asc())
        return list(db.execute(stmt).scalars().all())

    # --------- Requests ----------
    def list_my_requests(
        self, db: Session, employee_id: str, status: Optional[LeaveStatus]
    ) -> List[Tuple[LeaveRequest, LeaveType]]:
        stmt = (
            select(LeaveRequest, LeaveType)
            .join(LeaveType, LeaveType.id == LeaveRequest.leave_type_id)
            .where(LeaveRequest.employee_id == employee_id)
            .order_by(LeaveRequest.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(LeaveRequest.status == status)

        rows = db.execute(stmt).all()
        return [(row[0], row[1]) for row in rows]

    def any_overlapping_request(
        self,
        db: Session,
        employee_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> bool:
        # overlaps if NOT( new.end < existing.start OR new.start > existing.end )
        stmt = (
            select(LeaveRequest.id)
            .where(
                and_(
                    LeaveRequest.employee_id == employee_id,
                    LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
                    ~(
                        or_(
                            LeaveRequest.end_datetime < start_dt,
                            LeaveRequest.start_datetime > end_dt,
                        )
                    ),
                )
            )
            .limit(1)
        )
        return db.execute(stmt).first() is not None

    def create_request(
        self,
        db: Session,
        employee_id: str,
        leave_type_id: int,
        requested_unit: LeaveReqUnit,
        start_dt: datetime,
        end_dt: datetime,
        requested_hours: Optional[float],
        reason: Optional[str],
    ) -> LeaveRequest:
        r = LeaveRequest(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            start_datetime=start_dt,
            end_datetime=end_dt,
            requested_unit=requested_unit,
            requested_hours=requested_hours,
            status=LeaveStatus.PENDING,
            reason=reason,
        )
        db.add(r)
        db.flush()
        return r

    def get_request_by_id(self, db: Session, req_id: int) -> Optional[LeaveRequest]:
        stmt = select(LeaveRequest).where(LeaveRequest.id == req_id)
        return db.execute(stmt).scalar_one_or_none()

    def cancel_request(self, db: Session, r: LeaveRequest) -> None:
        r.status = LeaveStatus.CANCELLED
        db.flush()

    # --------- Calendar (leaves in range) ----------
    def list_my_approved_leaves_in_range(
        self, db: Session, employee_id: str, start_dt: datetime, end_dt: datetime
    ) -> List[Tuple[LeaveRequest, LeaveType]]:
        stmt = (
            select(LeaveRequest, LeaveType)
            .join(LeaveType, LeaveType.id == LeaveRequest.leave_type_id)
            .where(
                and_(
                    LeaveRequest.employee_id == employee_id,
                    LeaveRequest.status == LeaveStatus.APPROVED,
                    ~(
                        or_(
                            LeaveRequest.end_datetime < start_dt,
                            LeaveRequest.start_datetime > end_dt,
                        )
                    ),
                )
            )
            .order_by(LeaveRequest.start_datetime.asc())
        )
        rows = db.execute(stmt).all()
        return [(row[0], row[1]) for row in rows]
