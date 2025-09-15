from fastapi import APIRouter, Depends
from app.core.deps import require_admin, require_super_admin

router = APIRouter(prefix="/api/protected", tags=["protected"])

@router.get("/any-admin", dependencies=[Depends(require_admin)])
def only_admins():
    return {"message": "Any authenticated admin can view this"}

@router.get("/super-only", dependencies=[Depends(require_super_admin)])
def only_super():
    return {"message": "Only (the single) super admin can view this"}
