"""Account schemas."""
from pydantic import BaseModel
from datetime import datetime


class AccountCreate(BaseModel):
    """Account creation schema."""
    account_id: str
    name: str
    type: str
    balance: float = 0.0
    currency: str = "USD"


class AccountResponse(BaseModel):
    """Account response schema."""
    id: int
    account_id: str
    name: str
    type: str
    balance: float
    currency: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

