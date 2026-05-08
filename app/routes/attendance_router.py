from __future__ import annotations
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
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
    CheckInWithFaceResponse,
    CheckOutWithFaceResponse,
)

router = APIRouter(prefix="/api", tags=["Attendance"])
controller = AttendanceController()


@router.post("/check-in", response_model=CheckInResponse)
def check_in(employeeId: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return controller.check_in(db, employeeId)


@router.post("/check-out", response_model=CheckOutResponse)
def check_out(employeeId: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return controller.check_out(db, employeeId)


@router.post(
    "/check-in-with-face",
    response_model=CheckInWithFaceResponse,
    summary="Check-in with face verification",
)
async def check_in_with_face(
    employeeId: str = Query(..., min_length=1),
    selfie: UploadFile = File(
        ..., description="Selfie image for face verification (JPEG/PNG/WEBP, max 3MB)"
    ),
    db: Session = Depends(get_db),
):
    """
    Check-in with face verification.

    - Verifies identity by comparing selfie with stored profile image FIRST
    - ONLY creates attendance check-in if face verification succeeds (verified=true)
    - Returns 401 error if face verification fails (NO check-in recorded)
    - Saves face verification metadata for audit trail

    Returns:
    - 200: Face verified, check-in recorded successfully
    - 401: Face verification failed, NO check-in recorded
    """
    try:
        return await controller.check_in_with_face(db, employeeId, selfie)
    except HTTPException as e:
        # Re-raise HTTPException for failed face verification
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Check-in failed: {str(e)}")


@router.post(
    "/check-out-with-face",
    response_model=CheckOutWithFaceResponse,
    summary="Check-out with face verification",
)
async def check_out_with_face(
    employeeId: str = Query(..., min_length=1),
    selfie: UploadFile = File(
        ..., description="Selfie image for face verification (JPEG/PNG/WEBP, max 3MB)"
    ),
    db: Session = Depends(get_db),
):
    """
    Check-out with face verification.

    - Verifies identity by comparing selfie with stored profile image FIRST
    - ONLY records check-out if face verification succeeds (verified=true)
    - Returns 401 error if face verification fails (NO check-out recorded)
    - Saves face verification metadata for audit trail
    - Updates attendance day totals

    Returns:
    - 200: Face verified, check-out recorded successfully
    - 401: Face verification failed, NO check-out recorded
    """
    try:
        return await controller.check_out_with_face(db, employeeId, selfie)
    except HTTPException as e:
        # Re-raise HTTPException for failed face verification
        raise e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Check-out failed: {str(e)}")


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


# ──────────────────────────────────────────────────────────────────────────────
# Attendance Evidence Routes (face verification audit trail)
# ──────────────────────────────────────────────────────────────────────────────


@router.get(
    "/evidence/session/{session_id}",
    response_model=list,
    summary="Get all evidence for an attendance session",
)
def get_session_evidence(
    session_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all face verification evidence records for a specific attendance session.
    Includes both check-in and check-out evidence if available.
    """
    try:
        return controller.get_session_evidence(db, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve evidence: {str(e)}")


@router.get(
    "/evidence/employee/{employee_id}",
    response_model=list,
    summary="Get all face verification evidence for an employee",
)
def get_employee_evidence(
    employee_id: str,
    date_from: date = Query(None, description="Filter from date (YYYY-MM-DD, optional)"),
    date_to: date = Query(None, description="Filter to date (YYYY-MM-DD, optional)"),
    db: Session = Depends(get_db),
):
    """
    Get all face verification evidence records for an employee.
    Optionally filter by date range.
    """
    try:
        return controller.get_employee_evidence(db, employee_id, date_from, date_to)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve evidence: {str(e)}")
