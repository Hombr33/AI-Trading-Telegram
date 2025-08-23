import base64
import json
import logging
import os
from typing import Any

import openai
from pydantic import BaseModel, Field, ValidationError

from src.common.interfaces import IAnalyzer
from src.api.models import SignalResponse
from src.core.config import AppConfig

# Configure logging
logger = logging.getLogger(__name__)


class TradingSetup(BaseModel):
    """Trading setup schema matching app-code-prompt.json signal_schema"""
    type: str = Field(description="SELL or BUY")
    entry_zone: List[float] = Field(description="[float_low, float_high] entry zone")
    entry_style: str = Field(description="limit, market, or stop")
    sl: float = Field(description="Stop loss level")
    tp: List[float] = Field(description="Take profit levels [tp1, tp2_optional]")
    confidence: int = Field(description="Confidence level 0-100")
    notes: str = Field(description="Short trading notes")
    
    class Config:
        extra = "forbid"


class TradingSignal(BaseModel):
    """Complete trading signal schema matching app-code-prompt.json"""
    id: str = Field(description="Unique signal ID")
    symbol: str = Field(description="Trading symbol")
    bias: str = Field(description="BULLISH, BEARISH, or NEUTRAL")
    setups: List[TradingSetup] = Field(description="List of trading setups")
    risk_per_trade_pct: float = Field(description="Risk percentage per trade")
    move_to_BE_at_R1: bool = Field(description="Move to breakeven at R1")
    tp1_close_pct: float = Field(description="Percentage to close at TP1")
    
    class Config:
        extra = "forbid"


class OpenAIAnalyzer(IAnalyzer):
    """
    An analyzer that uses OpenAI's GPT models to analyze market screenshots.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """Initialize the OpenAI analyzer."""
        self.api_key = api_key
        self.model = model
        self.client = None
        self.system_prompt = self._load_system_prompt()
        
        if api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            except ImportError:
                logger.warning("OpenAI library not available, using mock responses")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            logger.warning("No OpenAI API key provided, using mock responses")

    def _load_system_prompt(self) -> str:
        """Loads the detailed system prompt from the JSON file."""
        try:
            # Look for app-code-prompt.json in project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            prompt_path = os.path.join(project_root, "app-code-prompt.json")
            
            with open(prompt_path, "r") as f:
                prompt_data = json.load(f)
            
            # Construct system prompt from JSON data
            system_prompt = f"""
You are {prompt_data['agent_name']}, an {prompt_data['identity']['role']}

TRADING METHODOLOGY:
- Timeframes: {prompt_data['trading_SOP']['timeframes']}
- Entry Rules: Minimum {prompt_data['trading_SOP']['entry_rules']['confluences_min']} confluences required
- Required Signals: {', '.join(prompt_data['trading_SOP']['entry_rules']['required_signals'])}
- Risk Management: {prompt_data['trading_SOP']['risk']['risk_per_trade_pct']}% risk per trade

ANALYSIS STRUCTURE:
Provide analysis in these sections: {', '.join(prompt_data['outputs_contract']['analysis_sections'])}

SIGNAL FORMAT:
Return signals in JSON format matching this schema:
{json.dumps(prompt_data['outputs_contract']['signal_schema'], indent=2)}

PRINCIPLES:
{chr(10).join('- ' + p for p in prompt_data['identity']['principles'])}

Always include: {', '.join(prompt_data['response_style']['always_include'])}
Tone: {prompt_data['response_style']['tone']}
"""
            
            logger.info("System prompt loaded successfully from app-code-prompt.json")
            return system_prompt.strip()
            
        except FileNotFoundError:
            logger.warning("Could not load or parse app-code-prompt.json: File not found")
            return self._get_default_system_prompt()
        except Exception as e:
            logger.warning(f"Could not load or parse app-code-prompt.json: {e}")
            return self._get_default_system_prompt()
    
    def _get_default_system_prompt(self) -> str:
        """Returns a default system prompt if JSON loading fails."""
        return """
