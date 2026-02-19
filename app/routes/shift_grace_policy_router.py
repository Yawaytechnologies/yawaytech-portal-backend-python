from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.data.db import get_db
from app.schemas.shift_grace_policy import (
    ShiftGracePolicyCreate,
    ShiftGracePolicyUpdate,
    ShiftGracePolicyResponse,
)
from app.controllers.shift_grace_policy_controller import (
    create_policy_controller,
    get_policy_controller,
    list_policies_controller,
    update_policy_controller,
    delete_policy_controller,
)

router = APIRouter(prefix="/shift-grace-policies", tags=["Shift Grace Policies"])


@router.post("/", response_model=ShiftGracePolicyResponse)
def create_policy(policy: ShiftGracePolicyCreate, db: Session = Depends(get_db)):
    return create_policy_controller(policy, db)


@router.get("/{policy_id}", response_model=ShiftGracePolicyResponse)
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    return get_policy_controller(policy_id, db)


@router.get("/", response_model=list[ShiftGracePolicyResponse])
def list_policies(shift_id: Optional[int] = None, db: Session = Depends(get_db)):
    return list_policies_controller(shift_id, db)


@router.put("/{policy_id}", response_model=ShiftGracePolicyResponse)
def update_policy(policy_id: int, updates: ShiftGracePolicyUpdate, db: Session = Depends(get_db)):
    return update_policy_controller(policy_id, updates, db)


@router.delete("/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    return delete_policy_controller(policy_id, db)
