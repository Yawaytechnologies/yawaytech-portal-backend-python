import os
from sqlalchemy.engine import make_url
from dotenv import load_dotenv

load_dotenv(dotenv_path=r"D:\yawaytech-portal-backend\yawaytech-portal-backend-python\.env")

url = os.getenv("DATABASE_URL","").strip()
print("RAW DATABASE_URL:", url)
if not url:
    raise SystemExit("ERROR: no DATABASE_URL loaded")

u = make_url(url)
print("Parsed -> driver:", u.drivername, "| user:", u.username, "| host:", u.host, "| port:", u.port, "| db:", u.database)
