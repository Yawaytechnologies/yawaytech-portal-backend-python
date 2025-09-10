from __future__ import annotations
from datetime import datetime, timedelta, date
from typing import List, Dict
import calendar
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.timeutils import now_utc, to_local_date_ist, IST
from app.data.repositories.attendance_repository import AttendanceRepository
from app.data.models.add_employee import Employee  # to ensure employee exists

from app.schemas.attendance import (
    AttendanceDayItem,
    EmployeeAttendanceResponse,
    MonthlyAttendanceItem,
    EmployeeYearlyAttendanceResponse,
    EmployeeMonthlyAttendanceResponse,
)


def _to_hours_minutes(seconds: int) -> str:
    # rounds down to the minute
    minutes = seconds // 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _last_day_of_month(y: int, m: int) -> int:
    return calendar.monthrange(y, m)[1]


def _is_weekend(d: date) -> bool:
    # Mon=0 ... Sun=6
    return d.weekday() >= 5


def _avg_hhmm(total_seconds: int, denom_days: int) -> str:
    if denom_days <= 0:
        return "00:00"
    minutes = (total_seconds // 60) // denom_days
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


class AttendanceService:
    def __init__(self, repo: AttendanceRepository | None = None):
        self.repo = repo or AttendanceRepository()

    def _ensure_employee_exists(self, db: Session, employee_id: str):
        # Check if employee exists
        from sqlalchemy import select

        emp = db.execute(
            select(Employee).where(Employee.employee_id == employee_id)
        ).scalar_one_or_none()
        if not emp:
            raise HTTPException(404, f"Employee {employee_id} not found")

    def check_in(self, db: Session, employee_id: str):
        self._ensure_employee_exists(db, employee_id)
        if self.repo.get_open_session(db, employee_id):
            raise HTTPException(400, "Already checked in")

        t0 = now_utc()
        wdate = to_local_date_ist(t0)
        sess = self.repo.create_session(db, employee_id, t0, wdate)
        db.commit()
        db.refresh(sess)
        return sess

    def check_out(self, db: Session, employee_id: str):
        self._ensure_employee_exists(db, employee_id)
        sess = self.repo.get_open_session(db, employee_id)
        if not sess:
            raise HTTPException(400, "No open session")

        t1 = now_utc()
        start_local = sess.check_in_utc.astimezone(IST)
        end_local = t1.astimezone(IST)

        if start_local.date() == end_local.date():
            # Simple same-day close
            self.repo.close_session(db, sess, t1)
            seconds = int((t1 - sess.check_in_utc).total_seconds())
            self.repo.upsert_day_add_work(
                db, sess.employee_id, sess.work_date_local, sess.check_in_utc, t1, seconds
            )
        else:
            # Split across midnight (most common)
            first_midnight_local = datetime.combine(
                start_local.date() + timedelta(days=1), datetime.min.time(), tzinfo=IST
            )
            first_day_end_utc = first_midnight_local.astimezone(sess.check_in_utc.tzinfo)

            # allocate to first day
            self.repo.close_session(db, sess, first_day_end_utc)
            sec_first = int((first_day_end_utc - sess.check_in_utc).total_seconds())
            self.repo.upsert_day_add_work(
                db,
                sess.employee_id,
                sess.work_date_local,
                sess.check_in_utc,
                first_day_end_utc,
                sec_first,
            )

            # remainder to next day (rollup only)
            new_wdate = to_local_date_ist(first_day_end_utc)
            sec_rest = int((t1 - first_day_end_utc).total_seconds())
            self.repo.upsert_day_add_work(
                db, sess.employee_id, new_wdate, first_day_end_utc, t1, sec_rest
            )

        db.commit()
        db.refresh(sess)
        return sess

    def today_status(self, db: Session, employee_id: str):
        self._ensure_employee_exists(db, employee_id)
        now = now_utc()
        wdate = to_local_date_ist(now)

        day = self.repo.get_day(db, employee_id, wdate)
        closed_seconds = day.seconds_worked if day else 0

        open_sess = self.repo.get_open_session(db, employee_id)
        open_since = (
            open_sess.check_in_utc
            if (open_sess and to_local_date_ist(open_sess.check_in_utc) == wdate)
            else None
        )
        running = int((now - open_since).total_seconds()) if open_since else 0

        total = closed_seconds + running
        return {
            "employeeId": employee_id,
            "workDateLocal": wdate,
            "openSessionId": open_sess.id if open_sess else None,
            "openSinceUtc": open_since,
            "secondsWorkedSoFar": total,
            "present": total > 0 or bool(open_sess),
        }

    def month_view(self, db: Session, employee_id: str, year: int, month: int):
        self._ensure_employee_exists(db, employee_id)
        days = self.repo.month_days(db, employee_id, year, month)
        return [
            {
                "date": d.work_date_local,
                "secondsWorked": d.seconds_worked,
                "present": d.seconds_worked > 0,
            }
            for d in days
        ]

    def get_employee_attendance(
        self,
        db: Session,
        employee_id: str,
        date_from: date,
        date_to: date,
        include_absent: bool = True,
    ) -> EmployeeAttendanceResponse:
        if date_from > date_to:
            raise ValueError("date_from cannot be after date_to")

        emp = self.repo.get_employee_basic(db, employee_id)
        if not emp:
            # Surface a clean error; your router will map to 404
            raise LookupError("Employee not found")

        rows = self.repo.get_days_for_employee(db, employee_id, date_from, date_to)

        # Map existing days by date for quick lookup
        by_date: Dict[date, AttendanceDayItem] = {}
        for r in rows:
            status = "PRESENT" if (r.seconds_worked or 0) > 0 else "ABSENT"
            by_date[r.work_date_local] = AttendanceDayItem(
                work_date_local=r.work_date_local,
                seconds_worked=r.seconds_worked or 0,
                hours_worked=_to_hours_minutes(r.seconds_worked or 0),
                status=status,
                first_check_in_utc=r.first_check_in_utc,
                last_check_out_utc=r.last_check_out_utc,
            )

        # Build full day range; optionally inject ABSENT for missing rows
        items: List[AttendanceDayItem] = []
        cursor = date_from
        while cursor <= date_to:
            if cursor in by_date:
                items.append(by_date[cursor])
            else:
                if include_absent:
                    items.append(
                        AttendanceDayItem(
                            work_date_local=cursor,
                            seconds_worked=0,
                            hours_worked=_to_hours_minutes(0),
                            status="ABSENT",
                            first_check_in_utc=None,
                            last_check_out_utc=None,
                        )
                    )
            cursor = cursor + timedelta(days=1)

        present_days = sum(1 for it in items if it.status == "PRESENT")
        absent_days = sum(1 for it in items if it.status == "ABSENT")

        return EmployeeAttendanceResponse(
            employee_id=employee_id,
            employee_name=getattr(emp, "name", None),
            date_from=date_from,
            date_to=date_to,
            total_days=len(items),
            present_days=present_days,
            absent_days=absent_days,
            items=items,
        )

    def get_employee_attendance_monthly(
        self,
        db: Session,
        employee_id: str,
        year: int,
        include_absent: bool = True,
        working_days_only: bool = False,
        cap_to_today: bool = True,
    ) -> EmployeeYearlyAttendanceResponse:
        """
        Month-wise aggregation for an employee in a given year.
        - If include_absent=True, missing calendar days are counted as ABSENT.
        - If working_days_only=True, only Mon–Fri are considered for absence fill.
        - If cap_to_today=True, for current month in `year`, counts only up to local IST 'today'.
        """
        # Validate employee
        emp = self.repo.get_employee_basic(db, employee_id)
        if not emp:
            raise LookupError("Employee not found")

        # Fetch all day rows in the year
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        day_rows = self.repo.get_days_for_employee(db, employee_id, start, end)

        # Index by date for quick lookup
        by_date = {r.work_date_local: r for r in day_rows}

        months: list[MonthlyAttendanceItem] = []
        total_seconds = 0
        total_present = 0
        total_absent = 0

        today_local = datetime.now(IST).date()

        for m in range(1, 13):
            mdays = _last_day_of_month(year, m)
            m_start = date(year, m, 1)
            m_end = date(year, m, mdays)

            # Cap current month to today (avoid counting future days as absences)
            if cap_to_today and year == today_local.year and m == today_local.month:
                m_end = min(m_end, today_local)

            # Iterate days
            sec_sum = 0
            present_days = 0
            absent_days = 0
            days_counted = 0

            cursor = m_start
            while cursor <= m_end:
                # Skip weekends if we're only counting working days
                if working_days_only and _is_weekend(cursor):
                    cursor += timedelta(days=1)
                    continue

                days_counted += 1
                row = by_date.get(cursor)
                if row:
                    sw = row.seconds_worked or 0
                    sec_sum += sw
                    if sw > 0:
                        present_days += 1
                    else:
                        # Explicit ABSENT record (seconds=0)
                        absent_days += 1
                else:
                    # No row; treat as ABSENT only if include_absent is True
                    if include_absent:
                        absent_days += 1

                cursor += timedelta(days=1)

            total_seconds += sec_sum
            total_present += present_days
            total_absent += absent_days

            months.append(
                MonthlyAttendanceItem(
                    month=m,
                    month_name=calendar.month_name[m],
                    seconds_worked=sec_sum,
                    hours_worked=_to_hours_minutes(sec_sum),
                    present_days=present_days,
                    absent_days=absent_days,
                    days_counted=days_counted,
                )
            )

        return EmployeeYearlyAttendanceResponse(
            employee_id=employee_id,
            employee_name=getattr(emp, "name", None),
            year=year,
            total_seconds_worked=total_seconds,
            total_hours_worked=_to_hours_minutes(total_seconds),
            total_present_days=total_present,
            total_absent_days=total_absent,
            months=months,
        )

    def get_employee_month_report(
        self,
        db: Session,
        employee_id: str,
        year: int,
        month: int,
        include_absent: bool = True,
        working_days_only: bool = False,
        cap_to_today: bool = True,
    ) -> EmployeeMonthlyAttendanceResponse:
        """
        Detailed single-month report with daily rows and monthly totals.

        - include_absent=True: fills missing calendar days as ABSENT
        - working_days_only=True: counts only Mon–Fri (weekends entirely ignored)
        - cap_to_today=True: for the current month, count only up to local 'today'
        """
        if month < 1 or month > 12:
            raise ValueError("month must be in 1..12")

        emp = self.repo.get_employee_basic(db, employee_id)
        if not emp:
            raise LookupError("Employee not found")

        last_day = calendar.monthrange(year, month)[1]
        start = date(year, month, 1)
        end = date(year, month, last_day)

        # Avoid counting future days as ABSENT for the current month
        if cap_to_today:
            today_local = datetime.now(IST).date()
            if year == today_local.year and month == today_local.month:
                end = min(end, today_local)

        rows = self.repo.get_days_for_employee(db, employee_id, start, end)
        by_date = {r.work_date_local: r for r in rows}

        items: list[AttendanceDayItem] = []
        total_seconds = 0
        present_days = 0
        absent_days = 0
        days_counted = 0

        cursor = start
        while cursor <= end:
            if working_days_only and _is_weekend(cursor):
                cursor += timedelta(days=1)
                continue

            days_counted += 1
            r = by_date.get(cursor)
            if r:
                sw = r.seconds_worked or 0
                total_seconds += sw
                status = "PRESENT" if sw > 0 else "ABSENT"
                if status == "PRESENT":
                    present_days += 1
                else:
                    absent_days += 1
                items.append(
                    AttendanceDayItem(
                        work_date_local=cursor,
                        seconds_worked=sw,
                        hours_worked=_to_hours_minutes(sw),
                        status=status,
                        first_check_in_utc=r.first_check_in_utc,
                        last_check_out_utc=r.last_check_out_utc,
                    )
                )
            else:
                # No record for this date
                if include_absent:
                    absent_days += 1
                    items.append(
                        AttendanceDayItem(
                            work_date_local=cursor,
                            seconds_worked=0,
                            hours_worked=_to_hours_minutes(0),
                            status="ABSENT",
                            first_check_in_utc=None,
                            last_check_out_utc=None,
                        )
                    )
                # if not include_absent, we simply don't push an item for this missing day

            cursor += timedelta(days=1)

        return EmployeeMonthlyAttendanceResponse(
            employee_id=employee_id,
            employee_name=getattr(emp, "name", None),
            year=year,
            month=month,
            month_name=calendar.month_name[month],
            days_counted=days_counted,
            present_days=present_days,
            absent_days=absent_days,
            total_seconds_worked=total_seconds,
            total_hours_worked=_to_hours_minutes(total_seconds),
            avg_hours_per_present_day=_avg_hhmm(total_seconds, present_days),
            items=items,
        )
