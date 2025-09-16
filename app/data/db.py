# app/data/db.py
from __future__ import annotations
import os
from collections.abc import Generator
from typing import Dict, Any

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# 1) DATABASE URL (required)
#    Use Postgres (Supabase) like:
#    postgresql+psycopg://postgres:PASS@db.xxxxx.supabase.co:5432/postgres?sslmode=require
# ──────────────────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None or DATABASE_URL.strip() == "":
    raise RuntimeError("DATABASE_URL environment variable is not set")

# ──────────────────────────────────────────────────────────────────────────────
# 2) Engine options (tune without touching code)
# ──────────────────────────────────────────────────────────────────────────────
ECHO_SQL = os.getenv("DB_ECHO", "0") == "1"  # 1 = echo SQL to logs
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))  # small pool works well for Supabase/Render
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "5"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 min — drop idle conns
STATEMENT_TIMEOUT_MS = os.getenv("DB_STATEMENT_TIMEOUT_MS")  # e.g. "60000" for 60s

# UTC + optional statement timeout for Postgres (psycopg3)
connect_args: Dict[str, Any] = {}
if DATABASE_URL.startswith("postgresql+psycopg"):
    # Build -c options string safely
    opts = ["-c timezone=utc"]
    if STATEMENT_TIMEOUT_MS and STATEMENT_TIMEOUT_MS.isdigit():
        opts.append(f"-c statement_timeout={STATEMENT_TIMEOUT_MS}")
    connect_args["options"] = " ".join(opts)

# ──────────────────────────────────────────────────────────────────────────────
# 3) Engine + Session
#    pool_pre_ping=True heals broken conns (common on serverless/hosted DBs)
#    expire_on_commit=False prevents attributes from going stale between commits
# ──────────────────────────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    echo=ECHO_SQL,
    pool_pre_ping=True,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_recycle=POOL_RECYCLE,
    connect_args=connect_args,  # no-op for non-psycopg drivers
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # nicer DX for FastAPI services
    future=True,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
