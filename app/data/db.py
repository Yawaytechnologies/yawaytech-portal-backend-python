# app/data/db.py
from __future__ import annotations
import os
from collections.abc import Generator
from typing import Any, Dict

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

# Load .env (local dev). On Render, vars come from the dashboard.
load_dotenv()

# Prefer DATABASE_URL, else allow DB_URL override (e.g., sqlite for dev)
DATABASE_URL = (os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "").strip()
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./dev.db"  # local-only fallback

# Tuning
ECHO_SQL = os.getenv("DB_ECHO", "0") == "1"
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "5"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # seconds
STATEMENT_TIMEOUT_MS = os.getenv("DB_STATEMENT_TIMEOUT_MS")  # e.g. "60000"
CONNECT_TIMEOUT = os.getenv("DB_CONNECT_TIMEOUT", "5")  # seconds (string)
LOG_URL = os.getenv("DB_LOG_URL", "0") == "1"

# Parse/normalize URL and ensure ssl + connect_timeout
poolclass = None
connect_args: Dict[str, Any] = {}
is_postgres = False
is_pgbouncer = False

try:
    url = make_url(DATABASE_URL)
    backend = url.get_backend_name()
    is_postgres = backend.startswith("postgresql")

    if is_postgres:
        # Detect PgBouncer (Supabase pooler)
        host = (url.host or "").lower()
        is_pgbouncer = ("pooler.supabase.com" in host) or (url.port == 6543)

        # enforce SSL + connect_timeout
        q = dict(url.query)
        q.setdefault("sslmode", "require")
        q.setdefault("connect_timeout", CONNECT_TIMEOUT)
        url = url.set(query=q)
        DATABASE_URL = str(url)

except Exception:
    # leave DATABASE_URL as-is; engine will raise at runtime if invalid
    pass

if LOG_URL:
    try:
        safe = make_url(DATABASE_URL).render_as_string(hide_password=True)
        print("DB URL in use:", safe)
    except Exception:
        print("DB URL in use:", DATABASE_URL.split("@")[0] + "@***")

# psycopg v3 specific connection args
if DATABASE_URL.startswith("postgresql+psycopg"):
    opts = ["-c timezone=utc"]
    if STATEMENT_TIMEOUT_MS and STATEMENT_TIMEOUT_MS.isdigit():
        opts.append(f"-c statement_timeout={STATEMENT_TIMEOUT_MS}")
    connect_args["options"] = " ".join(opts)

# IMPORTANT: With PgBouncer transaction pooling, disable SQLAlchemy pooling.
if is_pgbouncer:
    poolclass = NullPool
    # SQLAlchemy pool_* args are ignored when poolclass=NullPool.

engine = create_engine(
    DATABASE_URL,
    echo=ECHO_SQL,
    future=True,
    pool_pre_ping=True,
    poolclass=poolclass,  # NullPool for PgBouncer; default otherwise
    pool_size=None if poolclass else POOL_SIZE,
    max_overflow=None if poolclass else MAX_OVERFLOW,
    pool_recycle=None if poolclass else POOL_RECYCLE,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False, future=True
)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
