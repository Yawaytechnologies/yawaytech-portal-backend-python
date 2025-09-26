# app/data/db.py
from __future__ import annotations
import os
from collections.abc import Generator
from typing import Any, Dict

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Load .env before reading variables
load_dotenv()

# Prefer DATABASE_URL, else allow DB_URL override (e.g., sqlite for dev)
DATABASE_URL = (os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "").strip()
if not DATABASE_URL:
    # explicit fallback only if you really want a local DB while developing
    DATABASE_URL = "sqlite:///./dev.db"

# Tuning
ECHO_SQL = os.getenv("DB_ECHO", "0") == "1"
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "5"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # seconds
STATEMENT_TIMEOUT_MS = os.getenv("DB_STATEMENT_TIMEOUT_MS")  # e.g. "60000"
CONNECT_TIMEOUT = os.getenv("DB_CONNECT_TIMEOUT", "5")      # seconds, as string
LOG_URL = os.getenv("DB_LOG_URL", "0") == "1"

# Ensure connect_timeout is present for Postgres URLs (helps fail fast)
try:
    url = make_url(DATABASE_URL)
    if url.get_backend_name().startswith("postgresql"):
        q = dict(url.query)
        q.setdefault("sslmode", "require")
        q.setdefault("connect_timeout", CONNECT_TIMEOUT)
        DATABASE_URL = str(url.set(query=q))
except Exception:
    # leave DATABASE_URL as-is if parsing fails; engine will raise at runtime
    pass

if LOG_URL:
    try:
        print("DB URL in use:", make_url(DATABASE_URL).render_as_string(hide_password=True))
    except Exception:
        print("DB URL in use:", DATABASE_URL.split("@")[0] + "@***")  # coarse hide

# psycopg v3 specific connection args (harmless for psycopg2/sqlite)
connect_args: Dict[str, Any] = {}
if DATABASE_URL.startswith("postgresql+psycopg"):
    opts = ["-c timezone=utc"]
    if STATEMENT_TIMEOUT_MS and STATEMENT_TIMEOUT_MS.isdigit():
        opts.append(f"-c statement_timeout={STATEMENT_TIMEOUT_MS}")
    connect_args["options"] = " ".join(opts)

engine = create_engine(
    DATABASE_URL,
    echo=ECHO_SQL,
    pool_pre_ping=True,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_recycle=POOL_RECYCLE,
    connect_args=connect_args,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False, future=True)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
