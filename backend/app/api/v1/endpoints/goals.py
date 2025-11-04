"""Goal endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user
from app.schemas.goals import GoalResponse, GoalCreate, GoalUpdate

router = APIRouter()


@router.get("/", response_model=List[GoalResponse])
async def get_goals(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user goals."""
    goals = db.query(models.Goal).filter(
        models.Goal.user_id == current_user.id
    ).all()
    return goals


@router.post("/", response_model=GoalResponse, status_code=201)
async def create_goal(
    goal_data: GoalCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new goal."""
    goal = models.Goal(
        user_id=current_user.id,
        **goal_data.dict()
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    goal_data: GoalUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a goal."""
    goal = db.query(models.Goal).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    for key, value in goal_data.dict(exclude_unset=True).items():
        setattr(goal, key, value)
    
    db.commit()
    db.refresh(goal)
    return goal

