# app/routers/user_router.py
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.data.db import get_db
from app.data import models
from app.controllers import user_controller
from app.schemas.user_schemas import (
    UserCreate,
    UserOut,
    UserUpdate,
    UserLogin,
    AuthResponse,
)
from app.core.security import create_access_token, verify_password

router = APIRouter(prefix="/users", tags=["Users"])


# ---------- Auth Endpoints ----------

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user and return an access token + sanitized user object.
    If your UserCreate schema already enforces password==confirm_password via a validator,
    this route will simply trust it. Otherwise, the explicit check below will catch it.
    """
    # Optional safety if your schema doesn't already validate this:
    if hasattr(payload, "confirm_password") and (payload.password != payload.confirm_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    user = user_controller.create_user(db, payload)
    token = create_access_token(subject=str(user.id), claims={"email": user.email})
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=AuthResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Login with JSON body:
      { "email": "user@example.com", "password": "secret" }
    Returns access token + sanitized user object.
    """
    email = payload.email.strip().lower()

    # SQLAlchemy 2.0 style
    user: models.User | None = db.execute(
        select(models.User).where(models.User.email == email)
    ).scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(subject=str(user.id), claims={"email": user.email})
    return {"access_token": token, "token_type": "bearer", "user": user}


# ---------- User CRUD Endpoints ----------

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_route(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Admin/utility endpoint to create a user (no token response).
    """
    # Optional safety if schema doesn't validate:
    if hasattr(payload, "confirm_password") and (payload.password != payload.confirm_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")
    return user_controller.create_user(db, payload)


@router.get("/", response_model=List[UserOut])
def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return user_controller.get_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserOut)
def read_user(user_id: int, db: Session = Depends(get_db)):
    return user_controller.get_user(db, user_id)


@router.put("/{user_id}", response_model=UserOut)
def update_user_route(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    return user_controller.update_user(db, user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user_route(user_id: int, db: Session = Depends(get_db)):
    return user_controller.delete_user(db, user_id)
