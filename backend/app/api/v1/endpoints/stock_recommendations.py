"""
Stock recommendation endpoints.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user
from app.services.stock_recommendation_service import StockRecommendationService
from app.services.market_economic_service import MarketEconomicService
from app.core.config import settings

router = APIRouter()


@router.get("/recommendations")
async def get_stock_recommendations(
    risk_tolerance: str = Query("moderate", description="Risk tolerance: conservative, moderate, aggressive"),
    investment_amount: Optional[float] = Query(None, description="Investment amount"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get stock recommendations based on current market conditions."""
    try:
        # Get market context
        market_service = MarketEconomicService()
        market_context = await market_service.get_comprehensive_market_context()
        
        # Get stock recommendations
        stock_service = StockRecommendationService(alpha_vantage_api_key=settings.ALPHA_VANTAGE_API_KEY)
        recommendations = await stock_service.get_recommended_stocks(
            market_context=market_context,
            risk_tolerance=risk_tolerance,
            investment_amount=investment_amount
        )
        
        return {
            "recommendations": recommendations,
            "market_context": market_context,
            "risk_tolerance": risk_tolerance,
            "count": len(recommendations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stock recommendations: {str(e)}")


@router.get("/analyze/{symbol}")
async def analyze_stock(
    symbol: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze a specific stock."""
    try:
        stock_service = StockRecommendationService(alpha_vantage_api_key=settings.ALPHA_VANTAGE_API_KEY)
        analysis = await stock_service.analyze_stock(symbol.upper())
        
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing stock: {str(e)}")


@router.get("/screen")
async def screen_stocks(
    sectors: Optional[List[str]] = Query(None, description="Filter by sectors"),
    min_market_cap: Optional[float] = Query(None, description="Minimum market cap"),
    max_pe: Optional[float] = Query(None, description="Maximum P/E ratio"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Screen stocks based on criteria."""
    try:
        # Get market context
        market_service = MarketEconomicService()
        market_context = await market_service.get_comprehensive_market_context()
        
        # Build criteria
        criteria = {}
        if sectors:
            criteria["sectors"] = sectors
        if min_market_cap:
            criteria["min_market_cap"] = min_market_cap
        if max_pe:
            criteria["max_pe"] = max_pe
        
        # Get screened stocks
        stock_service = StockRecommendationService(alpha_vantage_api_key=settings.ALPHA_VANTAGE_API_KEY)
        stocks = await stock_service.get_stock_screener(
            criteria=criteria,
            market_context=market_context
        )
        
        return {
            "stocks": stocks,
            "criteria": criteria,
            "count": len(stocks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error screening stocks: {str(e)}")

