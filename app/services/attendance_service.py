from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.timeutils import now_utc, to_local_date_ist, IST
from app.data.repositories.attendance_repository import AttendanceRepository
from app.data.models.add_employee import Employee  # to ensure employee exists


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
