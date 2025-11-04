"""
Agent orchestration service using LangGraph with Ollama.
"""
import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import structlog

from app.core.config import settings
from app.db import models

logger = structlog.get_logger()


class AgentService:
    """Service for orchestrating multi-agent system."""
    
    def __init__(self):
        """Initialize agent service with Ollama LLM."""
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.5,  # Lower temperature for faster, more focused responses
        )
    
    async def _get_user_financial_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user financial data for agent context."""
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return {}
        
        accounts = db.query(models.Account).filter(models.Account.user_id == user_id).all()
        transactions = db.query(models.Transaction).filter(
            models.Transaction.user_id == user_id
        ).limit(100).all()
        budgets = db.query(models.Budget).filter(models.Budget.user_id == user_id).all()
        goals = db.query(models.Goal).filter(models.Goal.user_id == user_id).all()
        
        total_balance = sum(acc.balance for acc in accounts)
        # Get current month/year for filtering
        from datetime import datetime
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        # Handle timezone-aware datetimes
        if transactions and transactions[0].date.tzinfo:
            now = datetime.now(transactions[0].date.tzinfo)
            current_month = now.month
            current_year = now.year
        monthly_income = sum(t.amount for t in transactions if t.amount > 0 and t.date.month == current_month and t.date.year == current_year)
        monthly_expenses = abs(sum(t.amount for t in transactions if t.amount < 0 and t.date.month == current_month and t.date.year == current_year))
        
        return {
            "total_balance": total_balance,
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "accounts_count": len(accounts),
            "budgets_count": len(budgets),
            "goals_count": len(goals),
            "transaction_categories": list(set(t.category for t in transactions if t.category)),
        }
    
    async def run_financial_planner_agent(
        self,
        user_id: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run Financial Planner Agent."""
        start_time = time.time()
        
        try:
            # Get user financial data
            from app.db.database import SessionLocal
            db = SessionLocal()
            try:
                financial_data = await self._get_user_financial_data(user_id, db)
            finally:
                db.close()
            
            # Prepare prompt for Ollama (text-based) - Fine-tuned for personal finance
            prompt_text = f"""You are an expert Financial Planner Agent specializing in personal finance. Your role is to analyze user financial data and provide personalized budget recommendations.

FINANCIAL PLANNING EXPERTISE:
- You understand the 50/30/20 budget rule (50% needs, 30% wants, 20% savings)
- You know emergency fund best practices (3-6 months expenses)
- You understand debt payoff strategies (snowball vs avalanche)
- You can identify spending patterns and optimize budgets

Analyze the user's financial situation and provide:
1. Budget recommendations for different categories based on income and expenses
2. Savings suggestions aligned with financial goals
3. Financial insights based on spending patterns
4. Specific dollar amounts for each category

Be practical, actionable, and supportive in your recommendations. Use personal finance principles.

User Financial Data:
- Total Balance: ${financial_data.get('total_balance', 0):,.2f}
- Monthly Income: ${financial_data.get('monthly_income', 0):,.2f}
- Monthly Expenses: ${financial_data.get('monthly_expenses', 0):,.2f}
- Transaction Categories: {', '.join(financial_data.get('transaction_categories', []))}

Context: {context}

Provide budget recommendations in JSON format with:
- recommendations: List of {{category, recommended_amount, reasoning}}
- total_recommended_budget: Total budget amount
- savings_suggestion: Suggested savings amount
- insights: List of financial insights
"""
            
            # Ollama doesn't have async ainvoke, use invoke instead
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.llm.invoke, prompt_text)
            
            # Parse response (simplified - in production, use structured output)
            import json
            import re
            response_text = response if isinstance(response, str) else str(response)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback structure
                result = {
                    "recommendations": [
                        {
                            "category": "Food & Dining",
                            "recommended_amount": financial_data.get('monthly_income', 0) * 0.15,
                            "reasoning": "Standard recommendation for food expenses"
                        },
                        {
                            "category": "Transportation",
                            "recommended_amount": financial_data.get('monthly_income', 0) * 0.10,
                            "reasoning": "Standard recommendation for transportation"
                        }
                    ],
                    "total_recommended_budget": financial_data.get('monthly_income', 0) * 0.80,
                    "savings_suggestion": financial_data.get('monthly_income', 0) * 0.20,
                    "insights": [
                        "Consider setting aside 20% of income for savings",
                        "Track expenses regularly to stay within budget"
                    ]
                }
            
            execution_time = int((time.time() - start_time) * 1000)
            logger.info("Financial Planner Agent executed", execution_time_ms=execution_time)
            
            return result
            
        except Exception as e:
            logger.error("Financial Planner Agent error", error=str(e))
            raise
    
    async def run_risk_assessment_agent(
        self,
        user_id: int,
        risk_score: float,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run Risk Assessment Agent."""
        start_time = time.time()
        
        try:
            prompt_text = f"""You are an expert Risk Assessment Agent specializing in personal finance and investment risk. Your role is to evaluate user financial risk and provide investment recommendations.

PERSONAL FINANCE RISK ASSESSMENT EXPERTISE:
- You understand risk tolerance levels (conservative, moderate, aggressive)
- You know investment diversification principles
- You understand asset allocation based on age and goals
- You can assess financial stability before recommending investments

Based on the risk score and user profile, provide:
1. Risk level assessment with explanation
2. Investment recommendations appropriate for their risk level
3. Warnings and precautions
4. Specific investment types (stocks, bonds, ETFs, etc.)

Be conservative and prioritize user financial security. Only recommend investments if they have emergency fund and stable income.

User Risk Score: {risk_score:.2f} (0-1 scale, where 0 is low risk, 1 is high risk)

Context: {context}

Provide risk assessment in JSON format with:
- risk_level: "low", "medium", or "high"
- recommendations: List of investment recommendations
- suitable_investment_types: List of suitable investment types
- warnings: List of warnings
"""
            
            # Ollama doesn't have async ainvoke, use invoke instead
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.llm.invoke, prompt_text)
            
            import json
            import re
            response_text = response if isinstance(response, str) else str(response)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback
                if risk_score < 0.3:
                    risk_level = "low"
                    investment_types = ["Savings Account", "CDs", "Bonds", "Conservative Mutual Funds"]
                elif risk_score < 0.7:
                    risk_level = "medium"
                    investment_types = ["Balanced Portfolio", "ETFs", "Moderate Mutual Funds"]
                else:
                    risk_level = "high"
                    investment_types = ["Stocks", "Aggressive Growth Funds"]
                
                result = {
                    "risk_level": risk_level,
                    "recommendations": [
                        "Diversify your investment portfolio",
                        "Consider your time horizon before investing",
                        "Start with small amounts to build confidence"
                    ],
                    "suitable_investment_types": investment_types,
                    "warnings": [
                        "Never invest more than you can afford to lose",
                        "Consult with a financial advisor for complex decisions"
                    ]
                }
            
            execution_time = int((time.time() - start_time) * 1000)
            logger.info("Risk Assessment Agent executed", execution_time_ms=execution_time)
            
            return result
            
        except Exception as e:
            logger.error("Risk Assessment Agent error", error=str(e))
            raise
    
    async def run_learning_agent(
        self,
        user_id: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run Learning & Motivation Agent."""
        start_time = time.time()
        
        try:
            # Get user progress with timeout
            import asyncio
            from app.db.database import SessionLocal
            db = SessionLocal()
            try:
                # Add timeout to prevent hanging
                financial_data = await asyncio.wait_for(
                    self._get_user_financial_data(user_id, db),
                    timeout=10.0
                )
                goals = db.query(models.Goal).filter(models.Goal.user_id == user_id).all()
            except asyncio.TimeoutError:
                logger.error("Timeout getting user financial data for motivation")
                financial_data = {}
                goals = []
            finally:
                db.close()
            
            # Build detailed financial stats for motivation
            savings_rate = financial_data.get('savings_rate', 0)
            monthly_income = financial_data.get('monthly_income', 0)
            monthly_expenses = financial_data.get('monthly_expenses', 0)
            total_balance = financial_data.get('total_balance', 0)
            goals_progress = financial_data.get('goal_progress', [])
            budget_status = financial_data.get('budget_status', [])
            
            prompt_text = f"""You are a Learning & Motivation Agent specializing in personal finance education. You have access to the user's ACTUAL financial data.

CRITICAL: Use the ACTUAL numbers provided. Reference specific dollar amounts and percentages from their real financial situation.

USER'S ACTUAL FINANCIAL SITUATION (REAL DATA):
- Total Account Balance: ${total_balance:,.2f}
- Monthly Income: ${monthly_income:,.2f}
- Monthly Expenses: ${monthly_expenses:,.2f}
- Savings Rate: {savings_rate:.1f}%
- Active Goals: {len(goals)}

GOAL PROGRESS (ACTUAL):
{chr(10).join([f"- {g.get('name', 'Unknown')}: ${g.get('current', 0):,.2f} / ${g.get('target', 0):,.2f} ({g.get('percentage', 0):.1f}% complete) - {g.get('days_remaining', 0)} days remaining" for g in goals_progress]) if goals_progress else "No active goals"}

BUDGET STATUS (ACTUAL):
{chr(10).join([f"- {b.get('category', 'Unknown')}: {b.get('percentage', 0):.1f}% used" for b in budget_status[:3]]) if budget_status else "No active budgets"}

INSTRUCTIONS:
1. Reference their ACTUAL savings rate ({savings_rate:.1f}%) and provide encouragement
2. If they have goals, reference SPECIFIC progress (e.g., "You're {goals_progress[0].get('percentage', 0):.1f}% towards your {goals_progress[0].get('name', 'goal')}!")
3. Provide dollar-specific tips based on their ACTUAL income (${monthly_income:,.2f})
4. Celebrate achievements if savings rate is good or goals are progressing well

Provide motivation in JSON format with:
- quote: An inspiring financial quote (personalized to their situation if possible)
- tip: A practical financial tip using ACTUAL numbers (e.g., "With your income of ${monthly_income:,.2f}, aim to save ${monthly_income * 0.20:,.2f}/month")
- achievement_message: Optional achievement message based on their ACTUAL progress
- progress_insights: List of progress insights referencing their ACTUAL goals and budgets

Be encouraging, positive, and educational. Reference their ACTUAL financial data throughout.
"""
            
            # Ollama doesn't have async ainvoke, use invoke instead
            # Add timeout to prevent hanging
            import asyncio
            loop = asyncio.get_event_loop()
            from app.core.config import settings
            timeout = 20.0 if "3b" in settings.OLLAMA_MODEL.lower() else 30.0
            
            try:
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, self.llm.invoke, prompt_text),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.error("Timeout getting motivation from LLM")
                raise Exception("LLM timeout")
            
            import json
            import re
            response_text = response if isinstance(response, str) else str(response)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback based on ACTUAL user data (not hardcoded)
                savings_rate = financial_data.get('savings_rate', 0)
                monthly_income = financial_data.get('monthly_income', 0)
                goals_progress = financial_data.get('goal_progress', [])
                
                quote = "The best time to plant a tree was 20 years ago. The second best time is now."
                tip = f"Automate your savings by setting up automatic transfers to save ${monthly_income * 0.20:,.2f} per month (20% of ${monthly_income:,.2f} income)."
                
                if savings_rate >= 20:
                    quote = "You're doing great! Consistent saving is the foundation of financial freedom."
                    tip = "Continue maintaining your excellent savings rate and consider investing surplus funds."
                elif savings_rate < 10:
                    tip = f"With your current savings rate of {savings_rate:.1f}%, aim to increase it gradually. Start by saving ${monthly_income * 0.10:,.2f} per month (10% of income)."
                
                progress_insights = []
                if goals_progress:
                    progress_insights.append(f"You're making progress on {len(goals_progress)} goal{'s' if len(goals_progress) > 1 else ''}! Keep up the momentum.")
                    if goals_progress[0].get('percentage', 0) > 50:
                        progress_insights.append(f"You're over halfway to your {goals_progress[0].get('name', 'goal')}! Stay focused!")
                else:
                    progress_insights.append("You're tracking your finances! Consider setting a financial goal to stay motivated.")
                
                progress_insights.append("Keep tracking your expenses to stay on budget.")
                
                result = {
                    "quote": quote,
                    "tip": tip,
                    "achievement_message": f"Great job maintaining a {savings_rate:.1f}% savings rate!" if savings_rate >= 15 else None,
                    "progress_insights": progress_insights
                }
            
            execution_time = int((time.time() - start_time) * 1000)
            logger.info("Learning Agent executed", execution_time_ms=execution_time)
            
            return result
            
        except Exception as e:
            logger.error("Learning Agent error", error=str(e))
            raise
    
    async def run_notification_agent(
        self,
        user_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Run Notification & Alert Agent."""
        start_time = time.time()
        alerts = []
        
        try:
            # Check budget overshoots
            budgets = db.query(models.Budget).filter(
                models.Budget.user_id == user_id,
                models.Budget.is_active == True
            ).all()
            
            for budget in budgets:
                if budget.current_spent > budget.amount:
                    alert = models.Alert(
                        user_id=user_id,
                        type="budget_overshoot",
                        title=f"Budget Exceeded: {budget.category}",
                        message=f"You've exceeded your {budget.category} budget by ${budget.current_spent - budget.amount:.2f}",
                        severity="warning",
                        metadata={"budget_id": budget.id}
                    )
                    db.add(alert)
                    alerts.append({
                        "type": "budget_overshoot",
                        "title": alert.title,
                        "message": alert.message
                    })
            
            # Check upcoming bills (simplified - in production, use transaction patterns)
            transactions = db.query(models.Transaction).filter(
                models.Transaction.user_id == user_id,
                models.Transaction.is_pending == True
            ).all()
            
            if transactions:
                alert = models.Alert(
                    user_id=user_id,
                    type="bill_reminder",
                    title="Pending Transactions",
                    message=f"You have {len(transactions)} pending transaction(s) that need attention",
                    severity="info"
                )
                db.add(alert)
                alerts.append({
                    "type": "bill_reminder",
                    "title": alert.title,
                    "message": alert.message
                })
            
            db.commit()
            
            execution_time = int((time.time() - start_time) * 1000)
            logger.info("Notification Agent executed", execution_time_ms=execution_time, alerts_generated=len(alerts))
            
            return alerts
            
        except Exception as e:
            logger.error("Notification Agent error", error=str(e))
            db.rollback()
            return []

