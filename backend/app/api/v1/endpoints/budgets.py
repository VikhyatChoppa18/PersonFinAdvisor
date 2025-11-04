"""Budget endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user
from app.schemas.budgets import BudgetResponse, BudgetCreate, BudgetUpdate

router = APIRouter()


@router.get("/", response_model=List[BudgetResponse])
async def get_budgets(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user budgets."""
    budgets = db.query(models.Budget).filter(
        models.Budget.user_id == current_user.id
    ).all()
    return budgets


@router.post("/", response_model=BudgetResponse, status_code=201)
async def create_budget(
    budget_data: BudgetCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new budget."""
    budget = models.Budget(
        user_id=current_user.id,
        **budget_data.dict()
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a budget."""
    budget = db.query(models.Budget).filter(
        models.Budget.id == budget_id,
        models.Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    for key, value in budget_data.dict(exclude_unset=True).items():
        setattr(budget, key, value)
    
    db.commit()
    db.refresh(budget)
    return budget

