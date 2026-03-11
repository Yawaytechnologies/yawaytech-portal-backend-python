import os
from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Expenses Tracker")
DB_URL = os.getenv("DB_URL", "sqlite:///./dev.db")


class _Settings(BaseModel):
    TZ_NAME: str = "Asia/Kolkata"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    ADMIN_ID: str = os.getenv("ADMIN_ID", "superadmin")
    ADMIN_PASSWORD_HASH: str | None = os.getenv("ADMIN_PASSWORD_HASH")
    ADMIN_PASSWORD_PLAINTEXT: str | None = os.getenv("ADMIN_PASSWORD", "admin123")

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_PROFILE_BUCKET: str = os.getenv("SUPABASE_PROFILE_BUCKET", "employee-profiles")
    SUPABASE_EVIDENCE_BUCKET: str = os.getenv("SUPABASE_EVIDENCE_BUCKET", "daily_attandance")

    SUPABASE_BUCKET_PUBLIC: bool = os.getenv("SUPABASE_BUCKET_PUBLIC", "false").lower() == "true"
    SIGNED_URL_EXPIRE_SECONDS: int = int(os.getenv("SIGNED_URL_EXPIRE_SECONDS", "3600"))


settings = _Settings()


# Normalize strings afterwards
if settings.ADMIN_PASSWORD_HASH:
    settings.ADMIN_PASSWORD_HASH = settings.ADMIN_PASSWORD_HASH.strip().strip('"').strip("'")
if settings.ADMIN_PASSWORD_PLAINTEXT:
    settings.ADMIN_PASSWORD_PLAINTEXT = settings.ADMIN_PASSWORD_PLAINTEXT.strip()

# Hard guard: catch the pooler mistake early
if "pooler.supabase.com" in settings.SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL is wrong. Use https://<project-ref>.supabase.co (project API URL), not pooler host."
    )
