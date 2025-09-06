from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.data.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate

class ExpenseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ExpenseCreate) -> Expense:
        obj = Expense(**data.model_dump(exclude_unset=True))
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list(self) -> List[Expense]:
        stmt = select(Expense).order_by(desc(Expense.id))
        return list(self.db.execute(stmt).scalars().all())

    def get(self, expense_id: int) -> Optional[Expense]:
        return self.db.get(Expense, expense_id)

    def update(self, obj: Expense, data: ExpenseUpdate) -> Expense:
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: Expense) -> None:
        self.db.delete(obj)
        self.db.commit()
