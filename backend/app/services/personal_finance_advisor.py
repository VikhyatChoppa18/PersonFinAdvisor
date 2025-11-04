"""
Personal Finance Advisor Agent - Optimizes spending and ensures financial health.
"""
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_community.llms import Ollama
import structlog

from app.core.config import settings
from app.db import models
from app.services.market_economic_service import MarketEconomicService
from app.services.stock_recommendation_service import StockRecommendationService

logger = structlog.get_logger()


class PersonalFinanceAdvisor:
    """Personal Finance Advisor Agent for optimizing spending and financial health."""
    
    def __init__(self):
        """Initialize advisor with Ollama LLM and market data service."""
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.5,  # Lower temperature for faster, more focused responses
        )
        self.market_service = MarketEconomicService()
        self.stock_service = StockRecommendationService(alpha_vantage_api_key=settings.ALPHA_VANTAGE_API_KEY)
    
    async def _get_user_financial_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get comprehensive user financial data."""
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return {}
        
        accounts = db.query(models.Account).filter(models.Account.user_id == user_id).all()
        transactions = db.query(models.Transaction).filter(
            models.Transaction.user_id == user_id
        ).limit(200).all()
        budgets = db.query(models.Budget).filter(models.Budget.user_id == user_id).all()
        goals = db.query(models.Goal).filter(models.Goal.user_id == user_id).all()
        
        total_balance = sum(acc.balance for acc in accounts)
        # Get current month/year for filtering transactions
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        # Calculate monthly income and expenses (filter by current month)
        monthly_income = sum(
            t.amount for t in transactions 
            if t.amount > 0 and 
            t.date.month == current_month and 
            t.date.year == current_year
        )
        monthly_expenses = abs(sum(
            t.amount for t in transactions 
            if t.amount < 0 and 
            t.date.month == current_month and 
            t.date.year == current_year
        ))
        
        # Budget analysis
        budget_overshoots = []
        budget_status = []
        for budget in budgets:
            if budget.is_active:
                percentage = (budget.current_spent / budget.amount * 100) if budget.amount > 0 else 0
                status = "over" if percentage > 100 else "on_track" if percentage < 80 else "warning"
                budget_status.append({
                    "category": budget.category,
                    "amount": budget.amount,
                    "spent": budget.current_spent,
                    "percentage": percentage,
                    "status": status
                })
                if percentage > 100:
                    budget_overshoots.append(budget.category)
        
        # Goal progress
        goal_progress = []
        for goal in goals:
            if goal.is_active:
                percentage = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
                # Handle timezone-aware vs naive datetime
                target_date = goal.target_date
                if target_date.tzinfo is not None:
                    now_tz = datetime.now(target_date.tzinfo)
                    days_remaining = (target_date - now_tz).days
                else:
                    now_tz = datetime.now()
                    days_remaining = (target_date.replace(tzinfo=None) - now_tz.replace(tzinfo=None)).days
                goal_progress.append({
                    "name": goal.name,
                    "target": goal.target_amount,
                    "current": goal.current_amount,
                    "percentage": percentage,
                    "days_remaining": days_remaining
                })
        
        # Spending patterns
        category_spending = {}
        for transaction in transactions:
            if transaction.amount < 0:  # Only expenses
                category = transaction.category or "Other"
                if category not in category_spending:
                    category_spending[category] = 0
                category_spending[category] += abs(transaction.amount)
        
        top_spending_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_balance": total_balance,
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "savings_rate": ((monthly_income - monthly_expenses) / monthly_income * 100) if monthly_income > 0 else 0,
            "budget_status": budget_status,
            "budget_overshoots": budget_overshoots,
            "goal_progress": goal_progress,
            "top_spending_categories": dict(top_spending_categories),
            "accounts_count": len(accounts),
            "goals_count": len(goals),
            "active_budgets_count": len([b for b in budgets if b.is_active]),
        }
    
    async def get_financial_health_score(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Calculate overall financial health score."""
        import asyncio
        
        try:
            # Run in executor since _get_user_financial_data uses sync DB queries
            # Add timeout to prevent hanging
            loop = asyncio.get_event_loop()
            financial_data = await asyncio.wait_for(
                loop.run_in_executor(None, self._get_user_financial_data, user_id, db),
                timeout=10.0  # 10 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("Timeout getting user financial data for health score")
            financial_data = {}
        except Exception as e:
            logger.error("Error getting user financial data for health score", error=str(e))
            financial_data = {}
        
        score = 100  # Start with perfect score
        issues = []
        recommendations = []
        
        # Savings rate check
        savings_rate = financial_data.get("savings_rate", 0)
        if savings_rate < 0:
            score -= 30
            issues.append("Spending exceeds income")
            recommendations.append("Reduce expenses immediately")
        elif savings_rate < 10:
            score -= 20
            issues.append("Low savings rate (<10%)")
            recommendations.append("Aim to save at least 20% of income")
        elif savings_rate < 20:
            score -= 10
            issues.append("Savings rate below recommended 20%")
            recommendations.append("Increase savings to 20% of income")
        
        # Budget overshoots
        overshoots = financial_data.get("budget_overshoots", [])
        if overshoots:
            score -= len(overshoots) * 5
            issues.append(f"Budget overshoots in: {', '.join(overshoots)}")
            recommendations.append(f"Review and reduce spending in: {', '.join(overshoots)}")
        
        # Emergency fund check
        total_balance = financial_data.get("total_balance", 0)
        monthly_expenses = financial_data.get("monthly_expenses", 0)
        if monthly_expenses > 0:
            months_emergency_fund = total_balance / monthly_expenses
            if months_emergency_fund < 3:
                score -= 15
                issues.append("Emergency fund below 3 months")
                recommendations.append("Build emergency fund to cover 3-6 months of expenses")
            elif months_emergency_fund < 6:
                score -= 5
                recommendations.append("Consider increasing emergency fund to 6 months")
        
        # Goal progress
        goals = financial_data.get("goal_progress", [])
        behind_goals = [g for g in goals if g.get("percentage", 0) < 50 and g.get("days_remaining", 0) < 90]
        if behind_goals:
            score -= len(behind_goals) * 5
            issues.append(f"Goals behind schedule: {', '.join([g['name'] for g in behind_goals])}")
            recommendations.append("Increase contributions to goals that are behind schedule")
        
        # Score classification
        if score >= 80:
            health_status = "Excellent"
        elif score >= 60:
            health_status = "Good"
        elif score >= 40:
            health_status = "Fair"
        else:
            health_status = "Needs Attention"
        
        return {
            "score": max(0, min(100, score)),
            "health_status": health_status,
            "issues": issues,
            "recommendations": recommendations,
            "financial_data": financial_data
        }
    
    async def optimize_spending(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Provide hyper-personalized spending optimization recommendations based on current market and economic conditions."""
        import asyncio
        
        try:
            # Run in executor since _get_user_financial_data uses sync DB queries
            # Add timeout to prevent hanging
            loop = asyncio.get_event_loop()
            financial_data = await asyncio.wait_for(
                loop.run_in_executor(None, self._get_user_financial_data, user_id, db),
                timeout=10.0  # 10 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("Timeout getting user financial data for optimization")
            financial_data = {}
        except Exception as e:
            logger.error("Error getting user financial data for optimization", error=str(e))
            financial_data = {}
        
        try:
            # Add timeout for market context
            market_context = await asyncio.wait_for(
                self.market_service.get_comprehensive_market_context(),
                timeout=5.0  # 5 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("Timeout getting market context for optimization")
            market_context = {}
        except Exception as e:
            logger.error("Error getting market context for optimization", error=str(e))
            market_context = {}
        
        # Build detailed financial analysis prompt with REAL data
        vix = market_context.get('market', {}).get('vix', 0) or 0
        treasury_10y = market_context.get('economic', {}).get('treasury_10y', 0) or 0
        sp500_change = market_context.get('market', {}).get('sp500', {}).get('change_pct', 0) if market_context.get('market', {}).get('sp500') else 0
        
        # Build strings separately to avoid f-string syntax errors
        market_summary_str = chr(10).join([f"- {item}" for item in market_context.get('summary', [])]) if market_context.get('summary') else "Market data available"
        sp500_perf = f"{sp500_change:.2f}%" if sp500_change else "N/A"
        treasury_yield = f"{treasury_10y:.2f}%" if treasury_10y else 'N/A'
        vix_level = 'High' if vix > 20 else 'Low' if vix < 15 else 'Moderate'
        yield_curve_status = 'Inverted (recession risk)' if market_context.get('economic', {}).get('yield_curve_inverted') else 'Normal'
        inflation_exp = market_context.get('inflation', {}).get('inflation_expectation', 'moderate')
        
        # Build budget status string
        if financial_data.get('budget_status'):
            budget_status_lines = []
            for b in financial_data.get('budget_status', []):
                budget_status_lines.append(f"- {b.get('category', 'Unknown')}: ${b.get('spent', 0):,.2f} spent of ${b.get('amount', 0):,.2f} budget ({b.get('percentage', 0):.1f}% used) - Status: {b.get('status', 'unknown')}")
            budget_status_str = chr(10).join(budget_status_lines)
        else:
            budget_status_str = "No active budgets"
        
        # Build spending categories string
        if financial_data.get('top_spending_categories'):
            spending_cat_lines = []
            for cat, amount in list(financial_data.get('top_spending_categories', {}).items())[:5]:
                spending_cat_lines.append(f"- {cat}: ${amount:,.2f}")
            spending_cat_str = chr(10).join(spending_cat_lines)
        else:
            spending_cat_str = "No spending data"
        
        # Build goal progress string
        if financial_data.get('goal_progress'):
            goal_progress_lines = []
            for g in financial_data.get('goal_progress', []):
                goal_progress_lines.append(f"- {g.get('name', 'Unknown')}: ${g.get('current', 0):,.2f} / ${g.get('target', 0):,.2f} ({g.get('percentage', 0):.1f}% complete) - {g.get('days_remaining', 0)} days remaining")
            goal_progress_str = chr(10).join(goal_progress_lines)
        else:
            goal_progress_str = "No active goals"
        
        # Build budget overshoots string
        if financial_data.get('budget_overshoots'):
            budget_overshoots_str = ', '.join(financial_data.get('budget_overshoots', []))
        else:
            budget_overshoots_str = 'No budget overshoots'
        
        prompt = f"""You are an expert Personal Finance Advisor specializing in spending optimization. You have access to REAL-TIME market data and the user's ACTUAL financial data.

CRITICAL: Use ONLY the ACTUAL numbers provided. Reference specific dollar amounts, categories, and percentages from their real data.

REAL-TIME MARKET & ECONOMIC CONDITIONS (LIVE DATA):
{market_summary_str}

Market Sentiment: {market_context.get('market', {}).get('sentiment', 'neutral')}
S&P 500 Performance: {sp500_perf}
Volatility (VIX): {vix:.2f} ({vix_level})
10-Year Treasury Yield: {treasury_yield}
Yield Curve Status: {yield_curve_status}
Inflation Expectation: {inflation_exp}

USER'S ACTUAL FINANCIAL SITUATION (REAL DATA):
- Total Account Balance: ${financial_data.get('total_balance', 0):,.2f}
- Monthly Income: ${financial_data.get('monthly_income', 0):,.2f}
- Monthly Expenses: ${financial_data.get('monthly_expenses', 0):,.2f}
- Savings Rate: {financial_data.get('savings_rate', 0):.1f}%
- Active Budgets: {financial_data.get('active_budgets_count', 0)}
- Active Goals: {financial_data.get('goals_count', 0)}

DETAILED BUDGET STATUS (ACTUAL):
{budget_status_str}

TOP SPENDING CATEGORIES (ACTUAL):
{spending_cat_str}

GOAL PROGRESS (ACTUAL):
{goal_progress_str}

BUDGET OVERSHOOTS (ACTUAL):
{budget_overshoots_str}

INSTRUCTIONS:
1. Reference SPECIFIC categories and amounts from the user's actual data
2. Provide dollar-specific recommendations based on ACTUAL income and expenses
3. Address SPECIFIC budget overshoots and goals
4. Reference REAL market conditions (e.g., "With current interest rates at {treasury_10y:.2f}%...")

Provide analysis in JSON format with:
1. spending_optimization: List of SPECIFIC ways to reduce spending using ACTUAL categories and amounts
2. savings_opportunities: List of SPECIFIC areas to save based on their ACTUAL spending patterns
3. priority_actions: Top 3 actions addressing their SPECIFIC budget overshoots and goals
4. budget_adjustments: Recommended adjustments for their ACTUAL budgets
5. financial_health_tips: Tips based on their ACTUAL savings rate ({financial_data.get('savings_rate', 0):.1f}%) and financial situation
6. risk_factors: Risks based on ACTUAL market conditions (VIX: {vix:.2f}, Rates: {treasury_10y:.2f}%)
7. positive_highlights: What they're doing well based on ACTUAL data

Be SPECIFIC, use REAL NUMBERS, and reference ACTUAL DATA throughout.
"""
        
        try:
            # Ollama doesn't have async ainvoke, use invoke instead
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.llm.invoke, prompt)
            response_text = response if isinstance(response, str) else str(response)
            
            import json
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback based on ACTUAL data (not hardcoded)
                top_category = list(financial_data.get('top_spending_categories', {}).keys())[0] if financial_data.get('top_spending_categories') else "spending"
                top_amount = list(financial_data.get('top_spending_categories', {}).values())[0] if financial_data.get('top_spending_categories') else 0
                savings_rate = financial_data.get('savings_rate', 0)
                monthly_income = financial_data.get('monthly_income', 0)
                target_savings = monthly_income * 0.20
                current_savings = monthly_income - financial_data.get('monthly_expenses', 0)
                
                result = {
                    "spending_optimization": [
                        f"Review your {top_category} category where you're spending ${top_amount:,.2f}",
                        f"With monthly expenses of ${financial_data.get('monthly_expenses', 0):,.2f}, consider reducing by 10-15%",
                        "Cancel unused subscriptions",
                        "Use cashback rewards for purchases",
                        "Negotiate better rates on bills and services"
                    ] if financial_data.get('top_spending_categories') else [
                        "Review top spending categories and identify areas to cut back",
                        "Consider meal planning to reduce food expenses",
                        "Cancel unused subscriptions"
                    ],
                    "savings_opportunities": [
                        f"Automate savings transfers to reach ${target_savings:,.2f} monthly savings (20% of ${monthly_income:,.2f} income)",
                        f"Consider high-yield savings accounts (current rates ~{treasury_10y:.2f}%)" if treasury_10y > 0 else "Consider high-yield savings accounts",
                        "Reduce dining out expenses",
                        "Shop during sales and use coupons"
                    ],
                    "priority_actions": [
                        f"Address budget overshoots in: {', '.join(financial_data.get('budget_overshoots', []))}" if financial_data.get('budget_overshoots') else "Review your budget status",
                        f"Increase savings from ${current_savings:,.2f} to ${target_savings:,.2f} per month",
                        "Review and cancel unnecessary subscriptions"
                    ],
                    "budget_adjustments": {
                        "increase": ["Emergency fund allocation"] if market_context.get('economic', {}).get('yield_curve_inverted') else [],
                        "decrease": list(financial_data.get('top_spending_categories', {}).keys())[:2] if financial_data.get('top_spending_categories') else []
                    },
                    "financial_health_tips": [
                        f"Aim to increase savings rate from {savings_rate:.1f}% to 20%",
                        f"Build 3-6 months emergency fund (target: ${financial_data.get('monthly_expenses', 0) * 6:,.2f})",
                        "Track expenses daily",
                        "Review budgets weekly"
                    ],
                    "risk_factors": [
                        f"High market volatility (VIX: {vix:.2f})" if vix > 20 else [],
                        f"Yield curve inversion suggests recession risk" if market_context.get('economic', {}).get('yield_curve_inverted') else []
                    ],
                    "positive_highlights": [
                        "You're tracking your finances",
                        "You have financial goals set"
                    ] if financial_data.get('goals_count', 0) > 0 else ["You're tracking your finances"]
                }
            
            return result
            
        except Exception as e:
            logger.error("Error in spending optimization", error=str(e))
            # Get market context for fallback
            try:
                market_context = await self.market_service.get_comprehensive_market_context()
            except:
                market_context = {}
            
            # Return fallback recommendations based on financial data AND market conditions
            fallback_recommendations = []
            if financial_data.get("budget_overshoots"):
                fallback_recommendations.append(f"Address budget overshoots in: {', '.join(financial_data['budget_overshoots'])}")
            if financial_data.get("savings_rate", 0) < 20:
                fallback_recommendations.append("Increase your savings rate to at least 20% of income")
            if financial_data.get("top_spending_categories"):
                top_cat = list(financial_data["top_spending_categories"].keys())[0]
                fallback_recommendations.append(f"Review spending in {top_cat} category")
            
            # Market-aware recommendations
            market_sentiment = market_context.get('market', {}).get('sentiment', 'neutral')
            interest_rate = market_context.get('economic', {}).get('treasury_10y')
            # Handle None values safely
            interest_rate = interest_rate if interest_rate is not None else 0
            inflation = market_context.get('inflation', {}).get('inflation_expectation', 'moderate')
            vix_value = market_context.get('market', {}).get('vix')
            vix_value = vix_value if vix_value is not None else 0
            volatility = 'high' if vix_value > 20 else 'low' if vix_value < 15 else 'moderate'
            
            savings_ops = [
                "Automate savings transfers",
                f"Consider high-yield savings accounts (current rates ~{interest_rate:.2f}%)" if interest_rate and interest_rate > 0 else "Consider high-yield savings accounts",
                "Reduce dining out expenses",
                "Shop during sales and use coupons",
            ]
            if inflation == 'high':
                savings_ops.append("Consider inflation-protected investments (TIPS, I-Bonds)")
            
            priority_actions = []
            if financial_data.get("budget_overshoots"):
                priority_actions.append("Address budget overshoots immediately")
            if market_context.get('economic', {}).get('yield_curve_inverted'):
                priority_actions.append("Build emergency fund (recession risk elevated)")
            if volatility == 'high':
                priority_actions.append("Avoid market timing - use dollar-cost averaging")
            priority_actions.append("Set up automatic savings")
            
            risk_factors = []
            if market_context.get('economic', {}).get('yield_curve_inverted'):
                risk_factors.append("Yield curve inversion suggests recession risk")
            if volatility == 'high':
                risk_factors.append("High market volatility - expect price swings")
            if inflation == 'high':
                risk_factors.append("Elevated inflation may erode purchasing power")
            
            return {
                "spending_optimization": [
                    "Review top spending categories and identify areas to cut back",
                    "Consider meal planning to reduce food expenses",
                    "Cancel unused subscriptions",
                    "Use cashback rewards for purchases",
                    "Negotiate better rates on bills and services",
                    f"Given {inflation} inflation, prioritize essential spending"
                ] if not fallback_recommendations else fallback_recommendations,
                "savings_opportunities": savings_ops,
                "priority_actions": priority_actions if priority_actions else [
                    "Set up automatic savings",
                    "Review and cancel unnecessary subscriptions"
                ],
                "budget_adjustments": {
                    "increase": ["Emergency fund allocation"] if market_context.get('economic', {}).get('yield_curve_inverted') else [],
                    "decrease": list(financial_data.get('top_spending_categories', {}).keys())[:2] if financial_data.get('top_spending_categories') else []
                },
                "financial_health_tips": [
                    "Aim for 20% savings rate",
                    f"Build 3-6 months emergency fund (especially important in current {market_sentiment} market)",
                    "Track expenses daily",
                    "Review budgets weekly",
                ] + (market_context.get('summary', [])[:2] if market_context.get('summary') else []),
                "risk_factors": risk_factors,
                "positive_highlights": [
                    "You're tracking your finances",
                    "You have financial goals set"
                ],
                "market_insights": market_context.get('summary', [])
            }
    
    async def get_financial_advice(self, user_id: int, question: str, db: Session) -> Dict[str, Any]:
        """Get hyper-personalized financial advice based on user question, their financial situation, and current market conditions."""
        try:
            financial_data = await self._get_user_financial_data(user_id, db)
        except Exception as e:
            logger.error("Error getting user financial data", error=str(e))
            financial_data = {}
        
        try:
            market_context = await self.market_service.get_comprehensive_market_context()
        except Exception as e:
            logger.error("Error getting market context", error=str(e))
            market_context = {}
        
        # Check if question is about stocks/investments
        question_lower = question.lower()
        is_stock_question = any(keyword in question_lower for keyword in [
            "stock", "stocks", "invest", "investment", "investing", "buy stock", 
            "which stock", "what stock", "recommend stock", "portfolio", "equity",
            "should i buy", "what to invest", "best stock", "good stock",
            "where to invest", "where should i invest", "how to invest",
            "invest next", "investment opportunities", "investing opportunities",
            "buy shares", "purchase stock", "stock recommendations"
        ])
        
        # Get stock recommendations if relevant
        stock_recommendations = []
        if is_stock_question:
            try:
                stock_recommendations = await self.stock_service.get_recommended_stocks(
                    market_context=market_context,
                    risk_tolerance="moderate",  # Could be determined from user profile
                    investment_amount=None  # Could be determined from user goals
                )
            except Exception as e:
                logger.error("Error getting stock recommendations", error=str(e))
        
        # Build detailed financial stats prompt
        financial_stats = ""
        if financial_data:
            # Build strings separately to avoid f-string syntax errors
            if financial_data.get('budget_status'):
                budget_status_lines = []
                for b in financial_data.get('budget_status', []):
                    budget_status_lines.append(f"- {b.get('category', 'Unknown')}: ${b.get('spent', 0):,.2f} spent of ${b.get('amount', 0):,.2f} budget ({b.get('percentage', 0):.1f}% used) - Status: {b.get('status', 'unknown')}")
                budget_status_str = chr(10).join(budget_status_lines)
            else:
                budget_status_str = "No active budgets"
            
            if financial_data.get('top_spending_categories'):
                spending_cat_lines = []
                for cat, amount in list(financial_data.get('top_spending_categories', {}).items())[:5]:
                    spending_cat_lines.append(f"- {cat}: ${amount:,.2f}")
                spending_cat_str = chr(10).join(spending_cat_lines)
            else:
                spending_cat_str = "No spending data available"
            
            if financial_data.get('budget_overshoots'):
                budget_overshoots_str = ', '.join(financial_data.get('budget_overshoots', []))
            else:
                budget_overshoots_str = 'No budget overshoots'
            
            if financial_data.get('goal_progress'):
                goal_progress_lines = []
                for g in financial_data.get('goal_progress', []):
                    goal_progress_lines.append(f"- {g.get('name', 'Unknown')}: ${g.get('current', 0):,.2f} / ${g.get('target', 0):,.2f} ({g.get('percentage', 0):.1f}% complete) - {g.get('days_remaining', 0)} days remaining")
                goal_progress_str = chr(10).join(goal_progress_lines)
            else:
                goal_progress_str = "No active goals"
            
            financial_stats = f"""
USER'S ACTUAL FINANCIAL SITUATION (REAL DATA):
- Total Account Balance: ${financial_data.get('total_balance', 0):,.2f}
- Monthly Income: ${financial_data.get('monthly_income', 0):,.2f}
- Monthly Expenses: ${financial_data.get('monthly_expenses', 0):,.2f}
- Savings Rate: {financial_data.get('savings_rate', 0):.1f}%
- Active Budgets: {financial_data.get('active_budgets_count', 0)}
- Active Financial Goals: {financial_data.get('goals_count', 0)}
- Accounts: {financial_data.get('accounts_count', 0)}

DETAILED BUDGET STATUS (ACTUAL):
{budget_status_str}

TOP SPENDING CATEGORIES (ACTUAL):
{spending_cat_str}

BUDGET OVERSHOOTS (ACTUAL):
{budget_overshoots_str}

GOAL PROGRESS (ACTUAL):
{goal_progress_str}
"""
        
        # Build market context with real data
        market_info = ""
        if market_context:
            vix = market_context.get('market', {}).get('vix', 0) or 0
            treasury_10y = market_context.get('economic', {}).get('treasury_10y', 0) or 0
            sp500_change = market_context.get('market', {}).get('sp500', {}).get('change_pct', 0) if market_context.get('market', {}).get('sp500') else 0
            
            # Build strings separately to avoid f-string syntax errors
            market_summary_str = chr(10).join([f"- {item}" for item in market_context.get('summary', [])]) if market_context.get('summary') else "Market data available"
            sp500_perf = f"{sp500_change:.2f}%" if sp500_change else "N/A"
            treasury_yield = f"{treasury_10y:.2f}%" if treasury_10y else 'N/A'
            vix_level = 'High' if vix > 20 else 'Low' if vix < 15 else 'Moderate'
            yield_curve_status = 'Inverted (recession risk)' if market_context.get('economic', {}).get('yield_curve_inverted') else 'Normal'
            inflation_exp = market_context.get('inflation', {}).get('inflation_expectation', 'moderate')
            
            market_info = f"""
REAL-TIME MARKET & ECONOMIC CONDITIONS (LIVE DATA):
{market_summary_str}

Market Sentiment: {market_context.get('market', {}).get('sentiment', 'neutral')}
S&P 500 Performance: {sp500_perf}
Volatility Index (VIX): {vix:.2f} ({vix_level})
10-Year Treasury Yield: {treasury_yield}
Yield Curve Status: {yield_curve_status}
Inflation Expectation: {inflation_exp}
"""
        
        # Build stock recommendations with real Alpha Vantage data
        stock_info = ""
        if stock_recommendations:
            # Build strings separately to avoid f-string syntax errors
            stock_lines = []
            for s in stock_recommendations[:8]:
                stock_name = s.get('name', s.get('symbol', 'N/A'))
                stock_line = (f"- {s.get('symbol', 'N/A')} ({stock_name}): {s.get('recommendation', 'HOLD')} at ${s.get('current_price', 0):.2f} | "
                            f"52w Change: {s.get('price_change_52w', 0):.2f}% | "
                            f"Reasons: {', '.join(s.get('reasons', [])[:2])} | "
                            f"P/E: {s.get('fundamentals', {}).get('pe_ratio', 'N/A')} | "
                            f"Dividend Yield: {s.get('fundamentals', {}).get('dividend_yield', 'N/A')}")
                stock_lines.append(stock_line)
            stock_info_str = chr(10).join(stock_lines)
            
            stock_info = f"""
REAL-TIME STOCK RECOMMENDATIONS (FROM ALPHA VANTAGE & YFINANCE DATA):
{stock_info_str}
"""
        
        # Build prompt based on question type
        if is_stock_question and stock_recommendations:
            question_context = "INVESTMENT QUESTION - The user is asking about WHERE TO INVEST. Provide SPECIFIC investment recommendations using the stock recommendations provided below. Focus on investment opportunities, portfolio allocation, and specific stocks to consider based on their budget and financial situation."
        elif is_stock_question:
            question_context = "INVESTMENT QUESTION - The user is asking about WHERE TO INVEST. Provide investment advice including portfolio allocation strategies, types of investments to consider, and general investment guidance based on their budget and financial situation."
        else:
            question_context = "GENERAL FINANCIAL QUESTION - Provide financial advice relevant to the user's specific question."
        
        prompt = f"""You are an expert Personal Finance Advisor with access to REAL-TIME market data from Alpha Vantage, live economic indicators, and the user's ACTUAL financial data. 

CRITICAL: You MUST use the ACTUAL numbers and data provided below. Do NOT use generic advice or hypothetical scenarios. Reference specific dollar amounts, percentages, and market conditions.

{question_context}

{market_info}

{financial_stats}

{stock_info}

USER'S QUESTION: {question}

INSTRUCTIONS:
{"FOR INVESTMENT QUESTIONS: Focus on providing SPECIFIC investment recommendations. If stock recommendations are provided, list them with their prices, recommendations, and reasons. Explain how much to invest based on their budget (e.g., 'With your monthly income of ${financial_data.get('monthly_income', 0):,.2f} and expenses of ${financial_data.get('monthly_expenses', 0):,.2f}, you have ${financial_data.get('monthly_income', 0) - financial_data.get('monthly_expenses', 0):,.2f} available. Consider investing X% of this amount...'). Reference specific stocks from the recommendations provided." if is_stock_question else ""}
1. Use the ACTUAL financial numbers provided (e.g., "With your current savings rate of {financial_data.get('savings_rate', 0):.1f}% and monthly income of ${financial_data.get('monthly_income', 0):,.2f}...")
2. Reference REAL market conditions (e.g., "With current VIX at {market_context.get('market', {}).get('vix', 0) or 0:.2f} and interest rates at {market_context.get('economic', {}).get('treasury_10y', 0) or 0:.2f}%...")
3. {"If stock recommendations are provided, list them prominently with their ACTUAL prices, recommendations (BUY/HOLD/SELL), and reasons. Calculate how much they can invest based on their budget." if is_stock_question else "Address their SPECIFIC budget overshoots, goals, and spending patterns"}
4. Provide dollar-specific advice based on their ACTUAL income and expenses

Provide your response in JSON format with:
1. answer: {"Direct answer with SPECIFIC investment recommendations. If stock recommendations are provided, list them with prices and reasons. Calculate investment amounts based on their budget (e.g., 'Based on your monthly income of ${financial_data.get('monthly_income', 0):,.2f} and expenses of ${financial_data.get('monthly_expenses', 0):,.2f}, you have ${financial_data.get('monthly_income', 0) - financial_data.get('monthly_expenses', 0):,.2f} available. Consider investing $X in [specific stocks]...')." if is_stock_question else "Direct answer using ACTUAL numbers and data (e.g., 'Based on your monthly income of ${financial_data.get('monthly_income', 0):,.2f}...')"}
2. recommendations: {"Specific investment recommendations with stock names, prices, and allocation suggestions" if is_stock_question else "Specific recommendations tailored to their ACTUAL financial situation"}
3. considerations: Real market risks and opportunities based on CURRENT conditions
4. next_steps: {"Actionable investment steps with specific dollar amounts and stock names" if is_stock_question else "Actionable steps with specific dollar amounts or percentages"}
5. market_context: How CURRENT market conditions (VIX: {market_context.get('market', {}).get('vix', 0) or 0:.2f}, Rates: {market_context.get('economic', {}).get('treasury_10y', 0) or 0:.2f}%) affect them

Be SPECIFIC, use REAL NUMBERS, and reference ACTUAL DATA throughout your response.
{"FOR INVESTMENT QUESTIONS: Make sure to provide actual stock recommendations with prices and reasons. Don't give generic budgeting advice - focus on WHERE TO INVEST." if is_stock_question else ""}
"""
        
        try:
            # Ollama doesn't have async ainvoke, use invoke instead
            # Add timeout to prevent hanging
            # Use shorter timeout for quantized models (they're faster)
            # llama3.2:3b typically responds in 5-10 seconds, larger models may take 15-30s
            import asyncio
            loop = asyncio.get_event_loop()
            timeout = 20.0 if "3b" in settings.OLLAMA_MODEL.lower() else 30.0
            response = await asyncio.wait_for(
                loop.run_in_executor(None, self.llm.invoke, prompt),
                timeout=timeout
            )
            response_text = response if isinstance(response, str) else str(response)
            
            import json
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {
                    "answer": response_text[:500],
                    "recommendations": [],
                    "considerations": [],
                    "next_steps": []
                }
            
            # Add stock recommendations if available
            if stock_recommendations:
                result["stock_recommendations"] = stock_recommendations[:8]
                if "answer" in result:
                    # Enhance answer with stock recommendations
                    if is_stock_question:
                        stock_summary = ", ".join([f"{s['symbol']} ({s.get('recommendation', 'HOLD')})" for s in stock_recommendations[:3]])
                        result["answer"] += f"\n\nBased on current market conditions, I recommend considering: {stock_summary}. See detailed recommendations below."
            
            return result
        except asyncio.TimeoutError:
            logger.error("Timeout getting financial advice from LLM")
            # Fall through to exception handler with stock recommendations
            raise Exception("LLM timeout")
            
        except Exception as e:
            logger.error("Error getting financial advice", error=str(e))
            # Provide helpful fallback answer based on common questions and market context
            market_context = await self.market_service.get_comprehensive_market_context()
            market_summary = ", ".join(market_context.get('summary', [])) if market_context.get('summary') else "moderate market conditions"
            interest_rate = market_context.get('economic', {}).get('treasury_10y', 0)
            inflation = market_context.get('inflation', {}).get('inflation_expectation', 'moderate')
            
            question_lower = question.lower()
            
            # Handle stock investment questions - use actual user financial data
            if is_stock_question:
                try:
                    # Get user's available funds for investment
                    monthly_income = financial_data.get('monthly_income', 0)
                    monthly_expenses = financial_data.get('monthly_expenses', 0)
                    available_for_investment = monthly_income - monthly_expenses
                    savings_rate = financial_data.get('savings_rate', 0)
                    
                    stock_recommendations = await self.stock_service.get_recommended_stocks(
                        market_context=market_context,
                        risk_tolerance="moderate"
                    )
                    
                    if stock_recommendations:
                        top_stocks = stock_recommendations[:5]
                        stock_list = "\n".join([
                            f"- {s['symbol']} ({s.get('name', s['symbol'])}): {s.get('recommendation', 'HOLD')} at ${s.get('current_price', 0):.2f} - {', '.join(s.get('reasons', [])[:2])}"
                            for s in top_stocks
                        ])
                        
                        # Calculate investment amount based on budget
                        investment_suggestion = available_for_investment * 0.3 if available_for_investment > 0 else 0
                        answer = f"Based on your budget (monthly income: ${monthly_income:,.2f}, expenses: ${monthly_expenses:,.2f}), you have ${available_for_investment:,.2f} available. Here are my investment recommendations for next month:\n\n{stock_list}\n\nWith your current savings rate of {savings_rate:.1f}%, consider investing ${investment_suggestion:,.2f} (30% of available funds) in these stocks. Always diversify and do your own research before investing."
                    else:
                        investment_suggestion = available_for_investment * 0.3 if available_for_investment > 0 else 0
                        answer = f"Based on your budget (monthly income: ${monthly_income:,.2f}, expenses: ${monthly_expenses:,.2f}), you have ${available_for_investment:,.2f} available. For next month, I recommend: 1) Consider diversified ETFs like SPY or VTI (invest ${investment_suggestion:,.2f}), 2) Use dollar-cost averaging, 3) Build emergency fund first. Current interest rates are {interest_rate:.2f}% and inflation is {inflation}."
                except Exception as stock_err:
                    logger.error("Error getting stock recommendations", error=str(stock_err))
                    monthly_income = financial_data.get('monthly_income', 0)
                    monthly_expenses = financial_data.get('monthly_expenses', 0)
                    available_for_investment = monthly_income - monthly_expenses
                    investment_suggestion = available_for_investment * 0.3 if available_for_investment > 0 else 0
                    answer = f"Based on your budget (monthly income: ${monthly_income:,.2f}, expenses: ${monthly_expenses:,.2f}), you have ${available_for_investment:,.2f} available. For next month: 1) Consider diversified ETFs (invest ${investment_suggestion:,.2f}), 2) Use dollar-cost averaging, 3) Build emergency fund first. Current interest rates are {interest_rate:.2f}%."
            elif "save" in question_lower or "saving" in question_lower:
                answer = f"Based on your financial situation and current market conditions ({market_summary}), I recommend: 1) Automate savings transfers, 2) Reduce dining out expenses, 3) Review and cancel unused subscriptions. With current interest rates at {interest_rate:.2f}% and inflation at {inflation} levels, start by setting aside at least 20% of your income for savings. Consider high-yield savings accounts for better returns."
            elif "budget" in question_lower:
                answer = f"To improve your budgeting in the current economic environment: 1) Track all expenses daily (especially important with {inflation} inflation), 2) Review budgets weekly, 3) Adjust budgets based on actual spending. Focus on categories where you're overspending. Given current market conditions, consider allocating more to necessities."
            elif "debt" in question_lower:
                answer = f"To pay off debt faster in the current environment: 1) Prioritize high-interest debt (especially important with interest rates at {interest_rate:.2f}%), 2) Consider debt consolidation if rates are favorable, 3) Increase monthly payments. The debt snowball or avalanche method can help. Lock in fixed rates if possible."
            elif "invest" in question_lower or "investment" in question_lower:
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
            
            # Add stock recommendations if it was a stock question
            if is_stock_question:
                try:
                    stock_recommendations = await self.stock_service.get_recommended_stocks(
                        market_context=market_context,
                        risk_tolerance="moderate"
                    )
                    if stock_recommendations:
                        result["stock_recommendations"] = stock_recommendations[:8]
                except Exception as stock_err:
                    logger.error("Error getting stock recommendations in fallback", error=str(stock_err))
            
            return result

