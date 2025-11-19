from datetime import date
from typing import Optional

from pydantic import BaseModel


class ExpenseBase(BaseModel):
    title: str
    amount: float
    category: str
    date: date
    description: str | None = None
    added_by: str


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(ExpenseBase):
    pass


class Expense(ExpenseBase):
    id: int

    class Config:
        from_attributes = True


class TotalSummary(BaseModel):
    total_expenses_all_time: float


class YearlySummary(BaseModel):
    year: int
    total_expenses_this_year: float


class MonthlySummary(BaseModel):
    year: int
    month: int
    total_expenses_this_month: float


class HalfSummary(BaseModel):
    year: int
    half: str
    total_expenses: float


class MonthlyTotal(BaseModel):
    month: int
    total: float


class MonthwiseSummary(BaseModel):
    year: int
    monthly_totals: list[MonthlyTotal]


class WeeklyTotal(BaseModel):
    week: int
    total: float


class WeeklySummary(BaseModel):
    year: int
    month: int
    weekly_totals: list[WeeklyTotal]


class CategoryTotal(BaseModel):
    category: str
    total: float


class CategorywiseSummary(BaseModel):
    year: int
    month: int
    category_totals: list[CategoryTotal]


class CategoryBreakdown(BaseModel):
    category: str
    amount: float
    tx_count: int


class CategorySummaryResponse(BaseModel):
    currency: str
    total_amount: float
    total_tx: int
    start_date: str
    end_date: str
    breakdown: list[CategoryBreakdown]
