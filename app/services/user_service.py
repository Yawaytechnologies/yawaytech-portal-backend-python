# app/services/user_service.py
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.data.repositories.user_repository import (
    get_user_by_email,
    get_user_by_phone,
    create_user_record,
)
from app.schemas.user_schemas import SignUpIn, UserOut

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _hash_password(raw: str) -> str:
    return pwd_ctx.hash(raw)

def register_user(db: Session, payload: SignUpIn) -> UserOut:
    # Uniqueness checks
    if get_user_by_email(db, payload.email):
        raise ValueError("Email already in use")
    if get_user_by_phone(db, payload.phone):
        raise ValueError("Phone already in use")

    user = create_user_record(
        db=db,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        password_hash=_hash_password(payload.password),
    )
    return UserOut.model_validate(user)
