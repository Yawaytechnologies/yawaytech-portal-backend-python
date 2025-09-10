# app/routes/expenses_router.py
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers import expenses_controller
from app.data.db import get_db
from app.schemas.expense import (  
    Expense as ExpenseOut,
)
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    MonthlySummary,
    TotalSummary,
    YearlySummary,
)


from app.services.expense_summary_service import get_monthly_expenses, get_weekly_expenses


# Reusable DB session type (removes Ruff B008 and keeps behavior the same)
DBSession = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/expenses", tags=["Expenses"])


# ---------- CRUD ----------
@router.post("/", response_model=ExpenseOut)
def create_expense(expense: ExpenseCreate, db: DBSession):
    return expenses_controller.create_expense(db, expense)


@router.get("/", response_model=list[ExpenseOut])
def list_expenses(db: DBSession, skip: int = 0, limit: int = 10):
    return expenses_controller.get_expenses(db, skip=skip, limit=limit)


@router.get("/{expense_id}", response_model=ExpenseOut)
def read_expense(expense_id: int, db: DBSession):
    return expenses_controller.get_expense(db, expense_id)


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, expense: ExpenseUpdate, db: DBSession):
    return expenses_controller.update_expense(db, expense_id, expense)


@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: DBSession):
    return expenses_controller.delete_expense(db, expense_id)


# ---------- Summary Endpoints ----------
@router.get("/summary/total", response_model=TotalSummary)
def total_expenses(db: DBSession):
    total = expenses_controller.get_total_expenses(db)
    return {"total_expenses_all_time": total}

  
@router.get("/summary/month",response_model=MonthlySummary) 
def monthly_expenses(db: Session = Depends(get_db)):
    return expense_summary_service.get_monthly_expenses(db)


#---------------------------------------------------------

from app.schemas.expense import MonthlyTrend, HalfYearSummary

@router.get("/summary/monthly-trend", response_model=List[MonthlyTrend])
def monthly_trend(year: int, db: Session = Depends(get_db)):
    return expense_summary_service.get_monthly_trend(db, year)

@router.get("/summary/first-half", response_model=HalfYearSummary)
def first_half(year: int, db: Session = Depends(get_db)):
    return expense_summary_service.get_half_year_summary(db, year, "H1")

@router.get("/summary/second-half", response_model=HalfYearSummary)
def second_half(year: int, db: Session = Depends(get_db)):
    return expense_summary_service.get_half_year_summary(db, year, "H2")


@router.get("/summary/monthly-trend/{year}")
def monthly_trend(year: int, db: Session = Depends(get_db)):
    return expense_summary_service.get_monthly_trend(db, year)



from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.expense_summary_service import get_monthly_expenses, get_weekly_expenses
from app.data.database import get_db

router = APIRouter(prefix="/expenses/summary", tags=["Expense Summary"])

@router.get("/monthly/{year}")
def monthly_summary(year: int, db: Session = Depends(get_db)):
    return get_monthly_expenses(db, year)

@router.get("/weekly/{year}/{month}")
def weekly_summary(year: int, month: int, db: Session = Depends(get_db)):
    return get_weekly_expenses(db, year, month)


@router.get("/summary/year", response_model=YearlySummary)
def yearly_expenses(db: DBSession):
    return expenses_controller.get_yearly_expenses(db)


@router.get("/summary/month", response_model=MonthlySummary)
def monthly_expenses(db: DBSession):
    return expenses_controller.get_monthly_expenses(db)
