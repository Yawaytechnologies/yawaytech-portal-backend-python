#!/usr/bin/env python3
"""
Test script to verify database connection independently of the FastAPI app.
This isolates DB issues from app logic.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment
load_dotenv()

# Import after loading env
from app.data.db import engine, DATABASE_URL

def test_connection():
    """Test basic database connection."""
    try:
        print(f"Testing connection to: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split(':')[2], '***') if '@' in DATABASE_URL else DATABASE_URL}")

        # Try to connect and execute a simple query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"Connection successful! Test query result: {row[0]}")

        print("Database connection test PASSED.")
        return True

    except Exception as e:
        print(f"Database connection test FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
