from datetime import date
from typing import Optional

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.data.models.expenses import Expense


def get_total_expenses(db: Session) -> float:
    total = db.query(func.sum(Expense.amount)).scalar() or 0.0
    return round(total, 2)


def get_yearly_expenses(db: Session) -> dict:
    year = date.today().year
    total = (
        db.query(func.sum(Expense.amount))
        .filter(extract("year", Expense.date) == year)
        .scalar()
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

    return {
        "year": today.year,
        "month": today.month,
        "total_expenses_this_month": round(total, 2),
    }


def get_half_expenses(db: Session, year: int, half: str) -> dict:
    if half == "H1":
        months = (1, 6)
    elif half == "H2":
        months = (7, 12)
    else:
        raise ValueError("Invalid half value. Must be 'H1' or 'H2'")

    total = (
        db.query(func.sum(Expense.amount))
        .filter(
            extract("year", Expense.date) == year,
            extract("month", Expense.date).between(*months),
        )
        .scalar()
    ) or 0.0

    return {
        "year": year,
        "half": half,
        "total_expenses": round(total, 2),
    }


def get_monthwise_expenses(db: Session, year: int, month: Optional[int] = None) -> dict:
    query = db.query(
        extract("month", Expense.date).label("month"),
        func.sum(Expense.amount).label("total"),
    ).filter(extract("year", Expense.date) == year)

    if month:
        query = query.filter(extract("month", Expense.date) == month)

    query = query.group_by("month").order_by("month")

    results = query.all()

    monthly_totals = [
        {"month": int(month), "total": float(total)} for month, total in results
    ]

    return {"year": year, "monthly_totals": monthly_totals}


def get_weekly_expenses(db: Session, year: int, month: int) -> dict:
    # Calculate week of month: (day - 1) // 7 + 1
    week_of_month = ((extract("day", Expense.date) - 1) // 7 + 1).label("week")

    query = (
        db.query(
            week_of_month,
            func.sum(Expense.amount).label("total"),
        )
        .filter(
            extract("year", Expense.date) == year,
            extract("month", Expense.date) == month,
        )
        .group_by(week_of_month)
        .order_by(week_of_month)
    )

    results = query.all()

    weekly_totals = [
        {"week": int(week), "total": float(total)} for week, total in results
    ]

    return {"year": year, "month": month, "weekly_totals": weekly_totals}


def get_half_year_expenses(db: Session) -> dict:
    today = date.today()
    year = today.year
    half = "H1" if today.month <= 6 else "H2"
    return get_half_expenses(db, year, half)


def get_half_month_expenses(
    db: Session, year: Optional[int] = None, month: Optional[int] = None
) -> dict:
    if year is None:
        year = date.today().year
    if month is None:
        month = date.today().month

    # First half: days 1-15
    total1 = (
        db.query(func.sum(Expense.amount))
        .filter(
            extract("year", Expense.date) == year,
            extract("month", Expense.date) == month,
            extract("day", Expense.date) <= 15,
        )
        .scalar()
    ) or 0.0

    # Second half: days 16-end
    total2 = (
        db.query(func.sum(Expense.amount))
        .filter(
            extract("year", Expense.date) == year,
            extract("month", Expense.date) == month,
            extract("day", Expense.date) > 15,
        )
        .scalar()
    ) or 0.0

    return {
        "year": year,
        "month": month,
        "first_half_total": round(total1, 2),
        "second_half_total": round(total2, 2),
    }


def get_categorywise_expenses(
    db: Session, year: Optional[int] = None, month: Optional[int] = None
) -> dict:
    from datetime import date
    from calendar import monthrange

    if year is None:
        year = date.today().year
    if month is None:
        month = date.today().month

    # Calculate start and end dates for the month
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    # Query for category breakdown with transaction counts
    query = (
        db.query(
            Expense.category.label("category"),
            func.sum(Expense.amount).label("total_amount"),
            func.count(Expense.id).label("transaction_count"),
        )
        .filter(
            extract("year", Expense.date) == year,
            extract("month", Expense.date) == month,
            Expense.category.isnot(None),  # Exclude NULL categories
        )
        .group_by(Expense.category)
        .order_by(Expense.category)
    )

    results = query.all()

    # Calculate totals
    total_amount = sum(float(total) for _, total, _ in results)
    total_transactions = sum(int(count) for _, _, count in results)

    # Create breakdown list
    breakdown = [
        {"category": category, "amount": float(total), "tx_count": int(count)}
        for category, total, count in results
    ]

    return {
        "currency": "INR",
        "total_amount": round(total_amount, 2),
        "total_tx": total_transactions,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "breakdown": breakdown,
    }
