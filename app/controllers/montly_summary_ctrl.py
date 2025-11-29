from datetime import date
from sqlalchemy.orm import Session
from app.services.monthly_summary_service import generate_monthly_summary
from app.data.repositories.monthly_summary_repo import list_summaries, get_summary

def get_employee_summary(db: Session, employee_id: str, month_start: date):
    return get_summary(db, employee_id, month_start)

def get_month_summaries(db: Session, month_start: date):
    return list_summaries(db, month_start)

def rollup_month_summaries(db: Session, month_start: date, employees: list[str]):
    results = []
    for emp in employees:
        results.append(generate_monthly_summary(db, emp, month_start))
    return results