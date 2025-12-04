from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.controllers import payroll_policy_controller
from app.schemas.payroll_policy import PayrollPolicyCreate, PayrollPolicyRead, PayrollPolicyUpdate
from app.data.db import get_db
from typing import List

router = APIRouter(prefix="/policies", tags=["Payroll Policies"])


@router.post("/", response_model=PayrollPolicyRead)
def create_policy(policy: PayrollPolicyCreate, db: Session = Depends(get_db)):
    return payroll_policy_controller.create_policy(db, policy)


@router.get("/{policy_id}", response_model=PayrollPolicyRead)
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = payroll_policy_controller.get_policy(db, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.get("/", response_model=List[PayrollPolicyRead])
def list_policies(db: Session = Depends(get_db)):
    return payroll_policy_controller.list_policies(db)


@router.put("/{policy_id}", response_model=PayrollPolicyRead)
def update_policy(policy_id: int, updates: PayrollPolicyUpdate, db: Session = Depends(get_db)):
    policy = payroll_policy_controller.update_policy(db, policy_id, updates)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.delete("/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    result = payroll_policy_controller.delete_policy(db, policy_id)
    if not result:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"message": "Policy deleted successfully"}
