#!/usr/bin/env python3
from app.data.db import engine
from sqlalchemy import text


def check_table():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'attendance_evidences'
                );
            """)).fetchone()
            print(f"attendance_evidences table exists: {result[0]}")
    except Exception as e:
        print(f"Error checking table: {e}")


if __name__ == "__main__":
    check_table()
