from datetime import date

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.data.models.expenses import Expense


def get_total_expenses(db: Session) -> float:
    total = db.query(func.sum(Expense.amount)).scalar() or 0.0
    return round(total, 2)


def get_yearly_expenses(db: Session) -> dict:
    year = date.today().year
    total = (
        db.query(func.sum(Expense.amount)).filter(extract("year", Expense.date) == year).scalar()
    ) or 0.0

    return {"year": year, "total_expenses_this_year": round(total, 2)}


def get_monthly_expenses(db: Session) -> dict:
    today = date.today()
    total = (
        db.query(func.sum(Expense.amount))
        .filter(
            extract("year", Expense.date) == today.year,
            extract("month", Expense.date) == today.month,
        )
        .scalar()
    ) or 0.0

    return {"year": today.year, "month": today.month, "total_expenses_this_month": round(total, 2)}
