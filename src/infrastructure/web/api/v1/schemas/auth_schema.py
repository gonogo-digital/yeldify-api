"""
Schemas for JWT authentication.
"""
from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data (payload)."""
    user_id: str
    username: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    user_id: str
    username: Optional[str] = None
    cpf: Optional[str] = None


class UserInDB(BaseModel):
    """User in database (simplified for this example)."""
    user_id: str
    username: str
    cpf: Optional[str] = None
    disabled: bool = False
