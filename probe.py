# probe.py (place in project root)
import os, psycopg
from dotenv import load_dotenv

# Load .env from this folder
load_dotenv()

u = os.getenv("DB_USER")
p = os.getenv("DB_PASS")
h = os.getenv("DB_HOST")
n = os.getenv("DB_NAME")

print(f"Trying {u}@{h}/" + (n or ""))

# Connect directly (bypasses SQLAlchemy)
conn = psycopg.connect(
    host=h, port=5432, dbname=n, user=u, password=p,
    sslmode="require", connect_timeout=10,
)

with conn.cursor() as cur:
    cur.execute("select current_database(), current_user")
    print("Connected ->", cur.fetchone())

conn.close()
