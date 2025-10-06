from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.controllers.worklog_controller import WorklogController
from app.schemas.worklog import Worklog, WorklogCreate, WorklogUpdate
from app.core.deps import get_db

router = APIRouter(prefix="/worklog", tags=["worklog"])
controller = WorklogController()


@router.post("/", response_model=Worklog, status_code=status.HTTP_201_CREATED)
def create_worklog(worklog_create: WorklogCreate, db: Session = Depends(get_db)):
    return controller.create_worklog(db, worklog_create)


@router.get("/{worklog_id}", response_model=Worklog)
def get_worklog(worklog_id: int, db: Session = Depends(get_db)):
    worklog = controller.get_worklog(db, worklog_id)
    if not worklog:
        raise HTTPException(status_code=404, detail="Worklog not found")
    return worklog


@router.get("/employee/{employee_id}", response_model=List[Worklog])
def get_worklogs_for_employee(employee_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return controller.get_worklogs_for_employee(db, employee_id, skip, limit)


@router.put("/{worklog_id}", response_model=Worklog)
def update_worklog(worklog_id: int, worklog_update: WorklogUpdate, db: Session = Depends(get_db)):
    worklog = controller.update_worklog(db, worklog_id, worklog_update)
    if not worklog:
        raise HTTPException(status_code=404, detail="Worklog not found")
    return worklog

from datetime import datetime

@router.put("/{worklog_id}/times", response_model=Worklog)
def update_work_times(worklog_id: int, start_time: datetime, end_time: datetime, db: Session = Depends(get_db)):
    worklog = controller.update_work_times(db, worklog_id, start_time, end_time)
    if not worklog:
        raise HTTPException(status_code=404, detail="Worklog not found")
    return worklog


@router.delete("/{worklog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worklog(worklog_id: int, db: Session = Depends(get_db)):
    success = controller.delete_worklog(db, worklog_id)
    if not success:
        raise HTTPException(status_code=404, detail="Worklog not found")
    return None


@router.post("/{worklog_id}/checkin", response_model=Worklog)
def checkin_worklog(worklog_id: int, db: Session = Depends(get_db)):
    worklog = controller.checkin_worklog(db, worklog_id)
    if not worklog:
        raise HTTPException(status_code=404, detail="Worklog not found")
    return worklog


@router.post("/{worklog_id}/checkout", response_model=Worklog)
def checkout_worklog(worklog_id: int, db: Session = Depends(get_db)):
    worklog = controller.checkout_worklog(db, worklog_id)
    if not worklog:
        raise HTTPException(status_code=404, detail="Worklog not found")
    return worklog


@router.post("/{worklog_id}/start", response_model=Worklog)
def start_progress_worklog(worklog_id: int, db: Session = Depends(get_db)):
    worklog = controller.start_progress_worklog(db, worklog_id)
    if not worklog:
        raise HTTPException(status_code=404, detail="Worklog not found")
    return worklog
