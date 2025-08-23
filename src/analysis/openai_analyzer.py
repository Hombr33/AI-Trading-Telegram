import base64
import json
import logging
import os
from typing import Any, List, Optional, Union

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

    def __init__(self, config: AppConfig):
        """Initialize the OpenAI analyzer with configuration."""
        self.api_key = config.openai.api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not configured.")
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Loads the detailed system prompt from the JSON file."""
        try:
            # Get the root directory (project root)
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            prompt_path = os.path.join(root_dir, "app-code-prompt.json")
            
            with open(prompt_path, "r") as f:
                prompt_data = json.load(f)
            
            # Convert the JSON prompt data into a comprehensive system message
            system_message = f"""
You are {prompt_data['agent_name']}, an {prompt_data['identity']['role']}

IDENTITY & PRINCIPLES:
{json.dumps(prompt_data['identity'], indent=2)}

TRADING METHODOLOGY:
{json.dumps(prompt_data['trading_SOP'], indent=2)}

OUTPUT CONTRACT:
{json.dumps(prompt_data['outputs_contract'], indent=2)}

AUTOMATION AWARENESS:
{json.dumps(prompt_data['automation_awareness'], indent=2)}

RESPONSE STYLE:
{json.dumps(prompt_data['response_style'], indent=2)}

CONSTRAINTS:
{json.dumps(prompt_data['constraints'], indent=2)}

MACHINE READABLE SIGNAL EXAMPLE:
{json.dumps(prompt_data['machine_readable_signal_example'], indent=2)}

You must analyze market screenshots and provide trading signals following the exact signal_schema format specified in outputs_contract.
Always include real-time market context and follow the trading SOP methodology.
"""
            return system_message
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Could not load or parse app-code-prompt.json: {e}")
            # Fallback to a simple instruction if the file is missing/corrupt
            return "You are a financial market analyst. Analyze the provided image and return a trading signal in JSON format."

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
            logger.error(f"OpenAI API error: {e}")
            return None
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
