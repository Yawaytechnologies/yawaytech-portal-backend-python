from typing import Dict, List
from datetime import datetime, timedelta, date
import calendar
import platform
import os
import sqlite3
from pathlib import Path

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.data.repositories.attendance_repository import AttendanceRepository
from app.data.models.add_employee import Employee
from app.data.models.attendance import DayStatus
from app.schemas.attendance import (
    EmployeeAttendanceResponse,
    AttendanceDayItem,
    EmployeeYearlyAttendanceResponse,
    MonthlyAttendanceItem,
    EmployeeMonthlyAttendanceResponse,
    EmployeeCheckInMonitoringResponse,
    CheckInMonitoringItem,
    VisitedSite,
)
from app.core.timeutils import (
    now_utc,
    to_local_date_ist,
    IST,
    _to_hours_minutes,
    _last_day_of_month,
    _is_weekend,
    _avg_hhmm,
)


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

        # Capture monitoring data
        self.capture_checkin_monitoring(db, sess.id)

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
                db,
                sess.employee_id,
                sess.work_date_local,
                sess.check_in_utc,
                t1,
                seconds,
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
            by_date[r.work_date_local] = AttendanceDayItem(
                work_date_local=r.work_date_local,
                seconds_worked=r.seconds_worked or 0,
                hours_worked=_to_hours_minutes(r.seconds_worked or 0),
                status=r.status,
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
                            status=DayStatus.ABSENT,
                            first_check_in_utc=None,
                            last_check_out_utc=None,
                        )
                    )
            cursor = cursor + timedelta(days=1)

        present_days = sum(1 for it in items if it.status == DayStatus.PRESENT)
        absent_days = sum(1 for it in items if it.status == DayStatus.ABSENT)

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
                if r.status == DayStatus.PRESENT:
                    present_days += 1
                else:
                    absent_days += 1
                items.append(
                    AttendanceDayItem(
                        work_date_local=cursor,
                        seconds_worked=sw,
                        hours_worked=_to_hours_minutes(sw),
                        status=r.status,
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
                            status=DayStatus.ABSENT,
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

    def get_employee_checkin_monitoring(
        self, db: Session, employee_id: str
    ) -> EmployeeCheckInMonitoringResponse:
        """
        Returns monitoring data for an employee.
        """
        emp = self.repo.get_employee_basic(db, employee_id)
        if not emp:
            raise LookupError("Employee not found")

        monitoring_rows = self.repo.get_monitoring_for_employee(db, employee_id)

        items = []
        for m in monitoring_rows:
            visited_sites = [
                VisitedSite(
                    url=site["url"],
                    title=site["title"],
                    visited_at=site["visited_at"],
                )
                for site in m.visited_sites
            ]
            items.append(
                CheckInMonitoringItem(
                    id=m.id,
                    session_id=m.session_id,
                    monitored_at_utc=m.monitored_at_utc,
                    cpu_percent=m.cpu_percent,
                    memory_percent=m.memory_percent,
                    active_apps=m.active_apps,
                    visited_sites=visited_sites,
                )
            )

        return EmployeeCheckInMonitoringResponse(
            employee_id=employee_id,
            employee_name=getattr(emp, "name", None),
            items=items,
        )

    def _get_browser_history(self, hours_back: int = 24):
        """
        Retrieves browser history from common browsers within the last N hours.
        Returns list of dicts with 'url', 'title', 'visited_at'.
        """
        import logging

        logger = logging.getLogger(__name__)
        visited_sites = []
        now = datetime.now()
        cutoff_time = now - timedelta(hours=hours_back)

        logger.info(f"Starting browser history retrieval for platform: {platform.system()}")

        # Browser history paths for different OS
        history_paths = []

        if platform.system() == "Windows":
            # Chrome
            chrome_path = (
                Path(os.environ.get("LOCALAPPDATA", ""))
                / "Google"
                / "Chrome"
                / "User Data"
                / "Default"
                / "History"
            )
            history_paths.append((chrome_path, "Chrome"))

            # Firefox
            firefox_path = Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles"
            if firefox_path.exists():
                for profile_dir in firefox_path.iterdir():
                    if profile_dir.is_dir():
                        places_path = profile_dir / "places.sqlite"
                        if places_path.exists():
                            history_paths.append((places_path, "Firefox"))
                            break

            # Edge
            edge_path = (
                Path(os.environ.get("LOCALAPPDATA", ""))
                / "Microsoft"
                / "Edge"
                / "User Data"
                / "Default"
                / "History"
            )
            history_paths.append((edge_path, "Edge"))

            # Opera
            opera_path = (
                Path(os.environ.get("APPDATA", "")) / "Opera Software" / "Opera Stable" / "History"
            )
            history_paths.append((opera_path, "Opera"))

            # Brave
            brave_path = (
                Path(os.environ.get("LOCALAPPDATA", ""))
                / "BraveSoftware"
                / "Brave-Browser"
                / "User Data"
                / "Default"
                / "History"
            )
            history_paths.append((brave_path, "Brave"))

        elif platform.system() == "Darwin":  # macOS
            # Chrome
            chrome_path = (
                Path.home()
                / "Library"
                / "Application Support"
                / "Google"
                / "Chrome"
                / "Default"
                / "History"
            )
            history_paths.append((chrome_path, "Chrome"))

            # Firefox
            firefox_path = Path.home() / "Library" / "Application Support" / "Firefox" / "Profiles"
            if firefox_path.exists():
                for profile_dir in firefox_path.iterdir():
                    if profile_dir.is_dir() and profile_dir.name.endswith(".default"):
                        places_path = profile_dir / "places.sqlite"
                        if places_path.exists():
                            history_paths.append((places_path, "Firefox"))
                            break

            # Safari (different format)
            safari_path = Path.home() / "Library" / "Safari" / "History.db"
            history_paths.append((safari_path, "Safari"))

        elif platform.system() == "Linux":
            # Chrome/Chromium
            chrome_path = Path.home() / ".config" / "google-chrome" / "Default" / "History"
            history_paths.append((chrome_path, "Chrome"))

            # Firefox
            firefox_path = Path.home() / ".mozilla" / "firefox"
            if firefox_path.exists():
                for profile_dir in firefox_path.iterdir():
                    if profile_dir.is_dir() and profile_dir.name.endswith(".default"):
                        places_path = profile_dir / "places.sqlite"
                        if places_path.exists():
                            history_paths.append((places_path, "Firefox"))
                            break

        logger.info(
            f"Found {len(history_paths)} potential browser history paths: {[str(p[0]) for p in history_paths]}"
        )

        # Extract history from each browser
        for history_path, browser_name in history_paths:
            try:
                if not history_path.exists():
                    logger.warning(
                        f"Browser history path does not exist: {history_path} for {browser_name}"
                    )
                    continue

                logger.info(f"Processing {browser_name} history at {history_path}")

                # Copy the history file to avoid locking issues
                import tempfile
                import shutil

                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_path = temp_file.name

                shutil.copy2(history_path, temp_path)
                logger.info(f"Copied history file to temp: {temp_path}")

                try:
                    conn = sqlite3.connect(f"file:{temp_path}?mode=ro", uri=True)
                    cursor = conn.cursor()

                    if browser_name in ["Chrome", "Edge"]:
                        # Chrome/Edge history query
                        # Chrome stores timestamps as microseconds since 1601-01-01
                        chrome_epoch_offset = 11644473600  # seconds from 1601-01-01 to 1970-01-01
                        cutoff_microseconds = int(
                            (cutoff_time.timestamp() + chrome_epoch_offset) * 1000000
                        )

                        cursor.execute(
                            """
                            SELECT url, title, last_visit_time
                            FROM urls
                            WHERE last_visit_time > ?
                            ORDER BY last_visit_time DESC
                            LIMIT 50
                        """,
                            (cutoff_microseconds,),
                        )

                        rows = cursor.fetchall()
                        logger.info(f"Retrieved {len(rows)} rows from {browser_name} history")
                        for row in rows:
                            url, title, timestamp = row
                            # Convert Chrome timestamp to Unix timestamp
                            unix_timestamp = (timestamp / 1000000) - chrome_epoch_offset
                            visited_at = datetime.fromtimestamp(unix_timestamp).isoformat()
                            visited_sites.append(
                                {
                                    "url": url,
                                    "title": title or "No Title",
                                    "visited_at": visited_at,
                                }
                            )

                    elif browser_name == "Firefox":
                        # Firefox history query
                        cursor.execute(
                            """
                            SELECT p.url, p.title, h.visit_date
                            FROM moz_places p
                            JOIN moz_historyvisits h ON p.id = h.place_id
                            WHERE h.visit_date > ?
                            ORDER BY h.visit_date DESC
                            LIMIT 50
                        """,
                            (int(cutoff_time.timestamp() * 1000000),),
                        )  # Firefox uses microseconds

                        rows = cursor.fetchall()
                        logger.info(f"Retrieved {len(rows)} rows from {browser_name} history")
                        for row in rows:
                            url, title, timestamp = row
                            visited_at = datetime.fromtimestamp(timestamp / 1000000).isoformat()
                            visited_sites.append(
                                {
                                    "url": url,
                                    "title": title or "No Title",
                                    "visited_at": visited_at,
                                }
                            )

                    elif browser_name == "Safari":
                        # Safari history query (different schema)
                        cursor.execute(
                            """
                            SELECT i.url, v.title, v.visit_time + 978307200
                            FROM history_items i
                            JOIN history_visits v ON i.id = v.history_item
                            WHERE v.visit_time + 978307200 > ?
                            ORDER BY v.visit_time DESC
                            LIMIT 50
                        """,
                            (cutoff_time.timestamp(),),
                        )  # Safari uses seconds since 2001-01-01

                        rows = cursor.fetchall()
                        logger.info(f"Retrieved {len(rows)} rows from {browser_name} history")
                        for row in rows:
                            url, title, timestamp = row
                            visited_at = datetime.fromtimestamp(timestamp).isoformat()
                            visited_sites.append(
                                {
                                    "url": url,
                                    "title": title or "No Title",
                                    "visited_at": visited_at,
                                }
                            )

                    conn.close()

                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass

            except Exception as e:
                logger.error(f"Error processing {browser_name} history: {e}")
                continue

        logger.info(f"Total visited sites before deduplication: {len(visited_sites)}")

        # Remove duplicates and limit to most recent 20 sites
        seen_urls = set()
        unique_sites = []
        for site in visited_sites:
            if site["url"] not in seen_urls:
                unique_sites.append(site)
                seen_urls.add(site["url"])
                if len(unique_sites) >= 20:
                    break

        logger.info(f"Final unique sites: {len(unique_sites)}")
        return unique_sites

    def capture_checkin_monitoring(self, db: Session, session_id: int):
        """
        Captures system monitoring data at check-in time.
        """
        import psutil

        monitored_at = now_utc()

        # Get CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent

        # Get active applications (running processes)
        active_apps = []
        for proc in psutil.process_iter(["pid", "name", "username"]):
            try:
                if proc.info["username"] and "system" not in proc.info["username"].lower():
                    active_apps.append(proc.info["name"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Limit to top 10 active apps
        active_apps = list(set(active_apps))[:10]

        # Get browser history
        visited_sites = self._get_browser_history(hours_back=24)

        # Save to database
        self.repo.create_monitoring(
            db=db,
            session_id=session_id,
            monitored_at_utc=monitored_at,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            active_apps=active_apps,
            visited_sites=visited_sites,
        )
