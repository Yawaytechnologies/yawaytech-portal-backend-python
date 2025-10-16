from datetime import date, datetime, time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


class WorkType(str, Enum):
    FEATURE = "Feature"
    BUG_FIX = "Bug Fix"
    MEETING = "Meeting"
    TRAINING = "Training"
    SUPPORT = "Support"
    OTHER = "Other"


class WorklogStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class WorklogBase(BaseModel):
    employee_id: str
    work_date: Optional[date] = None
    task: str = Field(..., max_length=100)
    description: str
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    work_type: Optional[WorkType] = None
    status: WorklogStatus = WorklogStatus.TODO

    @validator("end_time")
    def end_time_must_be_after_start_time(cls, v, values):
        if "start_time" in values and v and values["start_time"] and v <= values["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class WorklogCreate(BaseModel):
    employee_id: str
    task: str = Field(..., max_length=100)
    description: str
    work_date: date
    work_type: WorkType
    start_time: Optional[time] = None
    end_time: Optional[time] = None

    @validator("end_time")
    def end_time_must_be_after_start_time(cls, v, values):
        if "start_time" in values and v and values["start_time"] and v <= values["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class WorklogUpdate(BaseModel):
    task: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    work_type: Optional[WorkType] = None
    status: Optional[WorklogStatus] = None


class Worklog(WorklogBase):
    id: int
    duration_hours: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorklogSummary(BaseModel):
    total_hours: float
    worklogs_count: int
