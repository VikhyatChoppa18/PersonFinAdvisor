"""Transaction endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user
from app.schemas.transactions import TransactionResponse

router = APIRouter()


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user transactions with optional filters."""
    query = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    )
    
    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)
    if category:
        query = query.filter(models.Transaction.category == category)
    
    transactions = query.order_by(models.Transaction.date.desc()).limit(limit).all()
    return transactions

