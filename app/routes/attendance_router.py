from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.data.db import get_db
from app.controllers.attandence_controller import AttendanceController
from app.schemas.attendance import CheckInResponse, CheckOutResponse, TodayStatus, MonthDay

router = APIRouter(prefix="/attendance", tags=["Attendance"])
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
