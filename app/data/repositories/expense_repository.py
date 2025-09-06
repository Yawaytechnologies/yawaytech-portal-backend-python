# app/data/repositories/expense_repository.py
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.data.models.expenses import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


class ExpenseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: ExpenseCreate) -> Expense:
        expense = Expense(**data.model_dump())
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def list_all(self) -> list[Expense]:
        stmt = select(Expense).order_by(desc(Expense.created_at))
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, expense_id: int) -> Optional[Expense]:
        return self.db.get(Expense, expense_id)

    def update(self, expense_id: int, data: ExpenseUpdate) -> Optional[Expense]:
        expense = self.get_by_id(expense_id)
        if not expense:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(expense, k, v)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def delete(self, expense_id: int) -> bool:
        expense = self.get_by_id(expense_id)
        if not expense:
            return False
        self.db.delete(expense)
        self.db.commit()
        return True
