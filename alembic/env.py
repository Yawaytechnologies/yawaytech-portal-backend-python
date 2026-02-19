from __future__ import annotations

import os
from logging.config import fileConfig
from typing import Literal

from alembic import context  # type: ignore[attr-defined]
from sqlalchemy import engine_from_config, pool
from sqlalchemy.sql.schema import SchemaItem

# Alembic Config object, provides access to .ini values
config = context.config

# Configure Python logging via alembic.ini if present
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- target metadata ---------------------------------------------------------
# Import your SQLAlchemy Base here so autogenerate works.
try:
    from app.data.db import Base

    target_metadata = Base.metadata  # type: ignore[attr-defined]
except Exception as e:
    print(f"⚠️ Warning: Could not import Base metadata: {e}")
    target_metadata = None  # type: ignore[assignment]


# --- helpers -----------------------------------------------------------------
def _get_db_url() -> str:
    return (
        os.getenv("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
        or (_ for _ in ()).throw(RuntimeError("Set DATABASE_URL or sqlalchemy.url in alembic.ini"))
    )


def _include_object(
    obj: "SchemaItem",
    name: str | None,
    type_: Literal[
        "schema", "table", "column", "index", "unique_constraint", "foreign_key_constraint"
    ],
    reflected: bool,
    compare_to: "SchemaItem | None",
) -> bool:
    # Optional: Protect against accidental table drops when a model import is missing
    return True


# --- offline / online run modes ----------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection)."""
    url: str = _get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=_include_object,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (actual DB connection)."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _get_db_url()

    print("🔌 [Alembic] Attempting to connect to the database...")

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    try:
        with connectable.connect() as connection:
            print("✅ [Alembic] Successfully connected to the database.")
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_object=_include_object,
                compare_type=True,
                compare_server_default=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    except Exception as e:
        print(f"❌ [Alembic] Failed to connect: {e}")
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
