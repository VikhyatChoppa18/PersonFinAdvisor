"""
PyTorch model service for financial predictions and risk assessment.
"""
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from pathlib import Path
import structlog
import pickle

from app.core.config import settings

logger = structlog.get_logger()


class TimeSeriesForecaster(nn.Module):
    """LSTM-based time series forecasting model."""
    
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=1):
        super(TimeSeriesForecaster, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out


class RiskAssessmentModel(nn.Module):
    """Neural network for risk assessment."""
    
    def __init__(self, input_size=10, hidden_sizes=[64, 32, 16], output_size=1):
        super(RiskAssessmentModel, self).__init__()
        
        layers = []
        prev_size = input_size
        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(prev_size, hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_size = hidden_size
        
        layers.append(nn.Linear(prev_size, output_size))
        layers.append(nn.Sigmoid())
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


class ModelService:
    """Service for managing PyTorch models."""
    
    def __init__(self):
        """Initialize model service."""
        self.checkpoint_dir = Path(settings.MODEL_CHECKPOINT_DIR)
        self.artifact_dir = Path(settings.MODEL_ARTIFACT_DIR)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        
        self.forecaster = None
        self.risk_model = None
        self.scaler = None
        
        # Load models if available
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models if available."""
        try:
            # Load time series forecaster
            forecaster_path = self.checkpoint_dir / "forecaster.pth"
            if forecaster_path.exists():
                self.forecaster = TimeSeriesForecaster()
                self.forecaster.load_state_dict(torch.load(forecaster_path, map_location='cpu'))
                self.forecaster.eval()
                logger.info("Time series forecaster loaded")
            
            # Load risk assessment model
            risk_model_path = self.checkpoint_dir / "risk_model.pth"
            if risk_model_path.exists():
                self.risk_model = RiskAssessmentModel()
                self.risk_model.load_state_dict(torch.load(risk_model_path, map_location='cpu'))
                self.risk_model.eval()
                logger.info("Risk assessment model loaded")
            
            # Load scaler
            scaler_path = self.artifact_dir / "scaler.pkl"
            if scaler_path.exists():
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info("Scaler loaded")
        except Exception as e:
            logger.warning("Could not load models", error=str(e))
            # Models will be initialized on first use
    
    async def forecast_income_expenses(
        self,
        historical_data: pd.DataFrame,
        forecast_periods: int = 12
    ) -> Dict[str, List[float]]:
        """Forecast income and expenses using time series model."""
        if self.forecaster is None:
            # Initialize model if not loaded
            self.forecaster = TimeSeriesForecaster()
            logger.info("Using uninitialized forecaster - predictions will be based on trends")
        
        try:
            # Prepare data
            if 'income' in historical_data.columns and 'expenses' in historical_data.columns:
                income_data = historical_data['income'].values
                expense_data = historical_data['expenses'].values
            else:
                # Fallback: use simple moving average
                income_data = historical_data.iloc[:, 0].values if len(historical_data.columns) > 0 else [0] * len(historical_data)
                expense_data = historical_data.iloc[:, 1].values if len(historical_data.columns) > 1 else [0] * len(historical_data)
            
            # Simple forecasting using trend (since model may not be trained)
            if len(income_data) > 1:
                income_trend = np.mean(np.diff(income_data[-6:])) if len(income_data) >= 6 else 0
                expense_trend = np.mean(np.diff(expense_data[-6:])) if len(expense_data) >= 6 else 0
                
                last_income = income_data[-1]
                last_expense = expense_data[-1]
                
                income_forecast = [last_income + income_trend * (i + 1) for i in range(forecast_periods)]
                expense_forecast = [last_expense + expense_trend * (i + 1) for i in range(forecast_periods)]
            else:
                income_forecast = [income_data[0]] * forecast_periods if len(income_data) > 0 else [0] * forecast_periods
                expense_forecast = [expense_data[0]] * forecast_periods if len(expense_data) > 0 else [0] * forecast_periods
            
            return {
                "income_forecast": income_forecast,
                "expense_forecast": expense_forecast
            }
        except Exception as e:
            logger.error("Forecasting error", error=str(e))
            return {
                "income_forecast": [0] * forecast_periods,
                "expense_forecast": [0] * forecast_periods
            }
    
    async def assess_risk(self, user_data: Dict[str, Any]) -> float:
        """Assess user financial risk score (0-1 scale)."""
        if self.risk_model is None:
            # Initialize model if not loaded
            self.risk_model = RiskAssessmentModel()
            logger.info("Using uninitialized risk model - using rule-based assessment")
        
        try:
            # Extract features from user data
            features = self._extract_risk_features(user_data)
            
            # Convert to tensor
            feature_tensor = torch.FloatTensor([features])
            
            # Get risk score
            with torch.no_grad():
                if self.risk_model is not None:
                    risk_score = self.risk_model(feature_tensor).item()
                else:
                    # Rule-based fallback
                    risk_score = self._rule_based_risk_assessment(user_data)
            
            return max(0.0, min(1.0, risk_score))
            
        except Exception as e:
            logger.error("Risk assessment error", error=str(e))
            return 0.5  # Default medium risk
    
    def _extract_risk_features(self, user_data: Dict[str, Any]) -> List[float]:
        """Extract features for risk assessment."""
        total_balance = user_data.get('total_balance', 0)
        monthly_income = user_data.get('monthly_income', 0)
        monthly_expenses = user_data.get('monthly_expenses', 0)
        
        # Calculate features
        savings_rate = (monthly_income - monthly_expenses) / monthly_income if monthly_income > 0 else 0
        expense_ratio = monthly_expenses / monthly_income if monthly_income > 0 else 1
        balance_to_income = total_balance / monthly_income if monthly_income > 0 else 0
        
        # Normalize features (simplified)
        features = [
            min(savings_rate, 1.0) if savings_rate > 0 else 0.5,
            min(expense_ratio, 2.0) / 2.0,
            min(balance_to_income, 12.0) / 12.0,
            min(monthly_income / 10000, 1.0) if monthly_income > 0 else 0.5,
            min(monthly_expenses / 10000, 1.0) if monthly_expenses > 0 else 0.5,
            user_data.get('accounts_count', 1) / 10.0,
            user_data.get('budgets_count', 0) / 10.0,
            user_data.get('goals_count', 0) / 10.0,
            len(user_data.get('transaction_categories', [])) / 20.0,
            0.5  # Placeholder
        ]
        
        return features[:10]  # Ensure 10 features
    
    def _rule_based_risk_assessment(self, user_data: Dict[str, Any]) -> float:
        """Rule-based risk assessment fallback."""
        monthly_income = user_data.get('monthly_income', 0)
        monthly_expenses = user_data.get('monthly_expenses', 0)
        total_balance = user_data.get('total_balance', 0)
        
        if monthly_income == 0:
            return 0.8  # High risk if no income
        
        expense_ratio = monthly_expenses / monthly_income
        savings_rate = (monthly_income - monthly_expenses) / monthly_income
        
        # Higher expense ratio = higher risk
        # Lower savings rate = higher risk
        risk_score = 0.5  # Base risk
        
        if expense_ratio > 1.0:
            risk_score += 0.3  # Spending more than income
        elif expense_ratio > 0.9:
            risk_score += 0.2
        
        if savings_rate < 0:
            risk_score += 0.2  # Negative savings
        elif savings_rate < 0.1:
            risk_score += 0.1
        
        if total_balance < 0:
            risk_score += 0.2  # Negative balance
        
        return min(1.0, risk_score)
    
    async def personalize_recommendations(
        self,
        user_data: Dict[str, Any],
        transaction_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate personalized recommendations based on behavior analysis."""
        try:
            # Analyze spending patterns
            categories = {}
            for transaction in transaction_history:
                category = transaction.get('category', 'Other')
                amount = abs(transaction.get('amount', 0))
                if category not in categories:
                    categories[category] = 0
                categories[category] += amount
            
            # Identify top spending categories
            top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Generate personalized insights
            insights = []
            if top_categories:
                top_category = top_categories[0][0]
                insights.append(f"Your highest spending category is {top_category}")
            
            # Savings opportunity
            monthly_income = user_data.get('monthly_income', 0)
            monthly_expenses = user_data.get('monthly_expenses', 0)
            if monthly_income > monthly_expenses:
                potential_savings = monthly_income - monthly_expenses
                insights.append(f"You could save ${potential_savings:.2f} per month")
            
            return {
                "spending_patterns": dict(top_categories),
                "insights": insights,
                "recommendations": [
                    "Review your spending in top categories",
                    "Set up automatic savings",
                    "Track expenses daily"
                ]
            }
        except Exception as e:
            logger.error("Personalization error", error=str(e))
            return {
                "spending_patterns": {},
                "insights": [],
                "recommendations": []
            }

