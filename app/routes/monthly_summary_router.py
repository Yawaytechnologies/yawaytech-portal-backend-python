from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.controllers.montly_summary_ctrl import (
    get_employee_summary,
    get_month_summaries,
    rollup_month_summaries,
)
from app.data.db import get_db
from app.data.models.add_employee import Employee  # assuming you have an Employee model

router = APIRouter(prefix="/monthly-summary", tags=["Monthly Summary"])

# ✅ List all summaries for a given month
@router.get("/")
def list_month_summaries(month_start: date, db: Session = Depends(get_db)):
    summaries = get_month_summaries(db, month_start)
    return summaries

# ✅ Get a single employee’s summary for a given month
@router.get("/employee/{employee_id}")
def employee_summary(employee_id: str, month_start: date, db: Session = Depends(get_db)):
    summary = get_employee_summary(db, employee_id, month_start)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary

# ✅ Trigger rollup for all employees for a given month
@router.post("/rollup")
def rollup(month_start: date, db: Session = Depends(get_db)):
    employees = [e.employee_id for e in db.query(Employee).all()]
    results = rollup_month_summaries(db, month_start, employees)
    return {"generated": len(results), "summaries": results}
