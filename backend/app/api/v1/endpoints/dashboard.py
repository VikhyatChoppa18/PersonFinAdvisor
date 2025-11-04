"""
Dashboard endpoints for aggregated data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List

from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user
from app.schemas.dashboard import DashboardResponse, BudgetSummary, GoalSummary, TransactionSummary

router = APIRouter()


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard data with aggregated financial information."""
    # Get account balances
    accounts = db.query(models.Account).filter(
        models.Account.user_id == current_user.id,
        models.Account.is_active == True
    ).all()
    
    total_balance = sum(account.balance for account in accounts)
    
    # Get current month transactions
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Query transactions from current month
    monthly_transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id,
        models.Transaction.date >= start_of_month,
        models.Transaction.is_pending == False
    ).all()
    
    # Handle timezone-aware datetimes if needed
    if monthly_transactions and monthly_transactions[0].date.tzinfo:
        # If transactions are timezone-aware, make start_of_month timezone-aware too
        from datetime import timezone
        start_of_month = start_of_month.replace(tzinfo=timezone.utc)
        # Re-query if needed, or filter in Python
        monthly_transactions = [t for t in monthly_transactions if t.date >= start_of_month]
    
    total_income = sum(t.amount for t in monthly_transactions if t.amount > 0)
    total_expenses = abs(sum(t.amount for t in monthly_transactions if t.amount < 0))
    
    # If no income in current month (or very little data), use last 30 days as fallback
    if total_income == 0 or len(monthly_transactions) < 5:
        thirty_days_ago = now - timedelta(days=30)
        recent_transactions = db.query(models.Transaction).filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.date >= thirty_days_ago,
            models.Transaction.is_pending == False
        ).all()
        if recent_transactions:
            # Use 30-day data for better representation
            total_income = sum(t.amount for t in recent_transactions if t.amount > 0)
            total_expenses = abs(sum(t.amount for t in recent_transactions if t.amount < 0))
    
    # Get active budgets
    active_budgets = db.query(models.Budget).filter(
        models.Budget.user_id == current_user.id,
        models.Budget.is_active == True
    ).all()
    
    budget_summaries = [
        BudgetSummary(
            id=budget.id,
            category=budget.category,
            amount=budget.amount,
            current_spent=budget.current_spent,
            percentage=(budget.current_spent / budget.amount * 100) if budget.amount > 0 else 0
        )
        for budget in active_budgets
    ]
    
    # Get active goals
    active_goals = db.query(models.Goal).filter(
        models.Goal.user_id == current_user.id,
        models.Goal.is_active == True
    ).all()
    
    goal_summaries = [
        GoalSummary(
            id=goal.id,
            name=goal.name,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            percentage=(goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0,
            target_date=goal.target_date
        )
        for goal in active_goals
    ]
    
    # Get recent transactions
    recent_transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    ).order_by(models.Transaction.date.desc()).limit(10).all()
    
    transaction_summaries = [
        TransactionSummary(
            id=transaction.id,
            name=transaction.name,
            amount=transaction.amount,
            category=transaction.category,
            date=transaction.date
        )
        for transaction in recent_transactions
    ]
    
    # Get unread alerts
    unread_alerts = db.query(models.Alert).filter(
        models.Alert.user_id == current_user.id,
        models.Alert.is_read == False
    ).count()
    
    return DashboardResponse(
        total_balance=total_balance,
        total_income=total_income,
        total_expenses=total_expenses,
        net_income=total_income - total_expenses,
        budgets=budget_summaries,
        goals=goal_summaries,
        recent_transactions=transaction_summaries,
        unread_alerts=unread_alerts
    )

