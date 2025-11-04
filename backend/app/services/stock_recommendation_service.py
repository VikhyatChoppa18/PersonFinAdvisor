"""
Service for stock recommendations using Alpha Vantage and market analysis.
"""
import requests
import yfinance as yf
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class StockRecommendationService:
    """Service for providing stock recommendations based on market conditions."""
    
    def __init__(self, alpha_vantage_api_key: Optional[str] = None):
        """Initialize stock recommendation service."""
        self.alpha_vantage_api_key = alpha_vantage_api_key
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
    
    async def get_stock_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Get stock fundamentals from Alpha Vantage."""
        if not self.alpha_vantage_api_key:
            return {}
        
        try:
            params = {
                "function": "OVERVIEW",
                "symbol": symbol,
                "apikey": self.alpha_vantage_api_key
            }
            
            response = requests.get(self.alpha_vantage_base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "Error Message" not in data and "Note" not in data:
                    return {
                        "symbol": symbol,
                        "name": data.get("Name", ""),
                        "sector": data.get("Sector", ""),
                        "industry": data.get("Industry", ""),
                        "pe_ratio": data.get("PERatio", ""),
                        "market_cap": data.get("MarketCapitalization", ""),
                        "dividend_yield": data.get("DividendYield", ""),
                        "eps": data.get("EPS", ""),
                        "52_week_high": data.get("52WeekHigh", ""),
                        "52_week_low": data.get("52WeekLow", ""),
                        "beta": data.get("Beta", ""),
                        "profit_margin": data.get("ProfitMargin", ""),
                    }
        except Exception as e:
            logger.error("Error fetching Alpha Vantage data", symbol=symbol, error=str(e))
        
        return {}
    
    async def get_stock_technical_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get technical analysis from Alpha Vantage."""
        if not self.alpha_vantage_api_key:
            return {}
        
        try:
            # Get RSI (Relative Strength Index)
            params = {
                "function": "RSI",
                "symbol": symbol,
                "interval": "daily",
                "time_period": 14,
                "series_type": "close",
                "apikey": self.alpha_vantage_api_key
            }
            
            response = requests.get(self.alpha_vantage_base_url, params=params, timeout=10)
            rsi_data = {}
            if response.status_code == 200:
                data = response.json()
                if "Technical Analysis: RSI" in data:
                    rsi_series = data["Technical Analysis: RSI"]
                    if rsi_series:
                        latest_date = max(rsi_series.keys())
                        rsi_data = {
                            "rsi": float(rsi_series[latest_date].get("RSI", 0)),
                            "date": latest_date
                        }
        except Exception as e:
            logger.error("Error fetching RSI", symbol=symbol, error=str(e))
        
        return rsi_data
    
    async def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """Analyze a stock using Alpha Vantage and yfinance."""
        try:
            # Get data from yfinance (free, no API key needed)
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get recent price history
            hist = ticker.history(period="1y")
            
            if hist.empty:
                return {"error": f"Could not fetch data for {symbol}"}
            
            current_price = hist['Close'].iloc[-1]
            price_52w_ago = hist['Close'].iloc[0] if len(hist) > 250 else current_price
            
            # Calculate metrics
            price_change_52w = ((current_price - price_52w_ago) / price_52w_ago * 100) if price_52w_ago > 0 else 0
            
            # Get Alpha Vantage data if available
            fundamentals = await self.get_stock_fundamentals(symbol)
            technical = await self.get_stock_technical_analysis(symbol)
            
            # Determine recommendation
            recommendation = "HOLD"
            reasons = []
            
            # Technical analysis
            if technical.get("rsi"):
                rsi = technical["rsi"]
                if rsi < 30:
                    recommendation = "BUY"
                    reasons.append("Oversold (RSI < 30) - potential buying opportunity")
                elif rsi > 70:
                    recommendation = "SELL"
                    reasons.append("Overbought (RSI > 70) - consider taking profits")
            
            # Price momentum
            if price_change_52w > 20:
                reasons.append(f"Strong 52-week performance (+{price_change_52w:.1f}%)")
                if recommendation == "HOLD":
                    recommendation = "BUY"
            elif price_change_52w < -20:
                reasons.append(f"Weak 52-week performance ({price_change_52w:.1f}%)")
                if recommendation == "HOLD":
                    recommendation = "SELL"
            
            # Fundamental analysis
            if fundamentals.get("pe_ratio"):
                try:
                    pe = float(fundamentals["pe_ratio"])
                    if pe < 15:
                        reasons.append("Low P/E ratio - potentially undervalued")
                        if recommendation == "HOLD":
                            recommendation = "BUY"
                    elif pe > 25:
                        reasons.append("High P/E ratio - may be overvalued")
                except:
                    pass
            
            if fundamentals.get("dividend_yield"):
                try:
                    div_yield = float(fundamentals["dividend_yield"].rstrip('%'))
                    if div_yield > 3:
                        reasons.append(f"Good dividend yield ({div_yield:.2f}%)")
                except:
                    pass
            
            return {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "current_price": round(current_price, 2),
                "price_change_52w": round(price_change_52w, 2),
                "recommendation": recommendation,
                "reasons": reasons,
                "fundamentals": fundamentals,
                "technical": technical,
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
            }
        except Exception as e:
            logger.error("Error analyzing stock", symbol=symbol, error=str(e))
            return {"error": str(e)}
    
    async def get_recommended_stocks(
        self, 
        market_context: Dict[str, Any],
        risk_tolerance: str = "moderate",
        investment_amount: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get stock recommendations based on market conditions and user profile."""
        
        # Popular stocks across different sectors
        stock_universe = [
            # Tech
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
            # Finance
            "JPM", "BAC", "WFC", "GS", "MS",
            # Healthcare
            "JNJ", "PFE", "UNH", "ABBV", "TMO",
            # Consumer
            "WMT", "HD", "MCD", "NKE", "SBUX",
            # Industrial
            "BA", "CAT", "GE", "HON",
            # Energy
            "XOM", "CVX", "COP",
            # ETFs (diversified)
            "SPY", "QQQ", "VTI", "VOO"
        ]
        
        # Filter based on market conditions
        market_sentiment = market_context.get('market', {}).get('sentiment', 'neutral')
        volatility = market_context.get('market', {}).get('vix', 0)
        yield_curve_inverted = market_context.get('economic', {}).get('yield_curve_inverted', False)
        
        # Adjust recommendations based on market conditions
        if yield_curve_inverted or volatility > 25:
            # Defensive stocks and ETFs
            recommended_symbols = ["SPY", "VTI", "JNJ", "WMT", "PG", "KO", "PEP"]
        elif market_sentiment == "bearish" or volatility > 20:
            # Mix of defensive and growth
            recommended_symbols = ["SPY", "QQQ", "MSFT", "AAPL", "JNJ", "VTI"]
        elif market_sentiment == "bullish":
            # Growth stocks
            recommended_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META"]
        else:
            # Balanced portfolio
            recommended_symbols = ["SPY", "VTI", "AAPL", "MSFT", "JPM", "JNJ"]
        
        # Limit to top 10
        recommended_symbols = recommended_symbols[:10]
        
        # Analyze each stock
        recommendations = []
        for symbol in recommended_symbols:
            try:
                analysis = await self.analyze_stock(symbol)
                if "error" not in analysis:
                    # Add market context to recommendation
                    analysis["market_context"] = {
                        "current_sentiment": market_sentiment,
                        "volatility": "high" if volatility > 20 else "low",
                        "why_recommended": self._get_recommendation_reason(symbol, market_context, risk_tolerance)
                    }
                    recommendations.append(analysis)
            except Exception as e:
                logger.error("Error analyzing stock for recommendation", symbol=symbol, error=str(e))
                continue
        
        # Sort by recommendation strength
        recommendation_order = {"BUY": 3, "HOLD": 2, "SELL": 1}
        recommendations.sort(
            key=lambda x: (
                recommendation_order.get(x.get("recommendation", "HOLD"), 2),
                -len(x.get("reasons", []))
            ),
            reverse=True
        )
        
        return recommendations[:8]  # Return top 8 recommendations
    
    def _get_recommendation_reason(
        self, 
        symbol: str, 
        market_context: Dict[str, Any],
        risk_tolerance: str
    ) -> str:
        """Get reason why this stock is recommended in current market conditions."""
        reasons = []
        
        market_sentiment = market_context.get('market', {}).get('sentiment', 'neutral')
        volatility = market_context.get('market', {}).get('vix', 0)
        yield_curve_inverted = market_context.get('economic', {}).get('yield_curve_inverted', False)
        
        # ETF reasons
        if symbol in ["SPY", "VTI", "VOO", "QQQ"]:
            if yield_curve_inverted:
                reasons.append("Diversified ETF provides protection during uncertain times")
            elif volatility > 20:
                reasons.append("Broad market exposure reduces individual stock risk")
            else:
                reasons.append("Diversified exposure to entire market")
        
        # Tech stock reasons
        elif symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]:
            if market_sentiment == "bullish":
                reasons.append("Strong growth potential in bullish market")
            elif volatility > 20:
                reasons.append("Large-cap tech provides stability during volatility")
            else:
                reasons.append("Solid fundamentals and growth prospects")
        
        # Defensive stock reasons
        elif symbol in ["JNJ", "WMT", "PG", "KO"]:
            if yield_curve_inverted or volatility > 25:
                reasons.append("Defensive sector provides stability during economic uncertainty")
            else:
                reasons.append("Stable dividends and consistent performance")
        
        # Financial stock reasons
        elif symbol in ["JPM", "BAC", "GS"]:
            interest_rate = market_context.get('economic', {}).get('treasury_10y', 0)
            if interest_rate > 4:
                reasons.append("Benefit from rising interest rates")
            else:
                reasons.append("Strong financial position")
        
        if not reasons:
            reasons.append("Well-positioned for current market conditions")
        
        return "; ".join(reasons)
    
    async def get_stock_screener(
        self,
        criteria: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Screen stocks based on criteria."""
        # This would use Alpha Vantage's screener if available
        # For now, use our analysis method
        sectors = criteria.get("sectors", [])
        min_market_cap = criteria.get("min_market_cap", 0)
        max_pe = criteria.get("max_pe", 50)
        
        # Filter stocks based on criteria
        all_stocks = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
            "JPM", "BAC", "WFC", "GS", "MS",
            "JNJ", "PFE", "UNH", "ABBV",
            "WMT", "HD", "MCD", "NKE"
        ]
        
        recommendations = []
        for symbol in all_stocks:
            analysis = await self.analyze_stock(symbol)
            if "error" not in analysis:
                # Apply filters
                if sectors and analysis.get("sector") not in sectors:
                    continue
                if min_market_cap > 0 and analysis.get("market_cap", 0) < min_market_cap:
                    continue
                
                recommendations.append(analysis)
        
        return recommendations[:10]

