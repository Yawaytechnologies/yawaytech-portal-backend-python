from sqlalchemy.orm import Session
from app.services import payroll_policy_service
from app.schemas.payroll_policy import PayrollPolicyCreate, PayrollPolicyUpdate


def create_policy(db: Session, policy_data: PayrollPolicyCreate):
    return payroll_policy_service.create_policy(db, policy_data)


def get_policy(db: Session, policy_id: int):
    return payroll_policy_service.get_policy(db, policy_id)


def list_policies(db: Session):
    return payroll_policy_service.list_policies(db)


def update_policy(db: Session, policy_id: int, updates: PayrollPolicyUpdate):
    return payroll_policy_service.update_policy(db, policy_id, updates)


def delete_policy(db: Session, policy_id: int):
    return payroll_policy_service.delete_policy(db, policy_id)
