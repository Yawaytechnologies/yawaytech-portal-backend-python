#!/usr/bin/env python3
"""
Simple test using psycopg2 directly to isolate connection issues.
"""

import os
from dotenv import load_dotenv
import psycopg as psycopg2
from urllib.parse import urlparse
import pytest

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    pytest.skip("No DATABASE_URL found in .env", allow_module_level=True)

# Parse the URL
parsed = urlparse(DATABASE_URL)

conn_params = {
    "host": parsed.hostname,
    "port": parsed.port or 5432,
    "database": parsed.path[1:],  # Remove leading /
    "user": parsed.username,
    "password": parsed.password,
}


def test_psycopg2_connection():
    """Test direct psycopg2 connection to the database."""
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        assert result[0] == 1, f"Expected 1, got {result[0]}"
        cur.close()
        conn.close()
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")
