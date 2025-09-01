# app/schemas/user_schemas.py
from typing import Optional, Annotated
from pydantic import BaseModel, EmailStr, ConfigDict, StringConstraints, model_validator

# ---------- Reusable constrained types (Pydantic v2 style) ----------
Name = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=50,
        pattern=r"^[A-Za-z]+$",
    ),
]

Phone = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=10,
        max_length=10,
        pattern=r"^\d{10}$",
    ),
]

Password = Annotated[
    str,
    StringConstraints(
        min_length=8,
        max_length=18,
    ),
]

# ---------- Base ----------
class UserBase(BaseModel):
    first_name: Name
    last_name: Name
    email: EmailStr
    phone: Phone


# ---------- Incoming payloads ----------
class UserCreate(UserBase):
    password: Password
    confirm_password: Password

    @model_validator(mode="after")
    def _passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[Name] = None
    last_name: Optional[Name] = None
    phone: Optional[Phone] = None
    password: Optional[Password] = None
    confirm_password: Optional[Password] = None

    @model_validator(mode="after")
    def _passwords_match_if_provided(self):
        if (self.password or self.confirm_password) and (self.password != self.confirm_password):
            raise ValueError("Passwords do not match")
        return self


# ---------- Outgoing (responses) ----------
class UserOut(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)  # ORM mode in v2


# ---------- Auth DTOs ----------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(Token):
    user: UserOut


# ---------- Back-compat alias used by your service/router ----------
SignUpIn = UserCreate
