# app/data/db.py
from __future__ import annotations

import os
from typing import Any, Dict, Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

# --------------------------------------------------------------------------
# Load environment
# (On Render, env vars come from the dashboard; locally we use .env.)
# --------------------------------------------------------------------------
load_dotenv()

# Prefer DATABASE_URL, else allow DB_URL (e.g., sqlite for dev)
DATABASE_URL = (os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "").strip()
if not DATABASE_URL:
    # Local-only fallback so dev still runs without a Postgres URL
    DATABASE_URL = "sqlite:///./dev.db"

# --------------------------------------------------------------------------
# Tuning knobs (all optional)
# --------------------------------------------------------------------------
ECHO_SQL = os.getenv("DB_ECHO", "0") == "1"
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "5"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # seconds
STATEMENT_TIMEOUT_MS = os.getenv("DB_STATEMENT_TIMEOUT_MS")  # e.g. "60000"
CONNECT_TIMEOUT = os.getenv("DB_CONNECT_TIMEOUT", "5")  # seconds (string)
LOG_URL = os.getenv("DB_LOG_URL", "0") == "1"

# --------------------------------------------------------------------------
# Normalize URL, detect PgBouncer, set SSL + connect_timeout
# --------------------------------------------------------------------------
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

        # Enforce SSL + connect_timeout
        q = dict(url.query)
        q.setdefault("sslmode", "require")
        q.setdefault("connect_timeout", CONNECT_TIMEOUT)
        url = url.set(query=q)
        DATABASE_URL = str(url)

except Exception:
    # Leave DATABASE_URL as-is; engine will raise at runtime if invalid
    pass

if LOG_URL:
    try:
        safe = make_url(DATABASE_URL).render_as_string(hide_password=True)
        print("DB URL in use:", safe)
    except Exception:
        print("DB URL in use:", DATABASE_URL.split("@")[0] + "@***")

# psycopg v3 specific connection args (harmless if not psycopg v3)
if DATABASE_URL.startswith("postgresql+psycopg"):
    opts = ["-c timezone=utc"]
    if STATEMENT_TIMEOUT_MS and STATEMENT_TIMEOUT_MS.isdigit():
        opts.append(f"-c statement_timeout={STATEMENT_TIMEOUT_MS}")
    connect_args["options"] = " ".join(opts)

# --------------------------------------------------------------------------
# Create engine
# IMPORTANT: With PgBouncer (6543), disable SQLAlchemy pooling (NullPool).
#            With direct Postgres (e.g., 5432), use normal pooling.
# --------------------------------------------------------------------------
engine_kwargs: Dict[str, Any] = dict(
    echo=ECHO_SQL,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)

if is_pgbouncer:
    # PgBouncer → no ORM-side pooling
    engine_kwargs["poolclass"] = NullPool
else:
    # Direct DB → normal pooling is fine
    engine_kwargs.update(
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_recycle=POOL_RECYCLE,
    )

engine = create_engine(DATABASE_URL, **engine_kwargs)

# --------------------------------------------------------------------------
# Session / Base
# --------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)
Base = declarative_base()


# --------------------------------------------------------------------------
# Dependency for FastAPI routes
# --------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
