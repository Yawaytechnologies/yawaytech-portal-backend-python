from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.schemas.expense import Expense, ExpenseCreate, ExpenseUpdate
from app.controllers import expenses_controller
from app.data.db import get_db

router = APIRouter(prefix="/expenses", tags=["Expenses"])

@router.post("/", response_model=Expense)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    return expenses_controller.create_expense(db, expense)

@router.get("/", response_model=List[Expense])
def list_expenses(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return expenses_controller.get_expenses(db, skip=skip, limit=limit)

@router.get("/{expense_id}", response_model=Expense)
def read_expense(expense_id: int, db: Session = Depends(get_db)):
    return expenses_controller.get_expense(db, expense_id)

@router.put("/{expense_id}", response_model=Expense)
def update_expense(expense_id: int, expense: ExpenseUpdate, db: Session = Depends(get_db)):
    return expenses_controller.update_expense(db, expense_id, expense)

@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    return expenses_controller.delete_expense(db, expense_id)
