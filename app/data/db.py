# app/data/db.py
import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ Ensure mypy knows this is a definite str (not None)
if DATABASE_URL is None or DATABASE_URL.strip() == "":
    raise RuntimeError("DATABASE_URL environment variable is not set")

# (optional) pool_pre_ping helps on long-lived connections (Render, etc.)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
