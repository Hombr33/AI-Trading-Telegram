"""
Real-time data provider module for OpenAI analyzer.
Handles fetching current market data using OpenAI's function calling capabilities.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RealtimeDataProvider:
    """Provides real-time market data for analysis."""
    
    def __init__(self, openai_client=None):
        """Initialize real-time data provider.
        
        Args:
            openai_client: OpenAI async client instance
        """
        self.client = openai_client
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Get OpenAI function definitions for real-time data access.
        
        Returns:
            List of function definitions for OpenAI function calling
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_current_market_data",
                    "description": "Get current market data for trading symbols including prices, news, and sentiment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbols": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of trading symbols (e.g., EURUSD, XAUUSD, BTCUSDT)"
                            },
                            "data_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Types of data to fetch: prices, news, sentiment, events"
                            }
                        },
                        "required": ["symbols"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "get_economic_calendar",
                    "description": "Get upcoming economic events and news that may impact trading",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "timeframe": {
                                "type": "string",
                                "enum": ["today", "week", "month"],
                                "description": "Timeframe for economic events"
                            },
                            "impact_level": {
                                "type": "string",
                                "enum": ["high", "medium", "low", "all"],
                                "description": "Filter by impact level"
                            }
                        },
                        "required": ["timeframe"]
                    }
                }
            }
        ]
    
    async def get_current_market_data(self, symbols: List[str], 
                                    data_types: Optional[List[str]] = None) -> str:
        """Get current market data for specified symbols.
        
        Args:
            symbols: List of trading symbols
            data_types: Types of data to fetch
            
        Returns:
            Formatted market data string
        """
        if not self.client:
            return self._get_mock_market_data(symbols)
        
        # Check cache first
        cache_key = f"market_data_{'-'.join(symbols)}"
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached market data for {symbols}")
            return self.cache[cache_key]['data']
        
        try:
            # Use OpenAI to search for real-time data
            data_types_str = ", ".join(data_types or ["prices", "news", "sentiment"])
            symbols_str = ", ".join(symbols)
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial data analyst. Search for current market information and provide concise, actionable data."
                    },
                    {
                        "role": "user", 
                        "content": f"""Search for current market data for: {symbols_str}

Data types needed: {data_types_str}

Please provide:
1. Current prices and recent price movements (last 24 hours)
2. Major economic news affecting these instruments today
3. Market sentiment and volatility levels  
4. Any upcoming economic events or announcements
5. Technical analysis insights from financial websites

Format the response as structured data with specific price levels and timeframes.
Current time: {datetime.now().isoformat()}"""
                    }
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            market_data = response.choices[0].message.content
            
            # Cache the result
            self.cache[cache_key] = {
                'data': market_data,
                'timestamp': datetime.now().timestamp()
            }
            
            logger.info(f"Successfully fetched real-time market data for {symbols}")
            return market_data or "Real-time market data unavailable"
            
        except Exception as e:
            logger.warning(f"Failed to fetch real-time market data: {e}")
            return self._get_mock_market_data(symbols)
    
    async def get_economic_calendar(self, timeframe: str = "today", 
                                  impact_level: str = "high") -> str:
        """Get economic calendar events.
        
        Args:
            timeframe: Timeframe for events (today, week, month)
            impact_level: Impact level filter (high, medium, low, all)
            
        Returns:
            Formatted economic calendar data
        """
        if not self.client:
            return self._get_mock_economic_calendar(timeframe, impact_level)
        
        cache_key = f"economic_calendar_{timeframe}_{impact_level}"
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached economic calendar for {timeframe}")
            return self.cache[cache_key]['data']
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial calendar analyst. Provide current economic events and their market impact."
                    },
                    {
                        "role": "user",
                        "content": f"""Search for economic calendar events for: {timeframe}
Impact level: {impact_level}

Please provide:
1. Upcoming economic releases and announcements
2. Central bank meetings and policy decisions
3. Key economic indicators (GDP, inflation, employment)
4. Market-moving events and their expected impact
5. Specific times and dates in UTC

