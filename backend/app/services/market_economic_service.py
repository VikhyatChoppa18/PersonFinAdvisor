"""
Service to fetch real-time market and economic data for personalized financial advice.
"""
import yfinance as yf
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class MarketEconomicService:
    """Service to fetch market and economic indicators."""
    
    async def get_market_conditions(self) -> Dict[str, Any]:
        """Get current market conditions."""
        try:
            # Get major market indices
            sp500 = yf.Ticker("^GSPC")
            nasdaq = yf.Ticker("^IXIC")
            dow = yf.Ticker("^DJI")
            
            sp500_info = sp500.history(period="5d")
            nasdaq_info = nasdaq.history(period="5d")
            dow_info = dow.history(period="5d")
            
            # Calculate recent performance
            def get_performance(ticker_data):
                if len(ticker_data) >= 2:
                    current = ticker_data['Close'].iloc[-1]
                    previous = ticker_data['Close'].iloc[-2]
                    change_pct = ((current - previous) / previous) * 100
                    return {
                        "current": float(current),
                        "change_pct": float(change_pct),
                        "trend": "up" if change_pct > 0 else "down"
                    }
                return None
            
            sp500_perf = get_performance(sp500_info)
            nasdaq_perf = get_performance(nasdaq_info)
            dow_perf = get_performance(dow_info)
            
            # Get VIX (volatility index)
            vix = yf.Ticker("^VIX")
            vix_info = vix.history(period="5d")
            vix_current = float(vix_info['Close'].iloc[-1]) if len(vix_info) > 0 else None
            
            # Determine market sentiment
            market_sentiment = "neutral"
            if sp500_perf and nasdaq_perf:
                avg_change = (sp500_perf["change_pct"] + nasdaq_perf["change_pct"]) / 2
                if avg_change > 1:
                    market_sentiment = "bullish"
                elif avg_change < -1:
                    market_sentiment = "bearish"
            
            return {
                "sp500": sp500_perf,
                "nasdaq": nasdaq_perf,
                "dow": dow_perf,
                "vix": vix_current,
                "sentiment": market_sentiment,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Error fetching market conditions", error=str(e))
            return {
                "sentiment": "neutral",
                "error": str(e)
            }
    
    async def get_economic_indicators(self) -> Dict[str, Any]:
        """Get economic indicators."""
        try:
            # Get Treasury yields (10-year, 2-year)
            tnx = yf.Ticker("^TNX")  # 10-year Treasury
            irx = yf.Ticker("^IRX")  # 13-week Treasury
            
            tnx_info = tnx.history(period="5d")
            irx_info = irx.history(period="5d")
            
            treasury_10y = float(tnx_info['Close'].iloc[-1]) if len(tnx_info) > 0 else None
            treasury_3m = float(irx_info['Close'].iloc[-1]) if len(irx_info) > 0 else None
            
            # Yield curve inversion check (bearish signal)
            yield_curve_inverted = False
            if treasury_10y and treasury_3m and treasury_3m > treasury_10y:
                yield_curve_inverted = True
            
            # Get gold price (safe haven asset)
            gold = yf.Ticker("GC=F")
            gold_info = gold.history(period="5d")
            gold_price = float(gold_info['Close'].iloc[-1]) if len(gold_info) > 0 else None
            
            # Get USD strength (DXY)
            dxy = yf.Ticker("DX-Y.NYB")
            dxy_info = dxy.history(period="5d")
            usd_index = float(dxy_info['Close'].iloc[-1]) if len(dxy_info) > 0 else None
            
            # Get oil price
            oil = yf.Ticker("CL=F")
            oil_info = oil.history(period="5d")
            oil_price = float(oil_info['Close'].iloc[-1]) if len(oil_info) > 0 else None
            
            return {
                "treasury_10y": treasury_10y,
                "treasury_3m": treasury_3m,
                "yield_curve_inverted": yield_curve_inverted,
                "gold_price": gold_price,
                "usd_index": usd_index,
                "oil_price": oil_price,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error("Error fetching economic indicators", error=str(e))
            return {
                "error": str(e)
            }
    
    async def get_inflation_data(self) -> Dict[str, Any]:
        """Get inflation indicators (using TIPS as proxy)."""
        try:
            # TIPS (Treasury Inflation-Protected Securities) indicate inflation expectations
            tips = yf.Ticker("TIP")
            tips_info = tips.history(period="30d")
            
            if len(tips_info) > 0:
                tips_current = float(tips_info['Close'].iloc[-1])
                tips_30d_ago = float(tips_info['Close'].iloc[0])
                tips_change = ((tips_current - tips_30d_ago) / tips_30d_ago) * 100
                
                return {
                    "tips_price": tips_current,
                    "tips_change_30d": tips_change,
                    "inflation_expectation": "high" if tips_change > 2 else "moderate" if tips_change > 0 else "low"
                }
        except Exception as e:
            logger.error("Error fetching inflation data", error=str(e))
        
        return {
            "inflation_expectation": "moderate"
        }
    
    async def get_comprehensive_market_context(self) -> Dict[str, Any]:
        """Get comprehensive market and economic context."""
        market = await self.get_market_conditions()
        economic = await self.get_economic_indicators()
        inflation = await self.get_inflation_data()
        
        # Generate market summary
        market_summary = []
        
        if market.get("sentiment") == "bullish":
            market_summary.append("Markets are showing positive momentum")
        elif market.get("sentiment") == "bearish":
            market_summary.append("Markets are showing negative momentum")
        
        if economic.get("yield_curve_inverted"):
            market_summary.append("⚠️ Yield curve is inverted (potential recession indicator)")
        
        if market.get("vix"):
            if market["vix"] > 20:
                market_summary.append("High volatility (VIX > 20) - markets are uncertain")
            elif market["vix"] < 15:
                market_summary.append("Low volatility (VIX < 15) - markets are relatively calm")
        
        if inflation.get("inflation_expectation") == "high":
            market_summary.append("Inflation expectations are elevated")
        
        return {
            "market": market,
            "economic": economic,
            "inflation": inflation,
            "summary": market_summary,
            "timestamp": datetime.now().isoformat()
        }

