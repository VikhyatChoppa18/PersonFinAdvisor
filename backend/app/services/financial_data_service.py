"""
Service for fetching real-time financial data.
"""
import yfinance as yf
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog
import random

logger = structlog.get_logger()


class FinancialDataService:
    """Service for fetching real-time financial data."""
    
    def __init__(self):
        """Initialize financial data service."""
        pass
    
    async def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """Get real-time stock price."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d")
            
            current_price = hist['Close'].iloc[-1] if not hist.empty else info.get('currentPrice', 0)
            previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close > 0 else 0
            
            return {
                "symbol": symbol,
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume": hist['Volume'].iloc[-1] if not hist.empty else 0,
                "high": round(hist['High'].iloc[-1], 2) if not hist.empty else current_price,
                "low": round(hist['Low'].iloc[-1], 2) if not hist.empty else current_price,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error("Error fetching stock price", symbol=symbol, error=str(e))
            return {
                "symbol": symbol,
                "price": 0,
                "error": str(e)
            }
    
    async def get_market_indices(self) -> Dict[str, Any]:
        """Get major market indices."""
        indices = {
            "SPY": "S&P 500",
            "QQQ": "NASDAQ",
            "DIA": "Dow Jones",
            "IWM": "Russell 2000"
        }
        
        results = {}
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if not hist.empty and len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change = current - previous
                    change_percent = (change / previous * 100) if previous > 0 else 0
                    
                    results[name] = {
                        "symbol": symbol,
                        "value": round(current, 2),
                        "change": round(change, 2),
                        "change_percent": round(change_percent, 2),
                    }
            except Exception as e:
                logger.error("Error fetching index", symbol=symbol, error=str(e))
                results[name] = {
                    "symbol": symbol,
                    "value": 0,
                    "error": str(e)
                }
        
        return results
    
    async def get_exchange_rates(self, base_currency: str = "USD") -> Dict[str, float]:
        """Get real-time exchange rates."""
        try:
            # Using free API for exchange rates
            url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                
                # Return popular currencies
                popular_currencies = ["EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR"]
                return {currency: rates.get(currency, 0) for currency in popular_currencies}
            else:
                logger.warning("Exchange rate API returned error", status=response.status_code)
                return {}
        except Exception as e:
            logger.error("Error fetching exchange rates", error=str(e))
            # Fallback rates (approximate)
            return {
                "EUR": 0.92,
                "GBP": 0.79,
                "JPY": 150.0,
                "CAD": 1.35,
                "AUD": 1.52,
                "CHF": 0.89,
                "CNY": 7.20,
                "INR": 83.0,
            }
    
    async def get_crypto_prices(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Get real-time cryptocurrency prices."""
        if symbols is None:
            symbols = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "ADA-USD"]
        
        results = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    change = current_price - previous_close
                    change_percent = (change / previous_close * 100) if previous_close > 0 else 0
                    
                    coin_name = symbol.replace("-USD", "")
                    results[coin_name] = {
                        "symbol": symbol,
                        "price": round(current_price, 2),
                        "change": round(change, 2),
                        "change_percent": round(change_percent, 2),
                        "volume": hist['Volume'].iloc[-1] if not hist.empty else 0,
                    }
            except Exception as e:
                logger.error("Error fetching crypto price", symbol=symbol, error=str(e))
                results[symbol.replace("-USD", "")] = {
                    "symbol": symbol,
                    "price": 0,
                    "error": str(e)
                }
        
        return results
    
    async def generate_realistic_transactions(self, user_id: int, count: int = 10) -> List[Dict[str, Any]]:
        """Generate realistic transaction data based on real financial patterns."""
        categories = [
            "Food & Dining", "Shopping", "Transportation", "Bills & Utilities",
            "Entertainment", "Healthcare", "Travel", "Education", "Groceries",
            "Gas & Fuel", "Restaurants", "Coffee Shops", "Gym", "Subscriptions"
        ]
        
        merchants = {
            "Food & Dining": ["McDonald's", "Starbucks", "Pizza Hut", "Subway", "Chipotle"],
            "Shopping": ["Amazon", "Target", "Walmart", "Best Buy", "Nike"],
            "Transportation": ["Uber", "Lyft", "Metro", "Gas Station", "Parking"],
            "Bills & Utilities": ["Electric Company", "Water Department", "Internet Provider", "Phone Bill"],
            "Entertainment": ["Netflix", "Spotify", "Movie Theater", "Concert", "Video Games"],
            "Travel": ["Airline Ticket", "Hotel", "Airbnb", "Rental Car"],
            "Groceries": ["Whole Foods", "Kroger", "Safeway", "Trader Joe's"],
        }
        
        transactions = []
        base_date = datetime.now()
        
        for i in range(count):
            category = random.choice(categories)
            merchant_list = merchants.get(category, ["Generic Merchant"])
            merchant = random.choice(merchant_list)
            
            # Generate realistic amounts based on category
            amount_ranges = {
                "Food & Dining": (5, 50),
                "Shopping": (20, 500),
                "Transportation": (10, 100),
                "Bills & Utilities": (50, 300),
                "Entertainment": (10, 150),
                "Travel": (100, 2000),
                "Groceries": (30, 200),
                "Healthcare": (50, 500),
            }
            
            min_amount, max_amount = amount_ranges.get(category, (10, 100))
            amount = round(random.uniform(min_amount, max_amount), 2)
            
            # Make some transactions negative (expenses)
            if random.random() > 0.2:  # 80% expenses
                amount = -abs(amount)
            
            transaction_date = base_date - timedelta(days=random.randint(0, 30))
            
            transactions.append({
                "user_id": user_id,
                "name": merchant,
                "amount": amount,
                "category": category,
                "merchant_name": merchant,
                "date": transaction_date.isoformat(),
                "is_pending": random.random() > 0.9,  # 10% pending
            })
        
        return sorted(transactions, key=lambda x: x["date"], reverse=True)
    
    async def get_market_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent financial market news."""
        try:
            # Using Yahoo Finance news
            ticker = yf.Ticker("SPY")
            news = ticker.news[:limit]
            
            results = []
            for item in news:
                results.append({
                    "title": item.get("title", ""),
                    "publisher": item.get("publisher", ""),
                    "link": item.get("link", ""),
                    "published_at": datetime.fromtimestamp(item.get("providerPublishTime", 0)).isoformat() if item.get("providerPublishTime") else None,
                })
            
            return results
        except Exception as e:
            logger.error("Error fetching market news", error=str(e))
            return []

