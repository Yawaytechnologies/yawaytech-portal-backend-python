from pydantic import BaseModel, Field


class AdminLogin(BaseModel):
    admin_id: str = Field(..., min_length=1, max_length=80)
    password: str = Field(..., min_length=6)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BootstrapCreate(BaseModel):
    admin_id: str
    password: str
    bootstrap_token: str
