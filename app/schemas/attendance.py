from datetime import datetime, date
from pydantic import BaseModel


class CheckInResponse(BaseModel):
    sessionId: int
    employeeId: str
    checkInUtc: datetime
    workDateLocal: date


class CheckOutResponse(BaseModel):
    sessionId: int
    employeeId: str
    checkInUtc: datetime
    checkOutUtc: datetime
    workedSeconds: int


class TodayStatus(BaseModel):
    employeeId: str
    workDateLocal: date
    openSessionId: int | None
    openSinceUtc: datetime | None
    secondsWorkedSoFar: int
    present: bool


class MonthDay(BaseModel):
    date: date
    secondsWorked: int
    present: bool
