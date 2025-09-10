from __future__ import annotations
from sqlalchemy.orm import Session
from datetime import date
from app.services.attendance_service import AttendanceService
from app.schemas.attendance import CheckInResponse, CheckOutResponse, TodayStatus, MonthDay, EmployeeAttendanceResponse,  EmployeeMonthlyAttendanceResponse
from app.services.attendance_service import AttendanceService


class AttendanceController:
    def __init__(self, service: AttendanceService | None = None):
        self.service = service or AttendanceService()

    def check_in(self, db: Session, employee_id: str) -> CheckInResponse:
        s = self.svc.check_in(db, employee_id)
        return CheckInResponse(
            sessionId=s.id,
            employeeId=s.employee_id,
            checkInUtc=s.check_in_utc,
            workDateLocal=s.work_date_local,
        )

    def check_out(self, db: Session, employee_id: str) -> CheckOutResponse:
        s = self.svc.check_out(db, employee_id)
        worked = int((s.check_out_utc - s.check_in_utc).total_seconds()) if s.check_out_utc else 0
        return CheckOutResponse(
            sessionId=s.id,
            employeeId=s.employee_id,
            checkInUtc=s.check_in_utc,
            checkOutUtc=s.check_out_utc,
            workedSeconds=worked,
        )

    def today_status(self, db: Session, employee_id: str) -> TodayStatus:
        return TodayStatus(**self.svc.today_status(db, employee_id))

    def month_view(self, db: Session, employee_id: str, year: int, month: int) -> list[MonthDay]:
        return [MonthDay(**d) for d in self.svc.month_view(db, employee_id, year, month)]
    

    def get_employee_attendance(
        self,
        db: Session,
        employee_id: str,
        date_from: date,
        date_to: date,
        include_absent: bool,
    ) -> EmployeeAttendanceResponse:
        return self.service.get_employee_attendance(
            db=db,
            employee_id=employee_id,
            date_from=date_from,
            date_to=date_to,
            include_absent=include_absent,
        )
    


    def get_employee_month_report(
        self,
        db: Session,
        employee_id: str,
        year: int,
        month: int,
        include_absent: bool,
        working_days_only: bool,
        cap_to_today: bool,
    ) -> EmployeeMonthlyAttendanceResponse:
        return self.service.get_employee_month_report(
            db=db,
            employee_id=employee_id,
            year=year,
            month=month,
            include_absent=include_absent,
            working_days_only=working_days_only,
            cap_to_today=cap_to_today,
        )
