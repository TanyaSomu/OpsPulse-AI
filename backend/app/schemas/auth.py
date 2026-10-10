from typing import Optional
from pydantic import BaseModel, Field
from app.models.enums import UserRole

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)

class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=4)
    full_name: str
    role: UserRole = UserRole.RESPONDER
    organization_name: Optional[str] = "OpsPulse Engineering"

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class TokenPayload(BaseModel):
    sub: Optional[str] = None

from app.schemas.user import UserResponse
Token.model_rebuild()
