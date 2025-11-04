"""Agent schemas."""
from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class AgentRequest(BaseModel):
    """Agent request schema."""
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Base agent response schema."""
    agent_type: str
    result: Dict[str, Any]
    execution_time_ms: int


class BudgetRecommendation(BaseModel):
    """Budget recommendation schema."""
    category: str
    recommended_amount: float
    reasoning: str


class FinancialPlanResponse(BaseModel):
    """Financial plan response schema."""
    recommendations: List[BudgetRecommendation]
    total_recommended_budget: float
    savings_suggestion: float
    insights: List[str]


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response schema."""
    risk_score: float  # 0-1 scale
    risk_level: str  # low, medium, high
    recommendations: List[str]
    suitable_investment_types: List[str]
    warnings: List[str]


class MotivationResponse(BaseModel):
    """Motivation response schema."""
    quote: str
    tip: str
    achievement_message: Optional[str] = None
    progress_insights: List[str]

