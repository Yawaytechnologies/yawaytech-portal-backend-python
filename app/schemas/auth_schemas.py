from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SignupResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # If you want to return the user too:
    # user: UserOut
