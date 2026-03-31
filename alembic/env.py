from __future__ import annotations

import os
from logging.config import fileConfig
from typing import Literal
from urllib.parse import parse_qs, urlparse

from alembic import context  # type: ignore[attr-defined]
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL
from sqlalchemy.sql.schema import SchemaItem

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

try:
    from app.data.db import Base

    target_metadata = Base.metadata  # type: ignore[attr-defined]
except Exception as exc:
    print(f"Warning: Could not import Base metadata: {exc}")
    target_metadata = None  # type: ignore[assignment]


def _get_db_url() -> str:
    raw_url = (
        os.getenv("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
        or (_ for _ in ()).throw(RuntimeError("Set DATABASE_URL or sqlalchemy.url in alembic.ini"))
    )

    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif raw_url.startswith("postgresql+psycopg2://"):
        raw_url = raw_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)

    if raw_url.startswith("postgresql+psycopg://"):
        parsed = urlparse(raw_url)
        query = parse_qs(parsed.query)
        normalized = URL.create(
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
        return normalized.render_as_string(hide_password=False)

    return raw_url


def _include_object(
    obj: "SchemaItem",
    name: str | None,
    type_: Literal[
        "schema", "table", "column", "index", "unique_constraint", "foreign_key_constraint"
    ],
    reflected: bool,
    compare_to: "SchemaItem | None",
) -> bool:
    return True


def run_migrations_offline() -> None:
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
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _get_db_url()

    print("[Alembic] Attempting to connect to the database...")

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    try:
        with connectable.connect() as connection:
            print("[Alembic] Successfully connected to the database.")
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_object=_include_object,
                compare_type=True,
                compare_server_default=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    except Exception as exc:
        print(f"[Alembic] Failed to connect: {exc}")
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
