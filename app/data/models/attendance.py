# app/features/attendance.py
from __future__ import annotations
from datetime import datetime, date, timedelta
from typing import Iterable, Optional, List, Dict

from enum import Enum
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field, validator

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from app.data.db import Base, SessionLocal
from app.data.models.add_employee import (
    Employee,
)  # uses employees.employee_id as business key
from app.data.models.policy import WorkweekPolicy, HolidayCalendar

IST = ZoneInfo("Asia/Kolkata")

# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────


class PunchType(str, Enum):
    IN = "IN"
    OUT = "OUT"


class DayStatus(str, Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    LEAVE = "Leave"
    HOLIDAY = "Holiday"
    WEEKEND = "Weekend"


# ──────────────────────────────────────────────────────────────────────────────
# Attendance models
# ──────────────────────────────────────────────────────────────────────────────


class AttendanceSession(Base):
    """
    Raw work block (IN .. OUT). Never delete in normal flow.
    """

    __tablename__ = "attendance_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business FK to employees.employee_id (unique)
    employee_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    check_in_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    check_out_utc: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Local date (IST) at check-in; used for grouping/calendar
    work_date_local: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    employee: Mapped["Employee"] = relationship("Employee", viewonly=True)

    __table_args__ = (
        Index("ix_session_emp_open", "employee_id", "check_out_utc"),
        Index("ix_session_emp_date", "employee_id", "work_date_local"),
        CheckConstraint(
            "(check_out_utc IS NULL) OR (check_out_utc >= check_in_utc)",
            name="ck_session_chronology",
        ),
    )
    # NOTE (migration): add a generated tstzrange and an exclusion constraint to prevent overlap:
    #   ALTER TABLE attendance_sessions
    #     ADD COLUMN work_range tstzrange
    #       GENERATED ALWAYS AS (tstzrange(check_in_utc, check_out_utc, '[)')) STORED;
    #   CREATE EXTENSION IF NOT EXISTS btree_gist;
    #   ALTER TABLE attendance_sessions
    #     ADD CONSTRAINT ex_sessions_no_overlap
    #     EXCLUDE USING gist (employee_id WITH =, work_range WITH &&);


class AttendanceDay(Base):
    """
    One row per employee per local date – canonical truth for payroll.
    """

    __tablename__ = "attendance_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    employee_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("employees.employee_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    work_date_local: Mapped[date] = mapped_column(Date, nullable=False)

    # Rollup metrics
    seconds_worked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expected_seconds: Mapped[int] = mapped_column(
        Integer, default=28800, nullable=False
    )  # 8h
    paid_leave_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overtime_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    underwork_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unpaid_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    first_check_in_utc: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    last_check_out_utc: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    leave_type_code: Mapped[Optional[str]] = mapped_column(String(16))
    # Use the enum's values (e.g. "Present") as the database labels so PostgreSQL
    # receives the same strings that were used when the enum type was created
    # in migrations (see alembic/versions/* where day_status_enum uses "Present",
    # "Absent", ...). values_callable tells SQLAlchemy which strings represent
    # the enum members.
    status: Mapped[DayStatus] = mapped_column(
        SAEnum(
            DayStatus,
            name="day_status_enum",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
            native_enum=True,
        ),
        default=DayStatus.PRESENT,
        nullable=False,
    )

    lock_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    employee: Mapped["Employee"] = relationship("Employee", viewonly=True)

    __table_args__ = (
        UniqueConstraint(
            "employee_id", "work_date_local", name="uq_attendance_day_emp_date"
        ),
        Index("ix_attendance_day_emp_month", "employee_id", "work_date_local"),
        CheckConstraint("seconds_worked >= 0", name="ck_day_nonnegative"),
    )


class CheckInMonitoring(Base):
    """
    Optional telemetry captured during a session.
    """

    __tablename__ = "checkin_monitoring"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("attendance_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    monitored_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    cpu_percent: Mapped[Optional[float]] = mapped_column(Float)
    memory_percent: Mapped[Optional[float]] = mapped_column(Float)

    active_apps: Mapped[List[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    visited_sites: Mapped[List[Dict]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )

    session: Mapped["AttendanceSession"] = relationship(
        "AttendanceSession", viewonly=True
    )


# ──────────────────────────────────────────────────────────────────────────────
# Utilities – policy resolution (Saturdays / Holidays) & rollup math
# ──────────────────────────────────────────────────────────────────────────────


def _nth_weekday_of_month(d: date) -> int:
    """Return ordinal of weekday in month (e.g., 1..5 for Saturdays)."""
    # e.g., for 3rd Saturday, returns 3 when d is that Saturday
    day = d.day
    return (day + 6) // 7  # 1-7 -> 1, 8-14 -> 2, 15-21 -> 3, etc.


def _is_working_day(db: Session, region: Optional[str], d: date) -> bool:
    # Default Mon–Fri working, Sat/Sun off
    weekday = d.weekday()  # Mon=0 .. Sun=6
    default = weekday <= 4

    if not region:
        return default

    policy: Optional[WorkweekPolicy] = (
        db.query(WorkweekPolicy).filter(WorkweekPolicy.region == region).one_or_none()
    )
    if not policy or not policy.policy_json:
        return default

    pj = policy.policy_json
    mapping = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
    key = mapping.get(weekday)
    rule = pj.get(key, default)

    if isinstance(rule, bool):
        return rule
    if key == "sat" and isinstance(rule, str):  # e.g., "1st,3rd"
        nth = _nth_weekday_of_month(d)
        wanted = {s.strip().lower() for s in rule.split(",")}
        return (
            (f"{nth}st" in wanted)
            or (f"{nth}nd" in wanted)
            or (f"{nth}rd" in wanted)
            or (f"{nth}th" in wanted)
        )
    return default


def _holiday_is_paid(db: Session, region: Optional[str], d: date) -> Optional[bool]:
    # Region match or global (NULL region)
    row = (
        db.query(HolidayCalendar)
        .filter(HolidayCalendar.holiday_date == d)
        .filter((HolidayCalendar.region == region) | (HolidayCalendar.region.is_(None)))
        .order_by(HolidayCalendar.region.desc().nulls_last())
        .first()
    )
    return None if not row else bool(row.is_paid)


def _employee_region(db: Session, employee_id: str) -> Optional[str]:
    emp = (
        db.query(Employee.region)
        .filter(Employee.employee_id == employee_id)
        .one_or_none()
    )
    return emp[0] if emp else None


def _sum_session_seconds(sessions: Iterable[AttendanceSession]) -> int:
    total = 0
    for s in sessions:
        if s.check_out_utc is None:
            # If not checked out, count until now (server UTC)
            end = datetime.now(tz=ZoneInfo("UTC"))
        else:
            end = s.check_out_utc
        total += int((end - s.check_in_utc).total_seconds())
    return max(0, total)


def _local_date_ist(ts_utc: datetime) -> date:
    return ts_utc.astimezone(IST).date()


# ──────────────────────────────────────────────────────────────────────────────
# Rollup core
# ──────────────────────────────────────────────────────────────────────────────


def rollup_day(db: Session, employee_id: str, d: date) -> AttendanceDay:
    """Compute and upsert AttendanceDay for employee_id on local date d."""
    region = _employee_region(db, employee_id)

    # Gather sessions
    sessions: List[AttendanceSession] = (
        db.query(AttendanceSession)
        .filter(AttendanceSession.employee_id == employee_id)
        .filter(AttendanceSession.work_date_local == d)
        .all()
    )
    seconds_worked = _sum_session_seconds(sessions)
    first_in = min((s.check_in_utc for s in sessions), default=None)
    last_out = max((s.check_out_utc for s in sessions if s.check_out_utc), default=None)

    # Policy resolution
    is_working = _is_working_day(db, region, d)
    holiday_paid = _holiday_is_paid(db, region, d)

    # Expected hours: 8h if working; 0 if weekend; holiday handled below
    expected_seconds = 8 * 3600 if is_working else 0

    # Default values
    status = DayStatus.PRESENT
    paid_leave_seconds = 0
    overtime_seconds = 0
    underwork_seconds = 0
    unpaid_seconds = 0
    leave_type_code = None

    # Holiday logic
    if holiday_paid is not None:
        if holiday_paid:
            status = DayStatus.HOLIDAY
            expected_seconds = 8 * 3600
            paid_leave_seconds = expected_seconds  # treat as paid day
        else:
            status = DayStatus.HOLIDAY
            expected_seconds = 0  # unpaid special holiday

    # Weekend logic when not holiday
    elif not is_working:
        status = DayStatus.WEEKEND
        expected_seconds = 0

    # Compute metrics if working/holiday paid
    if expected_seconds > 0:
        blended = seconds_worked + paid_leave_seconds  # paid_time considered as work
        if status == DayStatus.PRESENT or status == DayStatus.HOLIDAY:
            overtime_seconds = max(0, blended - expected_seconds)
            underwork_seconds = max(0, expected_seconds - blended)
            # If no punches & not holiday paid → Absent
            if seconds_worked == 0 and holiday_paid is None:
                status = DayStatus.ABSENT
                unpaid_seconds = expected_seconds

    # Upsert day
    day: Optional[AttendanceDay] = (
        db.query(AttendanceDay)
        .filter(
            AttendanceDay.employee_id == employee_id, AttendanceDay.work_date_local == d
        )
        .one_or_none()
    )
    if not day:
        day = AttendanceDay(employee_id=employee_id, work_date_local=d)
        db.add(day)

    day.seconds_worked = seconds_worked
    day.expected_seconds = expected_seconds
    day.paid_leave_seconds = paid_leave_seconds
    day.overtime_seconds = overtime_seconds
    day.underwork_seconds = underwork_seconds
    day.unpaid_seconds = unpaid_seconds
    day.first_check_in_utc = first_in
    day.last_check_out_utc = last_out
    day.leave_type_code = leave_type_code
    day.status = status

    return day


def recompute_range(
    db: Session, employee_ids: Iterable[str], start: date, end: date
) -> int:
    """Recompute [start..end] inclusive for listed employees."""
    if start > end:
        raise ValueError("start > end")
    n = 0
    cur = start
    while cur <= end:
        for emp in employee_ids:
            rollup_day(db, emp, cur)
            n += 1
        cur += timedelta(days=1)
    return n


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI router – punch, query, override, recompute
# ──────────────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/attendance", tags=["attendance"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class PunchInOut(BaseModel):
    employee_id: str = Field(..., examples=["YTP000003"])
    punch_type: PunchType
    punched_at_utc: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("UTC"))
    )

    @validator("punched_at_utc")
    def ensure_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("punched_at_utc must be timezone-aware (UTC)")
        return v


@router.post("/punch", summary="Employee punch IN/OUT")
def punch(payload: PunchInOut, db: Session = Depends(get_db)):
    # Validate employee exists
    if (
        not db.query(Employee)
        .filter(Employee.employee_id == payload.employee_id)
        .first()
    ):
        raise HTTPException(404, "Employee not found")

    local_day = _local_date_ist(payload.punched_at_utc)

    if payload.punch_type == PunchType.IN:
        open_exists = (
            db.query(AttendanceSession)
            .filter(
                AttendanceSession.employee_id == payload.employee_id,
                AttendanceSession.check_out_utc.is_(None),
            )
            .first()
        )
        if open_exists:
            raise HTTPException(
                409, "Open session already exists. Please check out first."
            )
        sess = AttendanceSession(
            employee_id=payload.employee_id,
            check_in_utc=payload.punched_at_utc,
            check_out_utc=None,
            work_date_local=local_day,
        )
        db.add(sess)
        db.commit()
        db.refresh(sess)
        # Rollup today (idempotent; counts until now)
        rollup_day(db, payload.employee_id, local_day)
        db.commit()
        return {"ok": True, "session_id": sess.id, "work_date_local": str(local_day)}

    else:  # OUT
        current_session: Optional[AttendanceSession] = (
            db.query(AttendanceSession)
            .filter(
                AttendanceSession.employee_id == payload.employee_id,
                AttendanceSession.check_out_utc.is_(None),
            )
            .order_by(AttendanceSession.check_in_utc.desc())
            .first()
        )
        if not current_session:
            raise HTTPException(409, "No open session found for check-out.")
        # At this point current_session is guaranteed to be non-None due to the check above
        assert current_session is not None
        if payload.punched_at_utc < current_session.check_in_utc:
            raise HTTPException(400, "Checkout earlier than check-in.")
        current_session.check_out_utc = payload.punched_at_utc
        # Ensure local date remains from check-in day
        current_session.work_date_local = _local_date_ist(current_session.check_in_utc)
        db.commit()
        # Rollup that day
        rollup_day(db, payload.employee_id, current_session.work_date_local)
        db.commit()
        return {
            "ok": True,
            "session_id": current_session.id,
            "worked_seconds": _sum_session_seconds([current_session]),
        }


class DailyQuery(BaseModel):
    employee_id: str
    start: date
    end: date


@router.get("/daily", summary="Get rolled-up daily attendance")
def get_daily(
    employee_id: str = Query(...),
    start: date = Query(...),
    end: date = Query(...),
    db: Session = Depends(get_db),
):
    if start > end:
        raise HTTPException(400, "start > end")
    q = (
        db.query(AttendanceDay)
        .filter(AttendanceDay.employee_id == employee_id)
        .filter(
            AttendanceDay.work_date_local >= start, AttendanceDay.work_date_local <= end
        )
        .order_by(AttendanceDay.work_date_local.asc())
    )
    rows = q.all()
    return [
        {
            "date": str(r.work_date_local),
            "status": r.status.name,
            "expected_seconds": r.expected_seconds,
            "seconds_worked": r.seconds_worked,
            "paid_leave_seconds": r.paid_leave_seconds,
            "overtime_seconds": r.overtime_seconds,
            "underwork_seconds": r.underwork_seconds,
            "unpaid_seconds": r.unpaid_seconds,
            "first_check_in_utc": r.first_check_in_utc,
            "last_check_out_utc": r.last_check_out_utc,
        }
        for r in rows
    ]


class OverrideRequest(BaseModel):
    status: Optional[DayStatus] = None
    expected_seconds: Optional[int] = Field(None, ge=0)
    seconds_worked: Optional[int] = Field(None, ge=0)
    paid_leave_seconds: Optional[int] = Field(None, ge=0)
    overtime_seconds: Optional[int] = Field(None, ge=0)
    underwork_seconds: Optional[int] = Field(None, ge=0)
    unpaid_seconds: Optional[int] = Field(None, ge=0)
    leave_type_code: Optional[str] = None
    note: Optional[str] = None  # implement audit trail as needed


@router.patch("/admin/daily/{employee_id}/{work_date}", summary="Admin override a day")
def admin_override_day(
    employee_id: str,
    work_date: date,
    payload: OverrideRequest = Body(...),
    db: Session = Depends(get_db),
):
    day = (
        db.query(AttendanceDay)
        .filter(
            AttendanceDay.employee_id == employee_id,
            AttendanceDay.work_date_local == work_date,
        )
        .one_or_none()
    )
    if not day:
        # create if missing
        day = AttendanceDay(employee_id=employee_id, work_date_local=work_date)
        db.add(day)

    if day.lock_flag:
        raise HTTPException(409, "Period locked. Cannot override.")

    # apply overrides
    for field in (
        "status",
        "expected_seconds",
        "seconds_worked",
        "paid_leave_seconds",
        "overtime_seconds",
        "underwork_seconds",
        "unpaid_seconds",
        "leave_type_code",
    ):
        val = getattr(payload, field)
        if val is not None:
            setattr(day, field, val)

    db.commit()
    return {"ok": True}


class RecomputeRequest(BaseModel):
    employee_ids: List[str]
    start: date
    end: date


@router.post("/admin/recompute", summary="Recompute rollups for a range")
def admin_recompute(payload: RecomputeRequest, db: Session = Depends(get_db)):
    try:
        count = recompute_range(db, payload.employee_ids, payload.start, payload.end)
        db.commit()
        return {"ok": True, "days_processed": count}
    except ValueError as e:
        raise HTTPException(400, str(e))
