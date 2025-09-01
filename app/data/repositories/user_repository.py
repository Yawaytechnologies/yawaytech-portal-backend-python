# app/data/repositories/user_repository.py
from sqlalchemy.orm import Session
from typing import Optional, List
from app.data.models import User  # ensure this model has a 'password_hash' column

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
    return db.query(User).filter(User.phone == phone).first()

def create_user_record(
    db: Session,
    *,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    password_hash: str,
) -> User:
    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        password_hash=password_hash,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def list_users(db: Session, limit: int = 50, offset: int = 0) -> List[User]:
    return (
        db.query(User)
        .order_by(User.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
