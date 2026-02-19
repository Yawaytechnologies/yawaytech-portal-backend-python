from sqlalchemy.orm import Session
from app.data.models.payroll_policy import PayrollPolicy
from app.data.models.payroll_policy_rule import PayrollPolicyRule


def create_policy(db: Session, policy: PayrollPolicy, rules: list[PayrollPolicyRule]):
    db.add(policy)
    for rule in rules:
        policy.rules.append(rule)
    db.commit()
    db.refresh(policy)
    return policy


def get_policy(db: Session, policy_id: int):
    return db.query(PayrollPolicy).filter(PayrollPolicy.id == policy_id).first()


def list_policies(db: Session):
    return db.query(PayrollPolicy).all()


def update_policy(db: Session, policy_id: int, updates: dict):
    policy = get_policy(db, policy_id)
    if not policy:
        return None
    for key, value in updates.items():
        setattr(policy, key, value)
    db.commit()
    db.refresh(policy)
    return policy


def delete_policy(db: Session, policy_id: int):
    policy = get_policy(db, policy_id)
    if not policy:
        return None
    db.delete(policy)
    db.commit()
    return policy
