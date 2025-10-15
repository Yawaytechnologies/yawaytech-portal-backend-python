from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.services.worklog_service import WorklogService
from app.schemas.worklog import Worklog, WorklogCreate, WorklogUpdate, WorklogSummary


class WorklogController:
    def __init__(self):
        pass

    def create_worklog(self, db: Session, worklog_create: WorklogCreate) -> Worklog:
        service = WorklogService(db)
        return service.create_worklog(worklog_create)

    def get_worklog(self, db: Session, worklog_id: int) -> Optional[Worklog]:
        service = WorklogService(db)
        return service.get_worklog(worklog_id)

    def get_worklogs_for_employee(
        self, db: Session, employee_id: str, skip: int = 0, limit: int = 100
    ) -> List[Worklog]:
        service = WorklogService(db)
        return service.get_worklogs_for_employee(employee_id, skip, limit)

    def update_worklog(
        self, db: Session, worklog_id: int, worklog_update: WorklogUpdate
    ) -> Optional[Worklog]:
        service = WorklogService(db)
        return service.update_worklog(worklog_id, worklog_update)

    def delete_worklog(self, db: Session, worklog_id: int) -> bool:
        service = WorklogService(db)
        return service.delete_worklog(worklog_id)

    def get_summary(self, db: Session, employee_id: str) -> WorklogSummary:
        service = WorklogService(db)
        summary = service.get_summary(employee_id)
        return WorklogSummary(**summary)

    def checkin_worklog(self, db: Session, worklog_id: int) -> Optional[Worklog]:
        service = WorklogService(db)
        return service.checkin_worklog(worklog_id)

    def checkout_worklog(self, db: Session, worklog_id: int) -> Optional[Worklog]:
        service = WorklogService(db)
        return service.checkout_worklog(worklog_id)

    def start_progress_worklog(self, db: Session, worklog_id: int) -> Optional[Worklog]:
        service = WorklogService(db)
        return service.start_progress_worklog(worklog_id)

    def update_work_times(
        self, db: Session, worklog_id: int, start_time: datetime, end_time: datetime
    ) -> Optional[Worklog]:
        service = WorklogService(db)
        return service.update_work_times(worklog_id, start_time, end_time)