Focus on events that could impact forex, commodities, and crypto markets.
Current time: {datetime.now().isoformat()}"""
                    }
                ],
                max_tokens=600,
                temperature=0.3
            )
            
            calendar_data = response.choices[0].message.content
            
            # Cache the result
            self.cache[cache_key] = {
                'data': calendar_data,
                'timestamp': datetime.now().timestamp()
            }
            
            logger.info(f"Successfully fetched economic calendar for {timeframe}")
            return calendar_data or "Economic calendar data unavailable"
            
        except Exception as e:
            logger.warning(f"Failed to fetch economic calendar: {e}")
            return self._get_mock_economic_calendar(timeframe, impact_level)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid.
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            True if cache is valid, False otherwise
        """
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key]['timestamp']
        current_time = datetime.now().timestamp()
        
        return (current_time - cached_time) < self.cache_ttl
    
    def _get_mock_market_data(self, symbols: List[str]) -> str:
        """Get mock market data for testing.
        
        Args:
            symbols: List of trading symbols
            
        Returns:
            Mock market data string
        """
        mock_data = []
        mock_data.append("=== MOCK MARKET DATA ===")
        
        for symbol in symbols:
            if "USD" in symbol and len(symbol) == 6:
                # Forex pair
                mock_data.append(f"{symbol}: 1.1000 (+0.0050, +0.45%)")
                mock_data.append(f"- 24h Range: 1.0950 - 1.1050")
                mock_data.append(f"- Volatility: Medium")
                mock_data.append(f"- Trend: Bullish short-term")
            elif "XAU" in symbol:
                # Gold
                mock_data.append(f"{symbol}: $2650.00 (+15.50, +0.59%)")
                mock_data.append(f"- 24h Range: $2635.00 - $2665.00")
                mock_data.append(f"- Volatility: High")
                mock_data.append(f"- Trend: Consolidation")
            elif "BTC" in symbol or "ETH" in symbol:
                # Crypto
                price = 95000 if "BTC" in symbol else 3500
                mock_data.append(f"{symbol}: ${price:.2f} (+2.5%)")
                mock_data.append(f"- 24h Volume: High")
                mock_data.append(f"- Volatility: Very High")
        
        mock_data.append(f"\nMarket Session: {'London' if 7 <= datetime.now().hour <= 16 else 'Asian'}")
        mock_data.append("News: No major events scheduled")
        mock_data.append("Sentiment: Neutral to Bullish")
        
        return "\n".join(mock_data)
    
    def _get_mock_economic_calendar(self, timeframe: str, impact_level: str) -> str:
        """Get mock economic calendar for testing.
        
        Args:
            timeframe: Timeframe for events
            impact_level: Impact level filter
            
        Returns:
            Mock economic calendar string
        """
        mock_events = []
        mock_events.append("=== MOCK ECONOMIC CALENDAR ===")
        
        if impact_level in ["high", "all"]:
            mock_events.append("HIGH IMPACT EVENTS:")
            mock_events.append("- US Non-Farm Payrolls (15:30 UTC)")
            mock_events.append("- ECB Interest Rate Decision (13:45 UTC)")
            mock_events.append("- Fed Chair Speech (18:00 UTC)")
        
        if impact_level in ["medium", "all"]:
            mock_events.append("MEDIUM IMPACT EVENTS:")
            mock_events.append("- US Retail Sales (13:30 UTC)")
            mock_events.append("- German IFO Business Climate (09:00 UTC)")
        
        mock_events.append(f"\nTimeframe: {timeframe}")
        mock_events.append("Market Impact: Moderate to High volatility expected")
        
        return "\n".join(mock_events)
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        logger.info("Cleared real-time data cache")
    
    def set_cache_ttl(self, seconds: int):
        """Set cache time-to-live in seconds.
        
        Args:
            seconds: Cache TTL in seconds
        """
        self.cache_ttl = seconds
        logger.info(f"Set cache TTL to {seconds} seconds")
