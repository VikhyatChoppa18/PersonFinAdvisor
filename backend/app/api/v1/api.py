"""
Main API router combining all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, accounts, transactions, budgets, goals, agents, dashboard, financial_data, stock_recommendations

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(financial_data.router, prefix="/financial-data", tags=["financial-data"])
api_router.include_router(stock_recommendations.router, prefix="/stocks", tags=["stock-recommendations"])

