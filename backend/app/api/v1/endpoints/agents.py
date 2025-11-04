"""
Agent orchestration endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
import structlog

from app.db.database import get_db
from app.db import models
from app.core.security import get_current_user
from app.schemas.agents import AgentRequest, AgentResponse, FinancialPlanResponse, RiskAssessmentResponse

logger = structlog.get_logger()

router = APIRouter()


@router.post("/financial-planner", response_model=FinancialPlanResponse)
async def get_financial_plan(
    request: AgentRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get financial plan recommendations from Financial Planner Agent."""
    from app.services.agent_service import AgentService
    
    agent_service = AgentService()
    result = await agent_service.run_financial_planner_agent(
        user_id=current_user.id,
        context=request.context or {}
    )
    
    return FinancialPlanResponse(**result)


@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_risk(
    request: AgentRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get risk assessment from Risk Assessment Agent."""
    from app.services.agent_service import AgentService
    from app.services.model_service import ModelService
    
    agent_service = AgentService()
    model_service = ModelService()
    
    # Get user data for risk assessment
    user_data = await agent_service._get_user_financial_data(current_user.id, db)
    
    # Run risk assessment model
    risk_score = await model_service.assess_risk(user_data)
    
    # Get agent recommendations
    result = await agent_service.run_risk_assessment_agent(
        user_id=current_user.id,
        risk_score=risk_score,
        context=request.context or {}
    )
    
    return RiskAssessmentResponse(**result, risk_score=risk_score)


@router.post("/learning-motivation")
async def get_motivation(
    request: AgentRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get motivational content from Learning & Motivation Agent."""
    from app.services.agent_service import AgentService
    
    try:
        logger.info("Getting motivation", user_id=current_user.id)
        agent_service = AgentService()
        result = await agent_service.run_learning_agent(
            user_id=current_user.id,
            context=request.context or {}
        )
        logger.info("Successfully got motivation", user_id=current_user.id)
        return result
    except Exception as e:
        logger.error("Learning Agent error", error=str(e), exc_info=True)
        # Return fallback with real user data instead of generic message
        try:
            from app.services.agent_service import AgentService
            agent_service = AgentService()
            financial_data = await agent_service._get_user_financial_data(current_user.id, db)
            goals = db.query(models.Goal).filter(models.Goal.user_id == current_user.id).all()
            
            # Build personalized fallback based on actual user data
            savings_rate = financial_data.get('savings_rate', 0)
            monthly_income = financial_data.get('monthly_income', 0)
            goals_count = len(goals)
            
            quote = "The best time to plant a tree was 20 years ago. The second best time is now."
            tip = "Automate your savings by setting up automatic transfers to a savings account each month."
            
            # Personalize based on user's actual data
            if savings_rate < 20:
                tip = f"With your current savings rate of {savings_rate:.1f}%, aim to save at least ${monthly_income * 0.20:,.2f} per month (20% of ${monthly_income:,.2f} income)."
            elif savings_rate >= 20:
                quote = "You're doing great! Consistent saving is the foundation of financial freedom."
                tip = "Continue maintaining your excellent savings rate and consider investing surplus funds."
            
            if goals_count > 0:
                progress_insights = [
                    f"You're working on {goals_count} financial goal{'s' if goals_count > 1 else ''}! Keep up the momentum.",
                    "Track your progress regularly to stay motivated."
                ]
            else:
                progress_insights = [
                    "You're tracking your finances! Consider setting a financial goal to stay motivated.",
                    "Start with a small goal and build from there."
                ]
            
            return {
                "quote": quote,
                "tip": tip,
                "achievement_message": f"Great job maintaining a {savings_rate:.1f}% savings rate!" if savings_rate >= 15 else None,
                "progress_insights": progress_insights
            }
        except Exception as data_err:
            logger.error("Error getting user data for motivation fallback", error=str(data_err))
            # Last resort generic fallback
            return {
                "quote": "The best time to plant a tree was 20 years ago. The second best time is now.",
                "tip": "Automate your savings by setting up automatic transfers to a savings account each month.",
                "achievement_message": None,
                "progress_insights": [
                    "You're making progress on your financial goals!",
                    "Keep tracking your expenses to stay on budget."
                ]
            }


@router.post("/generate-alerts")
async def generate_alerts(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger notification agent to generate alerts."""
    from app.services.agent_service import AgentService
    
    agent_service = AgentService()
    alerts = await agent_service.run_notification_agent(
        user_id=current_user.id,
        db=db
    )
    
    return {"alerts_generated": len(alerts), "alerts": alerts}


@router.get("/financial-health")
async def get_financial_health(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get financial health score and analysis."""
    from app.services.personal_finance_advisor import PersonalFinanceAdvisor
    
    try:
        logger.info("Fetching financial health score", user_id=current_user.id)
        advisor = PersonalFinanceAdvisor()
        health_data = await advisor.get_financial_health_score(
            user_id=current_user.id,
            db=db
        )
        logger.info("Successfully fetched financial health score", user_id=current_user.id)
        return health_data
    except Exception as e:
        logger.error("Error in get_financial_health", error=str(e), exc_info=True)
        # Return fallback health data instead of raising error
        # This ensures CORS headers are sent and frontend always gets data
        fallback_data = {
            "score": 70,
            "health_status": "Good",
            "issues": [],
            "recommendations": [
                "Continue tracking your expenses",
                "Aim for 20% savings rate",
                "Build 3-6 months emergency fund"
            ],
            "financial_data": {}
        }
        logger.info("Returning fallback financial health data", user_id=current_user.id)
        return fallback_data


@router.get("/optimize-spending")
async def optimize_spending(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get spending optimization recommendations."""
    from app.services.personal_finance_advisor import PersonalFinanceAdvisor
    
    try:
        logger.info("Fetching optimization recommendations", user_id=current_user.id)
        advisor = PersonalFinanceAdvisor()
        recommendations = await advisor.optimize_spending(
            user_id=current_user.id,
            db=db
        )
        logger.info("Successfully fetched optimization recommendations", user_id=current_user.id)
        return recommendations
    except Exception as e:
        logger.error("Error in optimize_spending", error=str(e), exc_info=True)
        # Return fallback recommendations instead of raising error
        # This ensures CORS headers are sent and frontend always gets data
        # Get actual financial data for fallback
        try:
            from app.services.personal_finance_advisor import PersonalFinanceAdvisor
            advisor = PersonalFinanceAdvisor()
            financial_data = await advisor._get_user_financial_data(current_user.id, db)
            market_context = await advisor.market_service.get_comprehensive_market_context()
            
            # Build data-driven fallback
            top_category = list(financial_data.get('top_spending_categories', {}).keys())[0] if financial_data.get('top_spending_categories') else None
            top_amount = list(financial_data.get('top_spending_categories', {}).values())[0] if financial_data.get('top_spending_categories') else 0
            savings_rate = financial_data.get('savings_rate', 0)
            monthly_income = financial_data.get('monthly_income', 0)
            interest_rate = market_context.get('economic', {}).get('treasury_10y', 0) or 0
            
            fallback_data = {
                "spending_optimization": [
                    f"Review your {top_category} category where you're spending ${top_amount:,.2f}" if top_category else "Review top spending categories",
                    "Consider meal planning to reduce food expenses",
                    "Cancel unused subscriptions",
                    "Use cashback rewards for purchases",
                    "Negotiate better rates on bills and services"
                ],
                "savings_opportunities": [
                    f"Automate savings transfers (target: ${monthly_income * 0.20:,.2f}/month for 20% savings rate)",
                    f"Consider high-yield savings accounts (current rates ~{interest_rate:.2f}%)" if interest_rate > 0 else "Consider high-yield savings accounts",
                    "Reduce dining out expenses",
                    "Shop during sales and use coupons",
                ],
                "priority_actions": [
                    f"Address budget overshoots in: {', '.join(financial_data.get('budget_overshoots', []))}" if financial_data.get('budget_overshoots') else "Review your budgets",
                    "Set up automatic savings",
                    "Review and cancel unnecessary subscriptions",
                    "Track expenses daily"
                ],
                "budget_adjustments": {
                    "increase": ["Emergency fund allocation"] if market_context.get('economic', {}).get('yield_curve_inverted') else [],
                    "decrease": list(financial_data.get('top_spending_categories', {}).keys())[:2] if financial_data.get('top_spending_categories') else []
                },
                "financial_health_tips": [
                    f"Increase savings rate from {savings_rate:.1f}% to 20%",
                    f"Build 3-6 months emergency fund (target: ${financial_data.get('monthly_expenses', 0) * 6:,.2f})",
                    "Track expenses daily",
                    "Review budgets weekly"
                ],
                "risk_factors": [
                    f"High market volatility (VIX: {market_context.get('market', {}).get('vix', 0):.2f})" if market_context.get('market', {}).get('vix', 0) > 20 else None,
                    "Yield curve inversion suggests recession risk" if market_context.get('economic', {}).get('yield_curve_inverted') else None
                ],
                "positive_highlights": [
                    "You're tracking your finances",
                    "You have financial goals set"
                ] if financial_data.get('goals_count', 0) > 0 else ["You're tracking your finances"]
            }
            # Remove None values
            fallback_data["risk_factors"] = [r for r in fallback_data["risk_factors"] if r is not None]
        except Exception as data_err:
            logger.error("Error getting financial data for fallback", error=str(data_err))
            # Last resort - but still try to use market data
            fallback_data = {
                "spending_optimization": [
                    "Review top spending categories and identify areas to cut back",
                    "Consider meal planning to reduce food expenses",
                    "Cancel unused subscriptions"
                ],
                "savings_opportunities": [
                    "Automate savings transfers",
                    "Consider high-yield savings accounts",
                    "Reduce dining out expenses"
                ],
                "priority_actions": [
                    "Set up automatic savings",
                    "Review and cancel unnecessary subscriptions",
                    "Track expenses daily"
                ],
                "budget_adjustments": {"increase": [], "decrease": []},
                "financial_health_tips": [
                    "Aim for 20% savings rate",
                    "Build 3-6 months emergency fund",
                    "Track expenses daily"
                ],
                "risk_factors": [],
                "positive_highlights": ["You're tracking your finances"]
            }
        logger.info("Returning fallback recommendations", user_id=current_user.id)
        return fallback_data


@router.post("/financial-advice")
async def get_financial_advice(
    question: str = Query(..., description="Financial question to ask the advisor"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized financial advice."""
    from app.services.personal_finance_advisor import PersonalFinanceAdvisor
    
    try:
        logger.info("Getting financial advice", user_id=current_user.id, question=question[:50])
        advisor = PersonalFinanceAdvisor()
        advice = await advisor.get_financial_advice(
            user_id=current_user.id,
            question=question,
            db=db
        )
        logger.info("Successfully got financial advice", user_id=current_user.id)
        return advice
    except Exception as e:
        logger.error("Error in get_financial_advice endpoint", error=str(e), exc_info=True)
        # The service's get_financial_advice method has its own exception handler
        # that provides intelligent fallback responses based on question type.
        # If we get here, it means an exception occurred before the service method
        # could use its fallback. Let's try to get a smart fallback anyway.
        try:
            from app.services.personal_finance_advisor import PersonalFinanceAdvisor
            from app.services.market_economic_service import MarketEconomicService
            
            advisor = PersonalFinanceAdvisor()
            market_service = MarketEconomicService()
            market_context = await market_service.get_comprehensive_market_context()
            market_summary = ", ".join(market_context.get('summary', [])) if market_context.get('summary') else "moderate market conditions"
            interest_rate = market_context.get('economic', {}).get('treasury_10y', 0) or 0
            inflation = market_context.get('inflation', {}).get('inflation_expectation', 'moderate')
            
            question_lower = question.lower()
            
            # Provide intelligent fallback based on question type
            if "save" in question_lower or "saving" in question_lower:
                answer = f"Based on your financial situation and current market conditions ({market_summary}), I recommend: 1) Automate savings transfers, 2) Reduce dining out expenses, 3) Review and cancel unused subscriptions. With current interest rates at {interest_rate:.2f}% and inflation at {inflation} levels, start by setting aside at least 20% of your income for savings. Consider high-yield savings accounts for better returns."
            elif "budget" in question_lower:
                answer = f"To improve your budgeting in the current economic environment: 1) Track all expenses daily (especially important with {inflation} inflation), 2) Review budgets weekly, 3) Adjust budgets based on actual spending. Focus on categories where you're overspending. Given current market conditions, consider allocating more to necessities."
            elif "debt" in question_lower:
                answer = f"To pay off debt faster in the current environment: 1) Prioritize high-interest debt (especially important with interest rates at {interest_rate:.2f}%), 2) Consider debt consolidation if rates are favorable, 3) Increase monthly payments. The debt snowball or avalanche method can help. Lock in fixed rates if possible."
            elif "invest" in question_lower or "investment" in question_lower or "stock" in question_lower:
                # Try to get stock recommendations
                stock_recommendations_for_fallback = []
                try:
                    from app.services.stock_recommendation_service import StockRecommendationService
                    from app.core.config import settings
                    stock_service = StockRecommendationService(alpha_vantage_api_key=settings.ALPHA_VANTAGE_API_KEY)
                    stock_recommendations_for_fallback = await stock_service.get_recommended_stocks(
                        market_context=market_context,
                        risk_tolerance="moderate"
                    )
                except Exception as stock_err:
                    logger.error("Error getting stock recommendations in endpoint fallback", error=str(stock_err))
                
                if stock_recommendations_for_fallback:
                    top_stocks = stock_recommendations_for_fallback[:5]
                    stock_list = "\n".join([
                        f"- {s['symbol']} ({s.get('name', s['symbol'])}): {s.get('recommendation', 'HOLD')} at ${s.get('current_price', 0):.2f} - {', '.join(s.get('reasons', [])[:2])}"
                        for s in top_stocks
                    ])
                    answer = f"Based on current market conditions ({market_summary}), here are my stock recommendations:\n\n{stock_list}\n\nConsider your risk tolerance and diversify your portfolio. Always do your own research before investing."
                else:
                    market_sentiment = market_context.get('market', {}).get('sentiment', 'neutral')
                    vix_value = market_context.get('market', {}).get('vix') or 0
                    volatility = 'high' if vix_value > 20 else 'low' if vix_value < 15 else 'moderate'
                    answer = f"Before investing in the current {market_sentiment} market with {volatility} volatility: 1) Build an emergency fund (3-6 months expenses), 2) Pay off high-interest debt, 3) Start with low-risk investments using dollar-cost averaging. Diversification is key. Given current market conditions, consider gradual entry rather than lump-sum investments."
            else:
                answer = f"Based on your financial data and current market conditions ({market_summary}), I recommend: 1) Track expenses regularly, 2) Build an emergency fund (especially important in current economic environment), 3) Set clear financial goals. Current interest rates are {interest_rate:.2f}% and inflation is {inflation}. Would you like more specific advice on any area?"
            
            result = {
                "answer": answer,
                "recommendations": [
                    "Review your financial goals regularly",
                    "Track expenses daily",
                    "Build emergency fund first"
                ],
                "considerations": [
                    "Your current savings rate",
                    "Budget overshoots",
                    "Goal progress"
                ],
                "next_steps": [
                    "Set up automatic savings",
                    "Review budgets weekly",
                    "Track all expenses"
                ]
            }
            
            # Add stock recommendations for stock/investment questions
            if ("stock" in question_lower or "invest" in question_lower or "investment" in question_lower) and 'stock_recommendations_for_fallback' in locals():
                if stock_recommendations_for_fallback:
                    result["stock_recommendations"] = stock_recommendations_for_fallback[:8]
            
            return result
        except Exception as fallback_error:
            logger.error("Error in fallback advice generation", error=str(fallback_error))
            # Last resort generic fallback
            return {
                "answer": f"Thank you for your question: '{question}'. I'm currently experiencing technical difficulties. Please try again in a moment, or contact support for immediate assistance.",
                "recommendations": [
                    "Review your budget regularly",
                    "Track all expenses",
                    "Set up automatic savings"
                ],
                "next_steps": [
                    "Try asking your question again",
                    "Check your financial dashboard",
                    "Review your budget and goals"
                ]
            }

