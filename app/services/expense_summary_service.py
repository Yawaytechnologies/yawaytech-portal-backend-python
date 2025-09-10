from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date
from app.data.models import Expense




def get_total_expenses(db: Session) -> float:
    total = db.query(func.sum(Expense.amount)).scalar() or 0.0
    return round(total, 2)

def get_yearly_expenses(db: Session) -> dict:
    year = date.today().year
    total = (
        db.query(func.sum(Expense.amount))
          .filter(extract('year', Expense.date) == year)
          .scalar()
    ) or 0.0

    return {"year": year, "total_expenses_this_year": round(total, 2)}

def get_monthly_expenses(db: Session) -> dict:
    today = date.today()
    total = (
        db.query(func.sum(Expense.amount))
          .filter(
              extract('year', Expense.date) == today.year,
              extract('month', Expense.date) == today.month
          )
          .scalar()
    ) or 0.0

    return {
        "year": today.year,
        "month": today.month,
        "total_expenses_this_month": round(total, 2)
    }





# def get_monthly_trend(db: Session, year: int) -> list[dict]:
#     results = (
#         db.query(extract('month', Expense.date).label("month"),
#                  func.sum(Expense.amount).label("total"))
#         .filter(extract('year', Expense.date) == year)
#         .group_by("month")
#         .order_by("month")
#         .all()
#     )
#     # Convert to list of dicts
#     return [{"month": int(month), "total": float(total)} for month, total in results]


def get_monthly_trend(db: Session, year: int) -> list[dict]:
    results = (
        db.query(
            extract('month', Expense.date).label("month"),
            func.sum(Expense.amount).label("total")
        )
        .filter(extract('year', Expense.date) == year)
        .group_by("month")
        .order_by("month")
        .all()
    )

    # Convert query result to dictionary {month: total}
    month_totals = {int(month): float(total) for month, total in results}

    # Always return 12 months (fill missing with 0.0)
    return [
        {"month": m, "total": round(month_totals.get(m, 0.0), 2)}
        for m in range(1, 13)
    ]


def get_half_year_summary(db: Session, year: int, half: str) -> dict:
    if half == "H1":   # Jan–Jun
        start_month, end_month = 1, 6
    else:              # Jul–Dec
        start_month, end_month = 7, 12

    total = (
        db.query(func.sum(Expense.amount))
          .filter(extract('year', Expense.date) == year)
          .filter(extract('month', Expense.date).between(start_month, end_month))
          .scalar()
    ) or 0.0

    return {"year": year, "half": half, "total": round(total, 2)}



# app/services/expense_summary_service.py

# def get_monthly_trend(db: Session, year: int) -> list[dict]:
#     results = (
#         db.query(
#             extract('month', Expense.date).label("month"),
#             func.sum(Expense.amount).label("total")
#         )
#         .filter(extract('year', Expense.date) == year)
#         .group_by("month")
#         .order_by("month")
#         .all()
#     )

#     month_totals = {int(month): float(total) for month, total in results}

#     return [
#         {"month": m, "total": round(month_totals.get(m, 0.0), 2)}
#         for m in range(1, 13)
#     ]





from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date
from calendar import monthrange
from app.data.models import Expense


def get_monthly_expenses(db: Session, year: int) -> list[dict]:
    results = (
        db.query(
            extract('month', Expense.date).label('month'),
            func.sum(Expense.amount).label('total')
        )
        .filter(extract('year', Expense.date) == year)
        .group_by('month')
        .all()
    )

    return [
        {"year": year, "month": int(month), "total": round(total, 2) if total else 0.0}
        for month, total in results
    ]


def get_weekly_expenses(db: Session, year: int, month: int) -> list[dict]:
    # Number of days in the month
    days_in_month = monthrange(year, month)[1]

    results = []
    start_day = 1
    week_number = 1

    while start_day <= days_in_month:
        end_day = min(start_day + 6, days_in_month)

        total = (
            db.query(func.sum(Expense.amount))
              .filter(
                  extract('year', Expense.date) == year,
                  extract('month', Expense.date) == month,
                  extract('day', Expense.date) >= start_day,
                  extract('day', Expense.date) <= end_day
              )
              .scalar()
        ) or 0.0

        results.append({
            "year": year,
            "month": month,
            "week": week_number,
            "start_day": start_day,
            "end_day": end_day,
            "total_expenses": round(total, 2)
        })

        start_day += 7
        week_number += 1

    return results

