# alembic/env.py
from __future__ import annotations
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from app.data.db import Base

# ── Put project root on sys.path ───────────────────────────────────────────────
HERE = os.path.dirname(__file__)  # .../alembic
ROOT = os.path.abspath(os.path.join(HERE, ".."))  # project root (where 'app/' lives)
if ROOT not in sys.path:
    sys.path.append(ROOT)

# (optional) load .env so DATABASE_URL is available
try:
    from dotenv import load_dotenv  # pip install python-dotenv

    load_dotenv()
except Exception:
    pass

# ── Alembic config & logging ──────────────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Core

# Attendance (models inside the feature module)

# Policy (moved out of attendance.py)

# Shifts

# Leave / Permission

# Payroll

# Optional: day override audit
# from app.data.models.attendance_override import AttendanceOverride

target_metadata = Base.metadata


def _get_db_url() -> str:
    return (
        os.getenv("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
        or (_ for _ in ()).throw(RuntimeError("Set DATABASE_URL or sqlalchemy.url in alembic.ini"))
    )


# Avoid accidental DROP TABLE when a model import is missing
def _include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table" and reflected and compare_to is None:
        return False
    return True


# ── DEBUG: print loaded table names (helps verify imports are working) ─────────
def _log_loaded_tables():
    try:
        tables = sorted(target_metadata.tables.keys())
        print(f"[alembic] Loaded tables ({len(tables)}): {tables}")
    except Exception:
        pass


# ── Offline migrations ────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    url = _get_db_url()
    _log_loaded_tables()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=_include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations ─────────────────────────────────────────────────────────
def run_migrations_online() -> None:
    url = _get_db_url()
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        _log_loaded_tables()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=_include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


# ── Entry point ───────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
