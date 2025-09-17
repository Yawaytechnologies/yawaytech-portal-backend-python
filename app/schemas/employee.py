from pydantic import BaseModel, Field


class EmployeeLogin(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=9)
    password: str = Field(..., min_length=6)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
