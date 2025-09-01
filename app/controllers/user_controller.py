# app/controllers/user_controller.py
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.data import models
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.core.security import get_password_hash


# ---------- Helpers ----------

def _email_normalized(email: str) -> str:
    # Normalize emails to avoid case-sensitive duplicates.
    return email.strip().lower()


def _raise_400(msg: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


def _raise_404(msg: str = "User not found") -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


# ---------- CRUD ----------

def create_user(db: Session, payload: UserCreate) -> models.User:
    """
    Create a new user with unique email & phone.
    Hashes the password via app.core.security.get_password_hash.
    """
    email = _email_normalized(payload.email)

    # App-level guards (fast failure)
    if db.execute(select(models.User).where(models.User.email == email)).scalar_one_or_none():
        _raise_400("Email already exists")

    if db.execute(select(models.User).where(models.User.phone == payload.phone)).scalar_one_or_none():
        _raise_400("Phone number already exists")

    user = models.User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=email,
        phone=payload.phone,
        password_hash=get_password_hash(payload.password),
    )

    db.add(user)
    try:
        # Commit can still fail if another request inserts the same email/phone in parallel.
        db.commit()
    except IntegrityError:
        db.rollback()
        _raise_400("Email or phone already exists")  # DB-level safety net
    db.refresh(user)
    return user


def get_users(db: Session, skip: int = 0, limit: int = 10) -> List[models.User]:
    """
    Paginated list of users.
    """
    stmt = select(models.User).offset(max(skip, 0)).limit(max(limit, 1))
    return list(db.execute(stmt).scalars().all())


def get_user(db: Session, user_id: int) -> models.User:
    """
    Fetch a single user by id or 404.
    """
    # SQLAlchemy 2.0 preferred API
    user = db.get(models.User, user_id)
    if not user:
        _raise_404()
    return user


def update_user(db: Session, user_id: int, payload: UserUpdate) -> models.User:
    """
    Update user fields. Keeps email/phone unique if changed.
    """
    user = get_user(db, user_id)

    # Email change → uniqueness check (normalize for storage)
    if payload.email is not None:
        new_email = _email_normalized(payload.email)
        if new_email != user.email:
            exists = db.execute(
                select(models.User).where(models.User.email == new_email, models.User.id != user.id)
            ).scalar_one_or_none()
            if exists:
                _raise_400("Email already exists")
            user.email = new_email

    # Phone change → uniqueness check
    if payload.phone is not None and payload.phone != user.phone:
        exists = db.execute(
            select(models.User).where(models.User.phone == payload.phone, models.User.id != user.id)
        ).scalar_one_or_none()
        if exists:
            _raise_400("Phone number already exists")
        user.phone = payload.phone

    # Other fields
    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.password is not None and payload.password.strip():
        user.password_hash = get_password_hash(payload.password)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        _raise_400("Email or phone already exists")
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> dict:
    """
    Delete user by id. 404 if not found.
    """
    user = get_user(db, user_id)
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}
