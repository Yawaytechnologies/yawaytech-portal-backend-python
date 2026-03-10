#!/usr/bin/env python3
from app.data.db import engine
from sqlalchemy import text


def test_table():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM attendance_evidences LIMIT 1;"))
            print("✅ Table exists and is accessible!")
    except Exception as e:
        print(f"❌ Error accessing table: {e}")


if __name__ == "__main__":
    test_table()
