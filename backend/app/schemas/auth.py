"""Authentication schemas."""
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    """User creation schema."""
    email: EmailStr
    password: str
    full_name: str | None = None


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str

