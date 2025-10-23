from datetime import datetime, time
from typing import List, Optional

from sqlalchemy.orm import Session

from app.data.models.worklog import Worklog, WorklogStatus
from app.data.repositories.worklog_repository import WorklogRepository
from app.schemas.worklog import WorklogCreate, WorklogUpdate


class WorklogService:
    def __init__(self, db: Session, repo: WorklogRepository | None = None):
        self.db = db
        self.repo = repo or WorklogRepository()

    def create_worklog(self, worklog_create: WorklogCreate) -> Worklog:
        duration = None
        if worklog_create.start_time and worklog_create.end_time:
            if worklog_create.end_time <= worklog_create.start_time:
                raise ValueError("end_time must be after start_time")
            # Calculate duration by combining times with a dummy date
            start_dt = datetime.combine(datetime.min.date(), worklog_create.start_time)
            end_dt = datetime.combine(datetime.min.date(), worklog_create.end_time)
            duration = (end_dt - start_dt).total_seconds() / 3600.0
        worklog = Worklog(
            employee_id=worklog_create.employee_id,
            work_date=worklog_create.work_date,
            task=worklog_create.task,
            description=worklog_create.description,
            start_time=worklog_create.start_time,
            end_time=worklog_create.end_time,
            duration_hours=duration,
            work_type=worklog_create.work_type,
            status=WorklogStatus.TODO,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return self.repo.create(self.db, worklog)

    def get_worklog(self, worklog_id: int) -> Optional[Worklog]:
        return self.repo.get_by_id(self.db, worklog_id)

    def get_worklogs_for_employee(
        self, employee_id: str, skip: int = 0, limit: int = 100
    ) -> List[Worklog]:
        return self.repo.get_by_employee(self.db, employee_id, skip, limit)

    def update_worklog(self, worklog_id: int, worklog_update: WorklogUpdate) -> Optional[Worklog]:
        worklog = self.repo.get_by_id(self.db, worklog_id)
        if not worklog:
            return None

        for field, value in worklog_update.dict(exclude_unset=True).items():
            setattr(worklog, field, value)

        if worklog.start_time and worklog.end_time:
            if worklog.end_time <= worklog.start_time:
                raise ValueError("end_time must be after start_time")
            # Calculate duration by combining times with a dummy date
            start_dt = datetime.combine(datetime.min.date(), worklog.start_time)
            end_dt = datetime.combine(datetime.min.date(), worklog.end_time)
            worklog.duration_hours = (end_dt - start_dt).total_seconds() / 3600.0

        worklog.updated_at = datetime.utcnow()
        return self.repo.update(self.db, worklog)

    def delete_worklog(self, worklog_id: int) -> bool:
        worklog = self.repo.get_by_id(self.db, worklog_id)
        if not worklog:
            return False
        self.repo.delete(self.db, worklog)
        return True

    def get_summary(self, employee_id: str):
        return self.repo.get_summary(self.db, employee_id)

    def checkin_worklog(self, worklog_id: int) -> Optional[Worklog]:
        worklog = self.repo.get_by_id(self.db, worklog_id)
        if not worklog:
            return None
        worklog.start_time = datetime.utcnow().time()
        worklog.status = WorklogStatus.TODO
        worklog.updated_at = datetime.utcnow()
        return self.repo.update(self.db, worklog)

    def checkout_worklog(self, worklog_id: int) -> Optional[Worklog]:
        worklog = self.repo.get_by_id(self.db, worklog_id)
        if not worklog:
            return None
        worklog.end_time = datetime.utcnow().time()
        worklog.status = WorklogStatus.DONE
        if worklog.start_time:
            # Calculate duration by combining times with a dummy date
            start_dt = datetime.combine(datetime.min.date(), worklog.start_time)
            end_dt = datetime.combine(datetime.min.date(), worklog.end_time)
            worklog.duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
        worklog.updated_at = datetime.utcnow()
        return self.repo.update(self.db, worklog)

    def start_progress_worklog(self, worklog_id: int) -> Optional[Worklog]:
        worklog = self.repo.get_by_id(self.db, worklog_id)
        if not worklog:
            return None
        worklog.status = WorklogStatus.IN_PROGRESS
        worklog.updated_at = datetime.utcnow()
        return self.repo.update(self.db, worklog)

    def update_work_times(
        self, worklog_id: int, start_time: time, end_time: time
    ) -> Optional[Worklog]:
        if end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        worklog = self.repo.get_by_id(self.db, worklog_id)
        if not worklog:
            return None
        worklog.start_time = start_time
        worklog.end_time = end_time
        worklog.status = WorklogStatus.IN_PROGRESS
        # Calculate duration by combining times with a dummy date
        start_dt = datetime.combine(datetime.min.date(), start_time)
        end_dt = datetime.combine(datetime.min.date(), end_time)
        worklog.duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
        worklog.updated_at = datetime.utcnow()
        return self.repo.update(self.db, worklog)
