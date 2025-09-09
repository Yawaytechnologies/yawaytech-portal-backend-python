from sqlalchemy.orm import Session
from app.services.attendance_service import AttendanceService
from app.schemas.attendance import CheckInResponse, CheckOutResponse, TodayStatus, MonthDay


class AttendanceController:
    def __init__(self):
        self.svc = AttendanceService()

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
