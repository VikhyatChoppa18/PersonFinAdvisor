"""Goal schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class GoalCreate(BaseModel):
    """Goal creation schema."""
    name: str
    target_amount: float
    target_date: datetime
    goal_type: str


class GoalUpdate(BaseModel):
    """Goal update schema."""
    current_amount: Optional[float] = None
    target_amount: Optional[float] = None
    target_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class GoalResponse(BaseModel):
    """Goal response schema."""
    id: int
    name: str
    target_amount: float
    current_amount: float
    target_date: datetime
    goal_type: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

