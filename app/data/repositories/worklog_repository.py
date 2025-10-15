from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.data.models.worklog import Worklog


class WorklogRepository:
    def __init__(self):
        pass

    def create(self, db: Session, worklog: Worklog) -> Worklog:
        db.add(worklog)
        db.commit()
        db.refresh(worklog)
        return worklog

    def get_by_id(self, db: Session, worklog_id: int) -> Optional[Worklog]:
        return db.query(Worklog).filter(Worklog.id == worklog_id).first()

    def get_by_employee(self, db: Session, employee_id: str, skip: int = 0, limit: int = 100) -> List[Worklog]:
        return (
            db.query(Worklog)
            .filter(Worklog.employee_id == employee_id)
            .order_by(Worklog.work_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, db: Session, worklog: Worklog) -> Worklog:
        db.commit()
        db.refresh(worklog)
        return worklog

    def delete(self, db: Session, worklog: Worklog) -> None:
        db.delete(worklog)
        db.commit()

    def get_summary(self, db: Session, employee_id: str):
        total_hours = (
            db.query(func.sum(Worklog.duration_hours))
            .filter(Worklog.employee_id == employee_id)
            .scalar()
        )
        count = (
            db.query(func.count(Worklog.id))
            .filter(Worklog.employee_id == employee_id)
            .scalar()
        )
        return {"total_hours": total_hours or 0, "worklogs_count": count or 0}

    # Removed get_pending_approvals method as reviewer_id is removed
