from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.data.repositories.monthly_summary_repo import upsert_summary
from app.data.models.attendance import AttendanceDay
from app.data.models.leave import LeaveRequest
from app.data.models.policy import HolidayCalendar

def aggregate_employee_month(db: Session, employee_id: str, month_start: date) -> dict:
    month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)

    # Attendance rollup
    attendance = (
        db.query(
            func.count().filter(AttendanceDay.status == "Present").label("present_days"),
            func.count().filter(AttendanceDay.status == "Leave").label("leave_days"),
            func.sum(AttendanceDay.seconds_worked).label("worked_seconds"),
            func.sum(AttendanceDay.expected_seconds).label("expected_seconds"),
            func.sum(AttendanceDay.overtime_seconds).label("overtime_seconds"),
            func.sum(AttendanceDay.underwork_seconds).label("underwork_seconds"),
        )
        .filter(
            AttendanceDay.employee_id == employee_id,  # must be str
            AttendanceDay.work_date_local >= month_start,
            AttendanceDay.work_date_local < month_end,
        )
        .one()
    )

    # Holidays
    holiday_days = (
        db.query(func.count(HolidayCalendar.id))
        .filter(
            HolidayCalendar.holiday_date >= month_start,
            HolidayCalendar.holiday_date < month_end,
        )
        .scalar()
    )

    # Leave requests
    leave = (
        db.query(
            func.sum(func.coalesce(LeaveRequest.requested_hours, 0))
                .filter(LeaveRequest.status == "APPROVED").label("approved_hours"),
            func.sum(func.coalesce(LeaveRequest.requested_hours, 0))
                .filter(LeaveRequest.status == "PENDING").label("pending_hours"),
            func.sum(func.coalesce(LeaveRequest.requested_hours, 0))
                .filter(LeaveRequest.status == "REJECTED").label("unpaid_hours"),
            func.count().filter(LeaveRequest.status == "APPROVED").label("approved_days"),
            func.count().filter(LeaveRequest.status == "REJECTED").label("unpaid_days"),
            func.count().filter(LeaveRequest.status == "PENDING").label("pending_days"),

        )
        .filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.start_datetime >= month_start,
            LeaveRequest.start_datetime < month_end,
        )
        .one()
    )

    # Leave type breakdown
    leave_breakdown = {
        leave_type_id: float(total_hours) if total_hours is not None else 0.0
        for leave_type_id, total_hours in db.query(
            LeaveRequest.leave_type_id, func.sum(LeaveRequest.requested_hours)
        )
        .filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.start_datetime >= month_start,
            LeaveRequest.start_datetime < month_end,
            LeaveRequest.status == "APPROVED"
        )
        .group_by(LeaveRequest.leave_type_id)
        .all()
    }

    return {
        "employee_id": employee_id,
        "month_start": month_start,
        "total_work_days": (attendance.present_days or 0) + (attendance.leave_days or 0),
        "present_days": attendance.present_days or 0,
        "holiday_days": holiday_days or 0,
        "weekend_days": 0,  # TODO: calculate from workweek_policies
        "leave_days": attendance.leave_days or 0,
        "paid_leave_hours": float(leave.approved_hours or 0),
        "unpaid_leave_hours": float(leave.unpaid_hours or 0),
        "pending_leave_hours": float(leave.pending_hours or 0),
        "total_worked_hours": float((attendance.worked_seconds or 0) / 3600),
        "expected_hours": float((attendance.expected_seconds or 0) / 3600),
        "overtime_hours": float((attendance.overtime_seconds or 0) / 3600),
        "underwork_hours": float((attendance.underwork_seconds or 0) / 3600),
        "leave_type_breakdown": leave_breakdown,
    }

def generate_monthly_summary(db: Session, employee_id: str, month_start: date):
    summary_data = aggregate_employee_month(db, employee_id, month_start)
    return upsert_summary(db, summary_data)