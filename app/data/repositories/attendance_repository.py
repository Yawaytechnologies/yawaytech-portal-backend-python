# app/data/repositories/attendance_repository.py
from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional
from calendar import monthrange

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.data.models.attendance import (
    AttendanceSession,
    AttendanceDay,
    CheckInMonitoring,
    DayStatus,  # Enum -> binds to DB enum values like "Present"
)
from app.data.models.add_employee import Employee

EIGHT_HOURS = 8 * 60 * 60  # 28_800


class AttendanceRepository:
    # ─────────────────────────────
    # Sessions
    # ─────────────────────────────
    def get_open_session(self, db: Session, employee_id: str) -> AttendanceSession | None:
        """
        Return the most recent open session (check_out_utc is NULL) for an employee, if any.
        """
        stmt = (
            select(AttendanceSession)
            .where(
                and_(
                    AttendanceSession.employee_id == employee_id,
                    AttendanceSession.check_out_utc.is_(None),
                )
            )
            .order_by(AttendanceSession.id.desc())
            .limit(1)
        )
        return db.execute(stmt).scalar_one_or_none()

    def create_session(
        self,
        db: Session,
        employee_id: str,
        check_in_utc: datetime,
        work_date_local: date,
    ) -> AttendanceSession:
        """
        Create a new IN session. Do NOT call if an open session already exists.
        """
        s = AttendanceSession(
            employee_id=employee_id,
            check_in_utc=check_in_utc,
            work_date_local=work_date_local,
        )
        db.add(s)
        db.flush()  # get s.id
        return s

    def close_session(
        self, db: Session, session: AttendanceSession, check_out_utc: datetime
    ) -> None:
        """
        Close an open session by setting check_out_utc.
        """
        session.check_out_utc = check_out_utc
        db.flush()

    # ─────────────────────────────
    # Days
    # ─────────────────────────────
    def get_day(self, db: Session, employee_id: str, work_date_local: date) -> AttendanceDay | None:
        """
        Fetch the AttendanceDay row (one per employee per local date).
        """
        stmt = select(AttendanceDay).where(
            (AttendanceDay.employee_id == employee_id)
            & (AttendanceDay.work_date_local == work_date_local)
        )
        return db.execute(stmt).scalar_one_or_none()

    def upsert_day_add_work(
        self,
        db: Session,
        employee_id: str,
        work_date_local: date,
        start_utc: datetime,
        end_utc: datetime,
        seconds: int,
    ) -> AttendanceDay:
        """
        Ensure the daily rollup row exists and add 'seconds' to seconds_worked.
        Sets safe defaults for NOT NULL columns. The policy/rollup layer can
        later overwrite expected_seconds/status for weekends/holidays/leave.
        """
        d = self.get_day(db, employee_id, work_date_local)
        if not d:
            d = AttendanceDay(
                employee_id=employee_id,
                work_date_local=work_date_local,
                # NOT NULL metrics (safe defaults)
                seconds_worked=0,
                expected_seconds=EIGHT_HOURS,
                paid_leave_seconds=0,
                overtime_seconds=0,
                underwork_seconds=0,
                unpaid_seconds=0,
                # timestamps
                first_check_in_utc=start_utc,
                last_check_out_utc=end_utc,
                # IMPORTANT: pass Enum, not raw uppercase strings
                status=DayStatus.PRESENT,  # binds to "Present" in DB
                lock_flag=False,
            )
            db.add(d)
            db.flush()
        else:
            # Normalize legacy nulls if any (after schema evolution)
            if d.expected_seconds is None:
                d.expected_seconds = EIGHT_HOURS
            if d.paid_leave_seconds is None:
                d.paid_leave_seconds = 0
            if d.overtime_seconds is None:
                d.overtime_seconds = 0
            if d.underwork_seconds is None:
                d.underwork_seconds = 0
            if d.unpaid_seconds is None:
                d.unpaid_seconds = 0
            if d.status is None:
                d.status = DayStatus.PRESENT

            # Expand first/last punch boundaries if needed
            if not d.first_check_in_utc or start_utc < d.first_check_in_utc:
                d.first_check_in_utc = start_utc
            if not d.last_check_out_utc or end_utc > d.last_check_out_utc:
                d.last_check_out_utc = end_utc

        # Accumulate worked time (never subtract)
        d.seconds_worked += max(0, int(seconds or 0))
        return d

    def month_days(
        self, db: Session, employee_id: str, year: int, month: int
    ) -> list[AttendanceDay]:
        """
        Return all AttendanceDay rows for the given calendar month (local).
        """
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])
        stmt = (
            select(AttendanceDay)
            .where(
                (AttendanceDay.employee_id == employee_id)
                & (AttendanceDay.work_date_local.between(start, end))
            )
            .order_by(AttendanceDay.work_date_local.asc())
        )
        return list(db.execute(stmt).scalars().all())

    def get_days_for_employee(
        self,
        db: Session,
        employee_id: str,
        date_from: date,
        date_to: date,
    ) -> List[AttendanceDay]:
        """
        Return AttendanceDay rows in [date_from, date_to] inclusive.
        """
        stmt = (
            select(AttendanceDay)
            .where(
                and_(
                    AttendanceDay.employee_id == employee_id,
                    AttendanceDay.work_date_local >= date_from,
                    AttendanceDay.work_date_local <= date_to,
                )
            )
            .order_by(AttendanceDay.work_date_local.asc())
        )
        return list(db.execute(stmt).scalars().all())

    # ─────────────────────────────
    # Employees (basic lookup)
    # ─────────────────────────────
    def get_employee_basic(self, db: Session, employee_id: str) -> Optional[Employee]:
        stmt = select(Employee).where(Employee.employee_id == employee_id)
        return db.execute(stmt).scalar_one_or_none()

    # ─────────────────────────────
    # Monitoring
    # ─────────────────────────────
    def create_monitoring(
        self,
        db: Session,
        session_id: int,
        monitored_at_utc: datetime,
        cpu_percent: float | None,
        memory_percent: float | None,
        active_apps: list[str],
        visited_sites: list[dict],
    ) -> CheckInMonitoring:
        """
        Create a CheckInMonitoring record linked to a session.
        """
        m = CheckInMonitoring(
            session_id=session_id,
            monitored_at_utc=monitored_at_utc,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            active_apps=active_apps,
            visited_sites=visited_sites,
        )
        db.add(m)
        db.flush()
        return m

    def get_monitoring_for_employee(self, db: Session, employee_id: str) -> List[CheckInMonitoring]:
        """
        Returns monitoring records for an employee ordered by capture time (desc).
        """
        stmt = (
            select(CheckInMonitoring)
            .join(AttendanceSession, CheckInMonitoring.session_id == AttendanceSession.id)
            .where(AttendanceSession.employee_id == employee_id)
            .order_by(CheckInMonitoring.monitored_at_utc.desc())
        )
        return list(db.execute(stmt).scalars().all())
