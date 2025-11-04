"""Account endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user
from app.schemas.accounts import AccountResponse, AccountCreate

router = APIRouter()


@router.get("/", response_model=List[AccountResponse])
async def get_accounts(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user accounts."""
    accounts = db.query(models.Account).filter(
        models.Account.user_id == current_user.id
    ).all()
    return accounts


@router.post("/", response_model=AccountResponse, status_code=201)
async def create_account(
    account_data: AccountCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new account."""
    account = models.Account(
        user_id=current_user.id,
        **account_data.dict()
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

