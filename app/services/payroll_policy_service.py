# app/services/payroll_policy_service.py
from sqlalchemy.orm import Session
from app.schemas.payroll_policy import PayrollPolicyCreate, PayrollPolicyUpdate
from app.data.models.payroll_policy import PayrollPolicy
from app.data.models.payroll_policy_rule import PayrollPolicyRule
from app.data.repositories import payroll_policy_repository


def create_policy(db: Session, data: PayrollPolicyCreate):
    policy = PayrollPolicy(
        name=data.name,
        description=data.description,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
        is_active=data.is_active,
    )
    # create rules list
    rules = [PayrollPolicyRule(**rule.dict()) for rule in data.rules]
    return payroll_policy_repository.create_policy(db, policy, rules)


def update_policy(db: Session, policy_id: int, updates: PayrollPolicyUpdate):
    policy = db.query(PayrollPolicy).filter(PayrollPolicy.id == policy_id).first()
    if not policy:
        return None

    # Update policy fields
    for k, v in updates.dict(exclude_unset=True, exclude={"rules"}).items():
        setattr(policy, k, v)

    # Update rules if provided
    if updates.rules is not None:
        # Clear existing rules (or selectively update)
        policy.rules.clear()
        for rule_data in updates.rules:
            rule = PayrollPolicyRule(**rule_data.dict(exclude_unset=True))
            policy.rules.append(rule)

    db.commit()
    db.refresh(policy)
    return policy


def get_policy(db: Session, policy_id: int):
    return db.query(PayrollPolicy).filter(PayrollPolicy.id == policy_id).first()


def list_policies(db: Session):
    return payroll_policy_repository.list_policies(db)


def delete_policy(db: Session, policy_id: int):
    policy = db.query(PayrollPolicy).filter(PayrollPolicy.id == policy_id).first()
    if policy:
        db.delete(policy)  # ✅ cascade deletes rules
        db.commit()
        return True
    return False