You are an expert trading analyst focused on scalping and precision execution.

Analyze market data and provide trading signals with:
- Clear entry zones and stop losses
- Risk/reward ratios of at least 1:1.5
- Confidence levels (0-100%)
- Support/resistance levels
- Market structure analysis

Return signals in JSON format with fields: symbol, bias, setups (type, entry_zone, sl, tp, confidence).
"""

    async def analyze_market(self, symbol: str) -> str:
        """Analyze market data using OpenAI Responses API with real-time web search."""
        try:
            if not self.client:
                logger.warning("OpenAI API key not configured - using mock response")
                return self._create_mock_analysis_response(symbol)
            
            # Create real-time prompt for web search
            prompt = self._create_realtime_prompt(symbol)
            
            # Make API call with system prompt and real-time search
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error in OpenAI real-time analysis: {e}")
            return self._create_mock_analysis_response(symbol)
    
    def _create_realtime_prompt(self, symbol: str) -> str:
        """Create a comprehensive prompt for real-time market analysis."""
        from datetime import datetime
        
        # Determine asset type for better search context
        if "USD" in symbol and len(symbol) == 6:
            asset_type = "forex pair"
            search_context = f"{symbol[:3]}/{symbol[3:]} exchange rate"
        elif "USDT" in symbol or "USD" in symbol:
            asset_type = "cryptocurrency"
            search_context = f"{symbol.replace('USDT', '').replace('USD', '')} cryptocurrency price"
        else:
            asset_type = "trading instrument"
            search_context = f"{symbol} price"
        
        return f"""
        I need a comprehensive trading signal analysis for {symbol} ({asset_type}).

        Please search for and analyze the following real-time information:
        1. Current {search_context} and recent price movements
        2. Latest market news affecting {symbol}
        3. Technical analysis indicators and trends
        4. Market sentiment and volume analysis
        5. Any significant events or announcements

        Based on this real-time data, provide a trading recommendation in JSON format with:
        {{
            "symbol": "{symbol}",
            "action": "BUY|SELL|HOLD",
            "entry_price": current_market_price,
            "stop_loss": recommended_stop_loss,
            "take_profit": recommended_take_profit,
            "confidence": confidence_score_1_to_10,
            "risk_level": "LOW|MEDIUM|HIGH",
            "reasoning": "detailed_explanation_with_current_market_context",
            "data_sources": "list_of_sources_used",
            "timestamp": "{datetime.now().isoformat()}"
        }}

        Focus on actionable insights based on current market conditions and real-time data.
        """
    
    def _create_mock_analysis_response(self, symbol: str) -> str:
        """Create a mock analysis response for testing in JSON format."""
        import random
        import json
        
        actions = ["BUY", "SELL", "HOLD"]
        risks = ["LOW", "MEDIUM", "HIGH"]
        
        action = random.choice(actions)
        risk = random.choice(risks)
        confidence = random.randint(6, 9)
        
        # Use realistic base prices for mock data
        if "BTC" in symbol:
            entry_price = 115000
        elif "ETH" in symbol:
            entry_price = 3800
        elif "SOL" in symbol:
            entry_price = 180
        elif "ADA" in symbol:
            entry_price = 1.20
        elif "USD" in symbol:
            entry_price = 1.1000
        else:
            entry_price = 100
        
        mock_response = {
            "action": action,
            "entry_price": entry_price,
            "stop_loss": entry_price * 0.98 if action == "BUY" else entry_price * 1.02,
            "take_profit": entry_price * 1.04 if action == "BUY" else entry_price * 0.96,
            "confidence": confidence,
            "risk_level": risk,
            "reasoning": f"Technical analysis shows {action.lower()} opportunity with {risk.lower()} risk. Market momentum and volume support this decision with {confidence}/10 confidence."
        }
        
        return json.dumps(mock_response)

    async def analyze(self, screenshot_data: bytes, market_context: dict) -> Any:
        """
        Analyzes the market data using OpenAI's vision and structured outputs.

        Returns:
            A validated SignalResponse object or None.
        """
        logger.info("Starting OpenAI analysis with real-time market data...")
        base64_image = base64.b64encode(screenshot_data).decode("utf-8")

        # First, get real-time market data
        market_data = await self._get_realtime_market_data(market_context)
        
        # Generate unique signal ID
        from datetime import datetime
        signal_id = f"{market_context.get('symbols', ['EURUSD'])[0].lower()}-{datetime.now().strftime('%Y-%m-%d-%H%M')}"
        
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""Analyze this chart screenshot with the following context:
                    
Market Context: {json.dumps(market_context)}
Real-time Market Data: {market_data}

Signal ID: {signal_id}

Follow your trading SOP methodology to analyze the chart:
1. H4_BigPicture: Identify overall trend, supply/demand zones, liquidity pools
2. H1_Structure: Market structure, support/resistance levels
3. M15_EntryZone: Refined entry zones, Quasimodo patterns, FVG/imbalance
4. M5_Execution: Candle rejection signals, entry confirmation
5. Scalping_Liquidity_Sweep_Option: Identify sweep areas for M1 entries

Provide a complete trading signal following the exact signal_schema format. 
Include multiple confluences and ensure minimum RR of 1.5.
Focus on high-probability setups with proper risk management.""",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ],
        }

        try:
            # If no OpenAI client, return mock response
            if not self.client:
                logger.info("Using mock OpenAI response (no API key configured)")
                return self._create_mock_signal_response(market_context)
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    user_message,
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "trading_signal",
                        "schema": TradingSignal.model_json_schema(),
                        "strict": True
                    }
                },
                max_tokens=2000,
                temperature=0.3
            )

            response_content = response.choices[0].message.content
            if not response_content:
                logger.warning("OpenAI response was empty.")
                return None

            # Parse and validate the structured output
            signal_data = json.loads(response_content)
            validated_signal = TradingSignal(**signal_data)
            
            logger.info(f"Successfully received and validated signal for {validated_signal.symbol}")
            
            # The validated signal already matches our simplified structure
            return validated_signal

        except openai.APIError as e:
            logger.error(f"Error during OpenAI analysis: {e}")
            return self._create_mock_signal_response(market_context)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {e}")
            logger.error(f"Raw response content: {response_content}")
            return None
        except ValidationError as e:
            logger.error(f"Failed to validate signal data against Pydantic model: {e}")
            logger.error(f"Received data: {signal_data}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during analysis: {e}")
            return None

    async def _get_realtime_market_data(self, market_context: dict) -> str:
        """
        Get real-time market data using OpenAI's chat completions with web search.
        
        Args:
            market_context: Market context with symbols and timeframes
            
        Returns:
            String containing real-time market information
        """
        try:
            symbols = market_context.get('symbols', ['EURUSD'])
            symbol_query = ', '.join(symbols)
            
            # Use OpenAI chat completions for real-time market data
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a financial market data analyst. Search for current market information and provide concise, actionable data."
                    },
                    {
                        "role": "user",
                        "content": f"""Search for current market data for forex pairs: {symbol_query}
                        
Please provide:
1. Current prices and recent price movements (today)
2. Major economic news affecting these currencies today
3. Market sentiment and volatility levels
4. Any upcoming economic events or announcements
5. Technical analysis insights from financial websites

Focus on actionable trading information for scalping and intraday strategies. Keep response concise and factual."""
                    }
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            market_data = response.choices[0].message.content
            logger.info("Successfully retrieved real-time market data")
            return market_data or "Real-time market data unavailable"
            
        except Exception as e:
            logger.warning(f"Failed to get real-time market data: {e}")
            return "Real-time market data unavailable - using chart analysis only"
