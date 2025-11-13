from __future__ import annotations
from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import date
from sqlalchemy.orm import Session
from app.data.db import get_db
from app.controllers.attandence_controller import AttendanceController
from app.schemas.attendance import (
    CheckInResponse,
    CheckOutResponse,
    TodayStatus,
    MonthDay,
    EmployeeAttendanceResponse,
    EmployeeYearlyAttendanceResponse,
    EmployeeMonthlyAttendanceResponse,
    EmployeeCheckInMonitoringResponse,
)

router = APIRouter(prefix="/api", tags=["Attendance"])
controller = AttendanceController()


@router.post("/check-in", response_model=CheckInResponse)
def check_in(employeeId: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return controller.check_in(db, employeeId)


@router.post("/check-out", response_model=CheckOutResponse)
def check_out(employeeId: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return controller.check_out(db, employeeId)


@router.get("/today", response_model=TodayStatus)
def today(employeeId: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return controller.today_status(db, employeeId)


@router.get("/month", response_model=list[MonthDay])
def month(
    employeeId: str = Query(..., min_length=1),
    year: int = Query(..., ge=1970),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
):
    return controller.month_view(db, employeeId, year, month)


@router.get(
    "/{employee_id}/days",
    response_model=EmployeeAttendanceResponse,
    summary="Get daily attendance for an employee by employee_id",
)
def get_employee_attendance_days(
    employee_id: str,
    date_from: date = Query(..., description="Inclusive start date (YYYY-MM-DD, local IST date)"),
    date_to: date = Query(..., description="Inclusive end date (YYYY-MM-DD, local IST date)"),
    include_absent: bool = Query(True, description="Fill missing days as ABSENT"),
    db: Session = Depends(get_db),
):
    try:
        return controller.get_employee_attendance(
            db=db,
            employee_id=employee_id,
            date_from=date_from,
            date_to=date_to,
            include_absent=include_absent,
        )
    except LookupError as _:
        raise HTTPException(status_code=404, detail="Employee not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{employee_id}/months",
    response_model=EmployeeYearlyAttendanceResponse,
    summary="Get month-wise attendance for an employee in a given year",
)
def get_employee_attendance_months(
    employee_id: str,
    year: int = Query(..., ge=1900, le=3000),
    include_absent: bool = Query(True, description="Treat missing calendar days as ABSENT"),
    working_days_only: bool = Query(False, description="Only count Mon–Fri for absence fill"),
    cap_to_today: bool = Query(True, description="For current month, count only until today"),
    db: Session = Depends(get_db),
):
    try:
        return controller.service.get_employee_attendance_monthly(
            db=db,
            employee_id=employee_id,
            year=year,
            include_absent=include_absent,
            working_days_only=working_days_only,
            cap_to_today=cap_to_today,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="Employee not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{employee_id}/monitoring",
    response_model=EmployeeCheckInMonitoringResponse,
    summary="Get check-in monitoring data for an employee",
)
def get_employee_checkin_monitoring(
    employee_id: str,
    db: Session = Depends(get_db),
):
    try:
        return controller.get_employee_checkin_monitoring(db, employee_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Employee not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{employee_id}/month-report",
    response_model=EmployeeMonthlyAttendanceResponse,
    summary="Get detailed month report (per-day) for an employee",
)
def get_employee_month_report(
    employee_id: str,
    year: int = Query(..., ge=1900, le=3000),
    month: int = Query(..., ge=1, le=12),
    include_absent: bool = Query(True, description="Fill missing days as ABSENT"),
    working_days_only: bool = Query(False, description="Ignore weekends entirely"),
    cap_to_today: bool = Query(True, description="For current month, count only up to today"),
    db: Session = Depends(get_db),
) -> EmployeeMonthlyAttendanceResponse:
    try:
        return controller.get_employee_month_report(
            db=db,
            employee_id=employee_id,
            year=year,
            month=month,
            include_absent=include_absent,
            working_days_only=working_days_only,
            cap_to_today=cap_to_today,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="Employee not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
