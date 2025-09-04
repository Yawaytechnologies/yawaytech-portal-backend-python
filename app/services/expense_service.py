from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.data.models import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


class ExpenseService:
    def __init__(self, db: Session):
        self.db = db

    def create_expense(self, expense_data: ExpenseCreate) -> Expense:
        expense = Expense(**expense_data.dict())
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def get_all_expenses(self) -> list[Expense]:
        return self.db.query(Expense).all()

    def get_expense_by_id(self, expense_id: int) -> Expense:
        expense = self.db.query(Expense).get(expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        return expense

    def update_expense(self, expense_id: int, data: ExpenseUpdate) -> Expense:
        expense = self.get_expense_by_id(expense_id)
        for key, value in data.dict().items():
            setattr(expense, key, value)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def delete_expense(self, expense_id: int) -> None:
        expense = self.get_expense_by_id(expense_id)
        self.db.delete(expense)
        self.db.commit()
