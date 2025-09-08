# app/controllers/expenses_controller.py

from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.data.models import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


def _dump(model: Any) -> dict[str, Any]:
    """Pydantic v2/v1 compatible to-dict helper."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()  # type: ignore[attr-defined]


def _dump_partial(model: Any) -> dict[str, Any]:
    """Dump only provided fields (exclude_unset) for PATCH/PUT."""
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=True)
    return model.dict(exclude_unset=True)  # type: ignore[attr-defined]


def get_expense(db: Session, expense_id: int) -> Expense:
    expense = db.get(Expense, expense_id)  # SQLAlchemy 2.0 style
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


def get_expenses(db: Session, skip: int = 0, limit: int = 100) -> list[Expense]:
    stmt = select(Expense).offset(skip).limit(limit)
    rows = db.execute(stmt).scalars().all()
    # ensure a concrete list type for mypy (some stubs mark .all() as Sequence)
    return list(rows)


def create_expense(db: Session, expense_data: ExpenseCreate) -> Expense:
    data = _dump(expense_data)
    expense = Expense(**data)
    try:
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense
    except SQLAlchemyError:
        db.rollback()
        raise


def update_expense(db: Session, expense_id: int, expense_data: ExpenseUpdate) -> Expense:
    expense = get_expense(db, expense_id)
    updates = _dump_partial(expense_data)
    for key, value in updates.items():
        setattr(expense, key, value)
    try:
        db.commit()
        db.refresh(expense)
        return expense
    except SQLAlchemyError:
        db.rollback()
        raise


def delete_expense(db: Session, expense_id: int) -> dict[str, str]:
    expense = get_expense(db, expense_id)
    try:
        db.delete(expense)
        db.commit()
        return {"detail": "Expense deleted"}
    except SQLAlchemyError:
        db.rollback()
        raise
