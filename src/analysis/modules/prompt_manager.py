"""
Prompt management module for OpenAI analyzer.
Handles system prompts, context loading, and prompt formatting.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages system prompts and context for OpenAI analysis."""

    def __init__(self, prompt_config_path: Optional[str] = None):
        """Initialize prompt manager.

        Args:
            prompt_config_path: Path to app-code-prompt.json file
        """
        self.prompt_config_path = prompt_config_path or self._get_default_config_path()
        self.prompt_config = self._load_prompt_config()
        self.system_prompt = self._build_system_prompt()

    def _get_default_config_path(self) -> str:
        """Get default path to app-code-prompt.json."""
        project_root = Path(__file__).parent.parent.parent.parent
        return str(project_root / "app-code-prompt.json")

    def _load_prompt_config(self) -> Dict[str, Any]:
        """Load configuration from app-code-prompt.json."""
        try:
            with open(self.prompt_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(
                f"Successfully loaded prompt config from {self.prompt_config_path}"
            )
            return config
        except FileNotFoundError:
            logger.error(f"Prompt config file not found: {self.prompt_config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in prompt config: {e}")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading prompt config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if loading fails."""
        return {
            "agent_name": "GPT-5 Trading Scalper AI",
            "identity": {
                "role": "Institutional-grade trading assistant",
                "principles": [
                    "Capital preservation first",
                    "Evidence-based analysis",
                    "Retail-feasible execution",
                ],
            },
            "trading_SOP": {
                "timeframes": {
                    "bias": ["H4", "H1"],
                    "setup": ["M15", "M5"],
                    "execution": ["M1"],
                },
                "entry_rules": {
                    "confluences_min": 3,
                    "required_signals": [
                        "Liquidity sweep or inducement",
                        "Candle rejection on M15/M5",
                        "Structure confirmation",
                    ],
                },
                "risk": {"risk_per_trade_pct": 2.0},
            },
            "outputs_contract": {
                "analysis_sections": [
                    "H4_BigPicture",
                    "H1_Structure",
                    "M15_EntryZone",
                    "M5_Execution",
                    "Trading_Plan",
                ],
                "signal_schema": {
                    "id": "string - unique signal identifier",
                    "symbol": "string - trading symbol",
                    "bias": "BULLISH|BEARISH|NEUTRAL",
                    "setups": [
                        {
                            "type": "BUY|SELL",
                            "entry_zone": "array of entry prices [min, max]",
                            "entry_style": "limit|market|stop",
                            "sl": "number - stop loss price",
                            "tp": "array of take profit levels",
                            "confidence": "number 0-100",
                            "notes": "string - setup notes",
                        }
                    ],
                    "risk_per_trade_pct": "number - risk percentage per trade",
                    "move_to_BE_at_R1": "boolean - move to breakeven at first target",
                    "tp1_close_pct": "number - percentage to close at first target (0.0-1.0)",
                },
            },
        }

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt from config."""
        config = self.prompt_config

        # Build the system prompt sections
        sections = []

        # Identity section
        sections.append(f"You are {config.get('agent_name', 'Trading AI Assistant')}")
        sections.append(
            f"Role: {config.get('identity', {}).get('role', 'Trading assistant')}"
        )

        # Principles section
        principles = config.get("identity", {}).get("principles", [])
        if principles:
            sections.append("\nCore Principles:")
            for principle in principles:
                sections.append(f"- {principle}")

        # Trading methodology section
        trading_sop = config.get("trading_SOP", {})
        if trading_sop:
            sections.append("\nTrading Methodology:")

            # Timeframes
            timeframes = trading_sop.get("timeframes", {})
            if timeframes:
                sections.append("Timeframes:")
                for tf_type, tfs in timeframes.items():
                    sections.append(f"- {tf_type.title()}: {', '.join(tfs)}")

            # Entry rules
            entry_rules = trading_sop.get("entry_rules", {})
            if entry_rules:
                sections.append("Entry Requirements:")
                sections.append(
                    f"- Minimum {entry_rules.get('confluences_min', 3)} confluences"
                )
                required_signals = entry_rules.get("required_signals", [])
                for signal in required_signals:
                    sections.append(f"- {signal}")

                rr_min = entry_rules.get("rr_min", 1.5)
                sections.append(f"- Minimum Risk:Reward ratio of {rr_min}:1")

            # Risk management
            risk = trading_sop.get("risk", {})
            if risk:
                sections.append("Risk Management:")
                sections.append(
                    f"- Risk per trade: {risk.get('risk_per_trade_pct', 2.0)}%"
                )
                sections.append(
                    f"- Max daily drawdown: {risk.get('max_daily_drawdown_pct', 6.0)}%"
                )

        # Analysis structure section
        outputs = config.get("outputs_contract", {})
        analysis_sections = outputs.get("analysis_sections", [])
        if analysis_sections:
            sections.append("\nAnalysis Structure:")
            sections.append("Provide analysis in these sections:")
            for section in analysis_sections:
                sections.append(f"- {section}")

        # Signal format section
        signal_schema = outputs.get("signal_schema", {})
        if signal_schema:
            sections.append("\nSignal Format:")
            sections.append(
                "IMPORTANT: Return ONLY valid JSON matching this exact schema. Do not include markdown formatting, explanations, or additional text."
            )
            sections.append("Required JSON structure:")
            sections.append(json.dumps(signal_schema, indent=2))
            sections.append("\nRequired field guidelines:")
            sections.append("- id: Generate unique ID like 'symbol-YYYY-MM-DD-HHMM'")
            sections.append("- symbol: Use exact trading symbol provided")
            sections.append("- bias: Must be 'BULLISH', 'BEARISH', or 'NEUTRAL'")
            sections.append("- setups: Array with at least one setup")
            sections.append("- risk_per_trade_pct: Use 2.0 (represents 2%)")
            sections.append("- move_to_BE_at_R1: Use true or false")
            sections.append("- tp1_close_pct: Use 0.5 (represents 50%)")
            sections.append("\nSetup guidelines:")
            sections.append("- type: Must be 'BUY' or 'SELL'")
            sections.append(
                "- entry_zone: [min_price, max_price] with realistic spread"
            )
            sections.append("- entry_style: Use 'limit', 'market', or 'stop'")
            sections.append("- sl: Stop loss price (ensure reasonable distance)")
            sections.append("- tp: Array of take profit levels [tp1, tp2]")
            sections.append("- confidence: Integer 0-100")
            sections.append("- notes: Brief explanation of setup")
            sections.append("\nPrice scaling guidelines:")
            sections.append(
                "- Forex majors (EUR/USD, GBP/USD): Use 4-5 decimal places, 5-20 pip spreads"
            )
            sections.append(
                "- Forex exotics (USD/RUB, USD/TRY): Use 2-4 decimal places, 50-200 pip spreads"
            )
            sections.append("- JPY pairs: Use 2-3 decimal places, 5-20 pip spreads")
            sections.append(
                "- Metals (XAU/USD, XAG/USD): Use 2 decimal places, $1-$10 spreads"
            )
            sections.append(
                "- Crypto: Use appropriate decimal places for the specific pair"
            )
            sections.append("\nValidation requirements:")
            sections.append("- Entry zone spread: Maximum 50 pips for forex")
            sections.append("- Stop loss distance: 10-500 pips from entry")
            sections.append("- Risk-reward ratio: Minimum 1.5:1")
            sections.append("- Confidence: 60-100 for valid signals")

        # Response style
        response_style = config.get("response_style", {})
        if response_style:
            sections.append("\nResponse Guidelines:")
            always_include = response_style.get("always_include", [])
            if always_include:
                sections.append(f"Always include: {', '.join(always_include)}")

            tone = response_style.get("tone", "")
            if tone:
                sections.append(f"Tone: {tone}")

        return "\n".join(sections)

    def get_system_prompt(self) -> str:
        """Get the system prompt for OpenAI analysis.

        Returns:
            System prompt string
        """
        return self.system_prompt

    def get_signal_schema(self) -> Dict[str, Any]:
        """Get the signal schema from the configuration.

        Returns:
            Signal schema dictionary
        """
        try:
            outputs = self.prompt_config.get("outputs_contract", {})
            signal_schema = outputs.get("signal_schema", {})
            return signal_schema
        except Exception as e:
            logger.error(f"Error getting signal schema: {e}")
            return {}

    def create_analysis_prompt(
        self, market_context: Dict[str, Any], realtime_data: Optional[str] = None
    ) -> str:
        """Create analysis prompt with market context and real-time data.

        Args:
            market_context: Market context dictionary
            realtime_data: Optional real-time market data

        Returns:
            Formatted analysis prompt
        """
        prompt_parts = []

        # Get symbol from market context
        symbols = market_context.get("symbols", ["UNKNOWN"])
        symbol = symbols[0] if symbols else "UNKNOWN"
        signal_id = f"{symbol.lower()}-{datetime.now().strftime('%Y-%m-%d-%H%M')}"

        # CRITICAL: JSON Schema Requirements
        prompt_parts.append(
            "🚨 CRITICAL: Generate a complete trading signal with ALL required fields."
        )
        prompt_parts.append(
            "You MUST include every field below. Missing fields cause validation failure."
        )
        prompt_parts.append("")
        prompt_parts.append("Required JSON Structure (EXACT FORMAT REQUIRED):")
        prompt_parts.append(
            f"""{{
    "id": "{signal_id}",
    "symbol": "{symbol}",
    "bias": "BULLISH|BEARISH|NEUTRAL",
    "risk_per_trade_pct": 2.0,
    "move_to_BE_at_R1": true,
    "tp1_close_pct": 0.5,
    "setups": [
        {{
            "type": "BUY|SELL",
            "entry_zone": [entry_low, entry_high],
            "entry_style": "limit",
            "sl": stop_loss_price,
            "tp": [tp1_price, tp2_price],
            "confidence": 60-100,
            "notes": "Brief setup explanation"
        }}
    ]
}}"""
        )

        # Real-time data if available
        if realtime_data:
            prompt_parts.append("\nReal-time Market Data:")
            prompt_parts.append(realtime_data)

        # Analysis instructions
        prompt_parts.append("\nAnalysis Instructions:")
        prompt_parts.append("1. Use the real-time market data provided above")
        prompt_parts.append(
            "2. Follow the multi-timeframe approach (H4 → H1 → M15 → M5 → M1)"
        )
        prompt_parts.append(
            "3. Identify all required confluences before providing signals"
        )
        prompt_parts.append(
            "4. Generate signals in the EXACT JSON format specified above"
        )
        prompt_parts.append(
            "5. Include confidence scores and risk management parameters"
        )
        prompt_parts.append(
            "6. Return ONLY the JSON object - no additional text, no markdown, no explanations"
        )
        prompt_parts.append(
            "7. Ensure all validation requirements are met before generating signal"
        )
        prompt_parts.append(
            "8. If no valid setup exists, return NEUTRAL bias with confidence 0"
        )
        prompt_parts.append(
            "9. Use realistic price levels based on the current market data"
        )

        # Price level requirements
        prompt_parts.append("\n💰 PRICE LEVEL REQUIREMENTS:")
        prompt_parts.append("- Use realistic price levels based on current market data")
        prompt_parts.append("- For BTCUSDT: Use prices around current market price")
        prompt_parts.append(
            "- Entry zones should be small (e.g., 100-500 points for crypto)"
        )
        prompt_parts.append("- Stop loss should be reasonable (e.g., 200-1000 points)")
        prompt_parts.append(
            "- Take profit should be achievable (e.g., 300-1500 points)"
        )
        prompt_parts.append("- All prices must be realistic and tradeable")

        # Risk-reward requirements
        prompt_parts.append("\n⚖️ RISK-REWARD REQUIREMENTS:")
        prompt_parts.append("- Minimum risk-reward ratio: 1.5:1")
        prompt_parts.append("- Target risk-reward ratio: 2.0:1 or higher")
        prompt_parts.append(
            "- Calculate: (TP1 distance from entry) / (SL distance from entry)"
        )
        prompt_parts.append(
            "- Example: If SL is 500 points away, TP1 should be at least 750 points away"
        )
        prompt_parts.append("- Ensure TP1 provides at least 1.5x the risk")

        # JSON formatting requirements
        prompt_parts.append("\n🚨 JSON FORMATTING REQUIREMENTS:")
        prompt_parts.append("- NO markdown formatting")
        prompt_parts.append("- NO code blocks")
        prompt_parts.append("- NO additional text before or after")
        prompt_parts.append("- ONLY the raw JSON object")
        prompt_parts.append("- Ensure all quotes are properly escaped")
        prompt_parts.append("- Use proper JSON syntax with no trailing commas")
        prompt_parts.append(
            "- Use realistic decimal places (e.g., 114000.50, not 114000.00)"
        )

        # Current timestamp for context
        prompt_parts.append(f"\nCurrent Time: {datetime.now().isoformat()}")

        return "\n".join(prompt_parts)

    def create_realtime_search_prompt(self, symbols: list) -> str:
        """Create prompt for real-time market data search.

        Args:
            symbols: List of trading symbols to search for

        Returns:
            Formatted search prompt
        """
        symbol_list = ", ".join(symbols)

        prompt = f"""Search for current market information for: {symbol_list}

Please provide:
1. Current prices and recent price movements (last 24 hours)
2. Major economic news affecting these instruments today
3. Market sentiment and volatility levels
4. Any upcoming economic events or announcements
5. Technical analysis insights from financial websites

Focus on actionable trading information for scalping and intraday strategies.
Keep response concise and factual.
Include specific price levels and timeframes where possible.

Current time: {datetime.now().isoformat()}"""

        return prompt

    def get_config(self) -> Dict[str, Any]:
        """Get the loaded prompt configuration."""
        return self.prompt_config

    def reload_config(self) -> bool:
        """Reload configuration from file.

        Returns:
            True if reload was successful, False otherwise
        """
        try:
            self.prompt_config = self._load_prompt_config()
            self.system_prompt = self._build_system_prompt()
            logger.info("Successfully reloaded prompt configuration")
            return True
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False
