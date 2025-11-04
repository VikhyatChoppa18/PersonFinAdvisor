"""Budget schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BudgetCreate(BaseModel):
    """Budget creation schema."""
    category: str
    amount: float
    period: str
    start_date: datetime
    end_date: datetime


class BudgetUpdate(BaseModel):
    """Budget update schema."""
    amount: Optional[float] = None
    current_spent: Optional[float] = None
    is_active: Optional[bool] = None


class BudgetResponse(BaseModel):
    """Budget response schema."""
    id: int
    category: str
    amount: float
    period: str
    current_spent: float
    start_date: datetime
    end_date: datetime
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

