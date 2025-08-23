"""
Prompt management module for OpenAI analyzer.
Handles system prompts, context loading, and prompt formatting.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

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
            logger.info(f"Successfully loaded prompt config from {self.prompt_config_path}")
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
                    "Retail-feasible execution"
                ]
            },
            "trading_SOP": {
                "timeframes": {
                    "bias": ["H4", "H1"],
                    "setup": ["M15", "M5"],
                    "execution": ["M1"]
                },
                "entry_rules": {
                    "confluences_min": 3,
                    "required_signals": [
                        "Liquidity sweep or inducement",
                        "Candle rejection on M15/M5",
                        "Structure confirmation"
                    ]
                },
                "risk": {
                    "risk_per_trade_pct": 2.0
                }
            },
            "outputs_contract": {
                "analysis_sections": [
                    "H4_BigPicture",
                    "H1_Structure", 
                    "M15_EntryZone",
                    "M5_Execution",
                    "Trading_Plan"
                ],
                "signal_schema": {
                    "symbol": "string",
                    "bias": "BULLISH|BEARISH|NEUTRAL",
                    "setups": []
                }
            }
        }
    
    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt from config."""
        config = self.prompt_config
        
        # Build the system prompt sections
        sections = []
        
        # Identity section
        sections.append(f"You are {config.get('agent_name', 'Trading AI Assistant')}")
        sections.append(f"Role: {config.get('identity', {}).get('role', 'Trading assistant')}")
        
        # Principles section
        principles = config.get('identity', {}).get('principles', [])
        if principles:
            sections.append("\nCore Principles:")
            for principle in principles:
                sections.append(f"- {principle}")
        
        # Trading methodology section
        trading_sop = config.get('trading_SOP', {})
        if trading_sop:
            sections.append("\nTrading Methodology:")
            
            # Timeframes
            timeframes = trading_sop.get('timeframes', {})
            if timeframes:
                sections.append("Timeframes:")
                for tf_type, tfs in timeframes.items():
                    sections.append(f"- {tf_type.title()}: {', '.join(tfs)}")
            
            # Entry rules
            entry_rules = trading_sop.get('entry_rules', {})
            if entry_rules:
                sections.append("Entry Requirements:")
                sections.append(f"- Minimum {entry_rules.get('confluences_min', 3)} confluences")
                required_signals = entry_rules.get('required_signals', [])
                for signal in required_signals:
                    sections.append(f"- {signal}")
                
                rr_min = entry_rules.get('rr_min', 1.5)
                sections.append(f"- Minimum Risk:Reward ratio of {rr_min}:1")
            
            # Risk management
            risk = trading_sop.get('risk', {})
            if risk:
                sections.append("Risk Management:")
                sections.append(f"- Risk per trade: {risk.get('risk_per_trade_pct', 2.0)}%")
                sections.append(f"- Max daily drawdown: {risk.get('max_daily_drawdown_pct', 6.0)}%")
        
        # Analysis structure section
        outputs = config.get('outputs_contract', {})
        analysis_sections = outputs.get('analysis_sections', [])
        if analysis_sections:
            sections.append("\nAnalysis Structure:")
            sections.append("Provide analysis in these sections:")
            for section in analysis_sections:
                sections.append(f"- {section}")
        
        # Signal format section
        signal_schema = outputs.get('signal_schema', {})
        if signal_schema:
            sections.append("\nSignal Format:")
            sections.append("Return signals in JSON format matching this schema:")
            sections.append(json.dumps(signal_schema, indent=2))
        
        # Response style
        response_style = config.get('response_style', {})
        if response_style:
            sections.append("\nResponse Guidelines:")
            always_include = response_style.get('always_include', [])
            if always_include:
                sections.append(f"Always include: {', '.join(always_include)}")
            
            tone = response_style.get('tone', '')
            if tone:
                sections.append(f"Tone: {tone}")
        
        return "\n".join(sections)
    
    def get_system_prompt(self) -> str:
        """Get the complete system prompt."""
        return self.system_prompt
    
    def create_analysis_prompt(self, market_context: Dict[str, Any], 
                             realtime_data: Optional[str] = None) -> str:
        """Create analysis prompt with market context and real-time data.
        
        Args:
            market_context: Market context dictionary
            realtime_data: Optional real-time market data
            
        Returns:
            Formatted analysis prompt
        """
        prompt_parts = []
        
        # Market context
        prompt_parts.append("Market Context:")
        prompt_parts.append(json.dumps(market_context, indent=2))
        
        # Real-time data if available
        if realtime_data:
            prompt_parts.append("\nReal-time Market Data:")
            prompt_parts.append(realtime_data)
        
        # Analysis instructions
        prompt_parts.append("\nAnalysis Instructions:")
        prompt_parts.append("1. Analyze the chart screenshot using the trading methodology")
        prompt_parts.append("2. Follow the multi-timeframe approach (H4 → H1 → M15 → M5 → M1)")
        prompt_parts.append("3. Identify all required confluences before providing signals")
        prompt_parts.append("4. Generate signals in the exact JSON format specified")
        prompt_parts.append("5. Include confidence scores and risk management parameters")
        
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
