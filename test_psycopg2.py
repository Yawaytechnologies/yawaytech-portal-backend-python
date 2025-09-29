#!/usr/bin/env python3
"""
Simple test using psycopg2 directly to isolate connection issues.
"""

import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("No DATABASE_URL found in .env")
    exit(1)

# Parse the URL
parsed = urlparse(DATABASE_URL)

conn_params = {
    "host": parsed.hostname,
    "port": parsed.port or 5432,
    "database": parsed.path[1:],  # Remove leading /
    "user": parsed.username,
    "password": parsed.password,
}

print(f"Attempting connection with params: {conn_params}")

try:
    conn = psycopg2.connect(**conn_params)
    print("Direct psycopg2 connection successful!")
    cur = conn.cursor()
    cur.execute("SELECT 1")
    result = cur.fetchone()
    print(f"Test query result: {result[0]}")
    cur.close()
    conn.close()
    print("Test PASSED.")
except Exception as e:
    print(f"Test FAILED: {e}")
