from typing import Optional
from sqlalchemy.orm import Session
from app.data.models.shift_grace_policy import ShiftGracePolicy


def create_policy(db: Session, policy_data):
    policy = ShiftGracePolicy(**policy_data.dict())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def get_policy(db: Session, policy_id: int):
    return db.query(ShiftGracePolicy).filter(ShiftGracePolicy.id == policy_id).first()


def list_policies(db: Session, shift_id: Optional[int] = None):
    query = db.query(ShiftGracePolicy)
    if shift_id:
        query = query.filter(ShiftGracePolicy.shift_id == shift_id)
    return query.all()


def update_policy(db: Session, policy_id: int, updates):
    policy = get_policy(db, policy_id)
    if not policy:
        return None
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(policy, key, value)
    db.commit()
    db.refresh(policy)
    return policy


def delete_policy(db: Session, policy_id: int):
    policy = get_policy(db, policy_id)
    if policy:
        db.delete(policy)
        db.commit()
    return policy
