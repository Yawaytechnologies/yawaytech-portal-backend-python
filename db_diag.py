#!/usr/bin/env python3
"""
db_diag.py — Robust database connectivity diagnostic (Postgres/SQLite).
- Loads .env (DATABASE_URL) unless an explicit URL is passed as argv[1]
- Prints parsed connection info with password masked
- For Postgres: forces sslmode=require + connect_timeout and sets statement_timeout
- Runs: SELECT current_user, SHOW server_version, SHOW ssl
- Exits 0 on success, 1 on failure
"""

from __future__ import annotations
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url, URL


def load_url_from_env_or_argv() -> str:
    load_dotenv()
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip()
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        print("ERROR: DATABASE_URL not set and no URL argument provided.")
        sys.exit(1)
    return url


def mask_url(u: URL) -> str:
    # Mask password and compress username a bit
    password = u.password or ""
    user = u.username or ""
    masked_pw = "***" if password else ""
    short_user = (user[:4] + "…") if user and len(user) > 8 else user
    # Rebuild a safe display string
    host = u.host or ""
    port = f":{u.port}" if u.port else ""
    db = f"/{u.database}" if u.database else ""
    return f"{u.drivername}://{short_user}:{masked_pw}@{host}{port}{db}"


def build_engine(url_str: str):
    url = make_url(url_str)

    # Normalize Postgres driver name: prefer psycopg2
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+psycopg2")

    # Common pool tuning
    pool_kwargs = dict(pool_size=5, max_overflow=5, pool_recycle=1800)

    if url.drivername.startswith("postgresql"):
        # Enforce SSL & timeouts. Avoid unknown params like "pgbouncer=true".
        q = dict(url.query)
        q.pop("pgbouncer", None)  # remove invalid option for psycopg/libpq
        q.setdefault("sslmode", "require")
        q.setdefault("connect_timeout", "30")
        url = url.set(query=q)

        connect_args = {
            "sslmode": q["sslmode"],
            "connect_timeout": int(q["connect_timeout"]),
        }
        return create_engine(url, connect_args=connect_args, **pool_kwargs), url

    if url.drivername.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False}), url

    # Other drivers as-is
    return create_engine(url, **pool_kwargs), url


def main():
    raw_url = load_url_from_env_or_argv()
    try:
        engine, normalized_url = build_engine(raw_url)
        print("Connecting with:", mask_url(normalized_url))

        with engine.connect() as conn:
            # For Postgres: set statement_timeout (safe no-op for sqlite)
            try:
                conn.execute(text("SET statement_timeout = 60000"))
            except Exception:
                pass

            # Run basic probes
            one = conn.execute(text("SELECT 1")).scalar_one()
            print("Basic SELECT 1 =>", one)

            # Try Postgres-specific diagnostics
            tried_pg = False
            try:
                who = conn.execute(text("SELECT current_user")).scalar_one()
                tried_pg = True
                print("current_user       :", who)
            except Exception:
                pass

            try:
                ver = conn.execute(text("SHOW server_version")).scalar_one()
                tried_pg = True
                print("server_version     :", ver)
            except Exception:
                pass

            try:
                ssl = conn.execute(text("SHOW ssl")).scalar_one()
                tried_pg = True
                print("ssl                :", ssl)
            except Exception:
                if tried_pg:
                    print("ssl                : (SHOW ssl unsupported)")

            # Try to see which address answered (Postgres)
            try:
                addr = conn.execute(text("SELECT inet_server_addr()")).scalar()
                if addr:
                    print("inet_server_addr   :", addr)
            except Exception:
                pass

        print("✅ Database connection test PASSED.")
        sys.exit(0)

    except Exception as e:
        print("❌ Database connection test FAILED:")
        print(repr(e))
        # Helpful hints for common cases
        if "password authentication failed for user" in str(e):
            print("\nHint: The server thinks your username/password is wrong.")
            print("- Ensure username includes the full suffix (e.g., postgres.xxxxxx)")
            print("- Re-copy the password from your provider dashboard")
            print("- Check if env vars like PGUSER/PGPASSWORD are overriding")
        if "Connection timed out" in str(e) or "timed out" in str(e):
            print("\nHint: Network may block the port you’re using.")
            print("- Supabase pooler uses 6543; try direct 5432 if available")
            print("- Try another network (mobile hotspot) to confirm")
            print("- In Windows: Test-NetConnection <host> -Port <port>")
        sys.exit(1)


if __name__ == "__main__":
    main()
