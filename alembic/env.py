import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context


# ─── Ensure Alembic can find your app ───────────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ─── Alembic Config ─────────────────────────────────────────────────────────────
config = context.config

# ─── Logging Setup ──────────────────────────────────────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ─── Import your models and metadata ────────────────────────────────────────────
from app.data.db import Base
from app.data.models import (
    add_employee,
    expenses,
    attendance,
    admin,
    dashboard,
)  # 👈 registers all models

target_metadata = Base.metadata


# ─── Offline Migrations ─────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ─── Online Migrations ──────────────────────────────────────────────────────────
def run_migrations_online() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    connectable = create_engine(database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ─── Entry Point ────────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
