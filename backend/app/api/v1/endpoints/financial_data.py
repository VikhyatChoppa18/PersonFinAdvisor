"""Financial data endpoints."""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user
from app.db import models
from app.services.financial_data_service import FinancialDataService

router = APIRouter()


@router.get("/stock/{symbol}")
async def get_stock_price(
    symbol: str,
    current_user: models.User = Depends(get_current_user)
):
    """Get real-time stock price."""
    service = FinancialDataService()
    return await service.get_stock_price(symbol.upper())


@router.get("/market-indices")
async def get_market_indices(
    current_user: models.User = Depends(get_current_user)
):
    """Get major market indices."""
    service = FinancialDataService()
    return await service.get_market_indices()


@router.get("/exchange-rates")
async def get_exchange_rates(
    base_currency: str = Query("USD", description="Base currency code"),
    current_user: models.User = Depends(get_current_user)
):
    """Get real-time exchange rates."""
    service = FinancialDataService()
    return await service.get_exchange_rates(base_currency)


@router.get("/crypto")
async def get_crypto_prices(
    symbols: Optional[List[str]] = Query(None, description="Crypto symbols (e.g., BTC-USD)"),
    current_user: models.User = Depends(get_current_user)
):
    """Get real-time cryptocurrency prices."""
    service = FinancialDataService()
    return await service.get_crypto_prices(symbols)


@router.post("/generate-transactions")
async def generate_transactions(
    count: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate realistic transaction data for testing."""
    service = FinancialDataService()
    transactions = await service.generate_realistic_transactions(current_user.id, count)
    
    # Save transactions to database
    saved_transactions = []
    for tx_data in transactions:
        # Check if account exists
        account = db.query(models.Account).filter(
            models.Account.user_id == current_user.id
        ).first()
        
        if not account:
            # Create a default account
            account = models.Account(
                user_id=current_user.id,
                account_id=f"default_{current_user.id}",
                name="Default Account",
                type="checking",
                balance=0.0,
            )
            db.add(account)
            db.commit()
            db.refresh(account)
        
        transaction = models.Transaction(
            user_id=current_user.id,
            account_id=account.id,
            transaction_id=f"gen_{tx_data['date']}_{len(saved_transactions)}",
            amount=tx_data["amount"],
            date=datetime.fromisoformat(tx_data["date"].replace("Z", "+00:00")),
            name=tx_data["name"],
            category=tx_data["category"],
            merchant_name=tx_data.get("merchant_name"),
            is_pending=tx_data.get("is_pending", False),
        )
        db.add(transaction)
        saved_transactions.append(transaction)
    
    db.commit()
    
    return {
        "message": f"Generated {len(saved_transactions)} transactions",
        "count": len(saved_transactions)
    }


@router.get("/market-news")
async def get_market_news(
    limit: int = Query(5, ge=1, le=20),
    current_user: models.User = Depends(get_current_user)
):
    """Get recent financial market news."""
    service = FinancialDataService()
    return await service.get_market_news(limit)
