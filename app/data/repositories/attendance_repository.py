from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from calendar import monthrange
from app.data.models.attendance import AttendanceSession, AttendanceDay, CheckInMonitoring
from app.data.models.add_employee import Employee


class AttendanceRepository:
    # Sessions
    def get_open_session(self, db: Session, employee_id: str) -> AttendanceSession | None:
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
        self, db: Session, employee_id: str, check_in_utc: datetime, work_date_local: date
    ) -> AttendanceSession:
        s = AttendanceSession(
            employee_id=employee_id, check_in_utc=check_in_utc, work_date_local=work_date_local
        )
        db.add(s)
        db.flush()
        return s

    def close_session(self, db: Session, session: AttendanceSession, check_out_utc: datetime):
        session.check_out_utc = check_out_utc
        db.flush()

    # Days
    def get_day(self, db: Session, employee_id: str, work_date_local: date) -> AttendanceDay | None:
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
        d = self.get_day(db, employee_id, work_date_local)
        if not d:
            d = AttendanceDay(
                employee_id=employee_id,
                work_date_local=work_date_local,
                seconds_worked=0,
                first_check_in_utc=start_utc,
                last_check_out_utc=end_utc,
                status="PRESENT",
            )
            db.add(d)
            db.flush()
        d.seconds_worked += max(0, seconds)
        if not d.first_check_in_utc or start_utc < d.first_check_in_utc:
            d.first_check_in_utc = start_utc
        if not d.last_check_out_utc or end_utc > d.last_check_out_utc:
            d.last_check_out_utc = end_utc
        return d

    def month_days(
        self, db: Session, employee_id: str, year: int, month: int
    ) -> list[AttendanceDay]:
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
        return list(db.execute(stmt).scalars())

    def get_employee_basic(self, db: Session, employee_id: str) -> Optional[Employee]:
        stmt = select(Employee).where(Employee.employee_id == employee_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_days_for_employee(
        self,
        db: Session,
        employee_id: str,
        date_from: date,
        date_to: date,
    ) -> List[AttendanceDay]:
        """
        Returns AttendanceDay rows in [date_from, date_to] (inclusive).
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

    # Monitoring
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
        Returns all monitoring records for an employee.
        """
        stmt = (
            select(CheckInMonitoring)
            .join(AttendanceSession, CheckInMonitoring.session_id == AttendanceSession.id)
            .where(AttendanceSession.employee_id == employee_id)
            .order_by(CheckInMonitoring.monitored_at_utc.desc())
        )
        return list(db.execute(stmt).scalars().all())
