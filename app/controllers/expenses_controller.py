from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.data.models import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate

def get_expense(db: Session, expense_id: int):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

def get_expenses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Expense).offset(skip).limit(limit).all()

def create_expense(db: Session, expense_data: ExpenseCreate):
    expense = Expense(**expense_data.dict())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense

def update_expense(db: Session, expense_id: int, expense_data: ExpenseUpdate):
    expense = get_expense(db, expense_id)
    for key, value in expense_data.dict(exclude_unset=True).items():
        setattr(expense, key, value)
    db.commit()
    db.refresh(expense)
    return expense

def delete_expense(db: Session, expense_id: int):
    expense = get_expense(db, expense_id)
    db.delete(expense)
    db.commit()
    return {"detail": "Expense deleted"}
