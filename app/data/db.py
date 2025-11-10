from __future__ import annotations
import os
from pathlib import Path
from typing import Generator, Any, Dict

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import NullPool

# ---------- Load .env ----------
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)
print(f"[DB] loaded .env from {ENV_PATH}")

# ---------- Read DATABASE_URL ----------
raw_url = os.getenv("DATABASE_URL")
print(f"[DB] raw DATABASE_URL: {raw_url!r}")

# ---------- Fallback to SQLite if missing or invalid ----------
if not raw_url or not raw_url.startswith("postgres"):
    dev_db_path = PROJECT_ROOT.parent / "dev.db"
    raw_url = f"sqlite:///{dev_db_path}"
    print(f"[DB] Using fallback SQLite: {raw_url}")

# ---------- Normalize and configure ----------
engine_kwargs: Dict[str, Any] = dict(pool_pre_ping=True)

try:
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql+psycopg://")

    if raw_url.startswith("postgresql+psycopg2://"):
        raw_url = raw_url.replace("postgresql+psycopg2://", "postgresql+psycopg://")

    if raw_url.startswith("postgresql+psycopg://"):
        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(raw_url)
        query = parse_qs(parsed.query)

        url = URL.create(
            drivername="postgresql+psycopg",
            username=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path.lstrip("/"),
            query={
                "sslmode": query.get("sslmode", ["require"])[0],
                "connect_timeout": query.get("connect_timeout", ["30"])[0],
            },
        )

        if "pooler.supabase.com" in (parsed.hostname or ""):
            engine_kwargs["poolclass"] = NullPool

        print(
            f"[DB] parsed -> user={url.username} host={url.host} port={url.port} db={url.database}"
        )
        engine = create_engine(url, **engine_kwargs)

    elif raw_url.startswith("sqlite:///"):
        engine_kwargs["poolclass"] = NullPool
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine = create_engine(raw_url, **engine_kwargs)

    else:
        raise ValueError(f"Unsupported database backend: {raw_url}")

except Exception as e:
    print(f"[DB] URL parse/normalize failed: {e}")
    engine = create_engine(raw_url, **engine_kwargs)

# ---------- Create session and base ----------
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# ---------- Startup probe ----------
# Commented out to speed up startup
# try:
#     with engine.connect() as conn:
#         try:
#             who = conn.execute(text("select current_user")).scalar()
#             ssl = conn.execute(text("show ssl")).scalar()
#             print(f"[DB] current_user: {who} | ssl={ssl}")
#         except Exception:
#             one = conn.execute(text("select 1")).scalar()
#             print(f"[DB] sqlite probe -> SELECT 1 = {one}")
# except Exception as e:
#     print(f"[DB] startup probe error: {e}")


# ---------- FastAPI dependency ----------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Enable automatic table creation on startup
Base.metadata.create_all(bind=engine)
