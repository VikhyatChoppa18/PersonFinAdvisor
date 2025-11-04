"""Dashboard schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import List


class BudgetSummary(BaseModel):
    """Budget summary schema."""
    id: int
    category: str
    amount: float
    current_spent: float
    percentage: float


class GoalSummary(BaseModel):
    """Goal summary schema."""
    id: int
    name: str
    target_amount: float
    current_amount: float
    percentage: float
    target_date: datetime


class TransactionSummary(BaseModel):
    """Transaction summary schema."""
    id: int
    name: str
    amount: float
    category: str | None
    date: datetime


class DashboardResponse(BaseModel):
    """Dashboard response schema."""
    total_balance: float
    total_income: float
    total_expenses: float
    net_income: float
    budgets: List[BudgetSummary]
    goals: List[GoalSummary]
    recent_transactions: List[TransactionSummary]
    unread_alerts: int

