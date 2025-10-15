from __future__ import annotations
from enum import Enum
from sqlalchemy import Column, Date, Float, Integer, String, Text, DateTime, Enum as SqlEnum, func

from app.data.db import Base


class ExpenseCategory(str, Enum):
    FOOD = "Food"
    TRANSPORT = "Transport"
    UTILITIES = "Utilities"
    ENTERTAINMENT = "Entertainment"
    PROGRESS = "Progress"
    OTHER = "Other"  # Optional catch-all category



class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(SqlEnum(ExpenseCategory, name="expense_category"), nullable=False)

    date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)  # Text is better for longer content
    added_by = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
