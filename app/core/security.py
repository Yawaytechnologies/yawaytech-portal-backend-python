import os
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGO = "HS256"

def hash_password(raw: str) -> str:
    return pwd_ctx.hash(raw)

def verify_password(raw: str, hashed: str) -> bool:
    return pwd_ctx.verify(raw, hashed)

def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    secret = os.getenv("SECRET_KEY", "dev-secret")
    ttl = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    minutes = expires_minutes or ttl

    to_encode = data.copy()
    to_encode.update({"exp": datetime.now(timezone.utc) + timedelta(minutes=minutes)})
    return jwt.encode(to_encode, secret, algorithm=ALGO)

def decode_token(token: str) -> dict:
    secret = os.getenv("SECRET_KEY", "dev-secret")
    return jwt.decode(token, secret, algorithms=[ALGO])
