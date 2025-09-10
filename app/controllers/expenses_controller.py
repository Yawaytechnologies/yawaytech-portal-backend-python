# app/controllers/expenses_controller.py

from sqlalchemy.orm import Session

from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.services.expense_service import ExpenseService
from app.services import expense_summary_service


def get_expense(db: Session, expense_id: int):
    service = ExpenseService(db)
    return service.get_expense_by_id(expense_id)


def get_expenses(db: Session, skip: int = 0, limit: int = 100):
    service = ExpenseService(db)
    return service.get_all_expenses()


def create_expense(db: Session, expense_data: ExpenseCreate):
    service = ExpenseService(db)
    return service.create_expense(expense_data)


def update_expense(db: Session, expense_id: int, expense_data: ExpenseUpdate):
    service = ExpenseService(db)
    return service.update_expense(expense_id, expense_data)


def delete_expense(db: Session, expense_id: int) -> dict[str, str]:
    service = ExpenseService(db)
    service.delete_expense(expense_id)
    return {"detail": "Expense deleted"}


def get_total_expenses(db: Session) -> float:
    return expense_summary_service.get_total_expenses(db)


def get_yearly_expenses(db: Session) -> dict:
    return expense_summary_service.get_yearly_expenses(db)


def get_monthly_expenses(db: Session) -> dict:
    return expense_summary_service.get_monthly_expenses(db)
