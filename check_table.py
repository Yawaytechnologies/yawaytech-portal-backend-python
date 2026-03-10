#!/usr/bin/env python3
from app.data.db import engine
from sqlalchemy import text


def check_table_exists():
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'attendance_evidences';"
                )
            )
            exists = bool(result.fetchone())
            print(f"attendance_evidences table exists: {exists}")
            return exists
    except Exception as e:
        print(f"Error checking table: {e}")
        return False


if __name__ == "__main__":
    check_table_exists()
