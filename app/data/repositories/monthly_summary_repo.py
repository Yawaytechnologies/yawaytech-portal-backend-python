from sqlalchemy.orm import Session
from datetime import date
from app.data.models.monthly_summary import MonthlyEmployeeSummary


def get_summary(db: Session, employee_id: str, month_start: date):
    return (
        db.query(MonthlyEmployeeSummary)
        .filter_by(employee_id=employee_id, month_start=month_start)
        .first()
    )


def upsert_summary(db: Session, summary_data: dict):
    existing = get_summary(db, summary_data["employee_id"], summary_data["month_start"])
    if existing:
        for key, value in summary_data.items():
            setattr(existing, key, value)
    else:
        db.add(MonthlyEmployeeSummary(**summary_data))
    db.commit()
    return existing or summary_data


def list_summaries(db: Session, month_start: date):
    return db.query(MonthlyEmployeeSummary).filter_by(month_start=month_start).all()
