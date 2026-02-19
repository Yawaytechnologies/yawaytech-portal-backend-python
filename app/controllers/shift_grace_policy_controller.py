from typing import Optional
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.data.db import get_db
from app.schemas.shift_grace_policy import (
    ShiftGracePolicyCreate,
    ShiftGracePolicyUpdate,
    ShiftGracePolicyResponse,
)
from app.services.shift_grace_policy_service import (
    create_policy_service,
    update_policy_service,
    list_policies_service,
    delete_policy_service,
)

# Controller functions wrap service calls and handle HTTP exceptions


def create_policy_controller(
    policy: ShiftGracePolicyCreate, db: Session = Depends(get_db)
) -> ShiftGracePolicyResponse:
    return create_policy_service(db, policy)


def get_policy_controller(
    policy_id: int, db: Session = Depends(get_db)
) -> ShiftGracePolicyResponse:
    policies = list_policies_service(db)
    result = next((p for p in policies if p.id == policy_id), None)
    if not result:
        raise HTTPException(status_code=404, detail="Policy not found")
    return result


def list_policies_controller(shift_id: Optional[int] = None, db: Session = Depends(get_db)):
    return list_policies_service(db, shift_id)


def update_policy_controller(
    policy_id: int, updates: ShiftGracePolicyUpdate, db: Session = Depends(get_db)
):
    updated = update_policy_service(db, policy_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Policy not found")
    return updated


def delete_policy_controller(policy_id: int, db: Session = Depends(get_db)):
    deleted = delete_policy_service(db, policy_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"detail": "Policy deleted"}
