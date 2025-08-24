"""
Signal validation module for OpenAI analyzer.
Validates trading signals against schema and business rules.
"""

import logging
from typing import Dict, Any, List, Optional, Union
import json
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class TradingSetup(BaseModel):
    """Trading setup schema matching app-code-prompt.json signal_schema"""
    type: str = Field(description="SELL or BUY")
    entry_zone: List[float] = Field(description="[float_low, float_high] entry zone")
    entry_style: str = Field(description="limit, market, or stop")
    sl: float = Field(description="Stop loss level")
    tp: List[float] = Field(description="Take profit levels [tp1, tp2_optional]")
    confidence: int = Field(description="Confidence level 0-100", ge=0, le=100)
    notes: str = Field(description="Short trading notes")
    
    class Config:
        extra = "forbid"


class TradingSignal(BaseModel):
    """Complete trading signal schema matching app-code-prompt.json"""
    id: str = Field(description="Unique signal ID")
    symbol: str = Field(description="Trading symbol")
    bias: str = Field(description="BULLISH, BEARISH, or NEUTRAL")
    setups: List[TradingSetup] = Field(description="List of trading setups")
    risk_per_trade_pct: float = Field(description="Risk percentage per trade", gt=0, le=10)
    move_to_BE_at_R1: bool = Field(description="Move to breakeven at R1")
    tp1_close_pct: float = Field(description="Percentage to close at TP1", gt=0, le=1)
    
    class Config:
        extra = "forbid"


class SignalValidator:
    """Validates trading signals against schema and business rules."""
    
    def __init__(self, prompt_config: Optional[Dict[str, Any]] = None):
        """Initialize signal validator.
        
        Args:
            prompt_config: Configuration from app-code-prompt.json
        """
        self.prompt_config = prompt_config or {}
        self.validation_rules = self._load_validation_rules()
        
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules from prompt config."""
        trading_sop = self.prompt_config.get('trading_SOP', {})
        
        return {
            'min_confidence': 60,
            'max_confidence': 100,
            'min_rr_ratio': trading_sop.get('entry_rules', {}).get('rr_min', 1.5),
            'max_risk_per_trade': trading_sop.get('risk', {}).get('risk_per_trade_pct', 2.0),
            'valid_biases': ['BULLISH', 'BEARISH', 'NEUTRAL'],
            'valid_setup_types': ['BUY', 'SELL'],
            'valid_entry_styles': ['limit', 'market', 'stop'],
            'max_entry_zone_spread_pips': 50,  # Maximum spread between entry zone levels (forex majors)
            'max_entry_zone_spread_pips_exotic': 200,  # Maximum spread for exotic pairs
            'min_sl_distance_pips': 10,       # Minimum SL distance from entry
            'max_sl_distance_pips': 500,      # Maximum SL distance from entry
            'max_sl_distance_pips_exotic': 1000,  # Maximum SL distance for exotic pairs
        }
    
    def validate_signal(self, signal_data: Union[Dict[str, Any], str]) -> tuple[Optional[TradingSignal], List[str]]:
        """Validate a trading signal.
        
        Args:
            signal_data: Signal data as dict or JSON string
            
        Returns:
            Tuple of (validated_signal, validation_errors)
        """
        # Store symbol for symbol-specific validation
        if isinstance(signal_data, dict):
            self._current_symbol = signal_data.get('symbol', 'UNKNOWN')
        elif isinstance(signal_data, str):
            try:
                temp_data = json.loads(signal_data)
                self._current_symbol = temp_data.get('symbol', 'UNKNOWN')
            except:
                self._current_symbol = 'UNKNOWN'
        else:
            self._current_symbol = 'UNKNOWN'
        errors = []
        
        # Parse JSON if string
        if isinstance(signal_data, str):
            try:
                signal_data = json.loads(signal_data)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON format: {e}")
                return None, errors
        
        # Basic schema validation
        try:
            validated_signal = TradingSignal(**signal_data)
        except ValidationError as e:
            for error in e.errors():
                field = " -> ".join(str(x) for x in error['loc'])
                errors.append(f"Schema error in {field}: {error['msg']}")
            return None, errors
        
        # Business rule validation
        business_errors = self._validate_business_rules(validated_signal)
        errors.extend(business_errors)
        
        if errors:
            return None, errors
        
        logger.info(f"Signal validation successful for {validated_signal.symbol}")
        return validated_signal, []
    
    def _validate_business_rules(self, signal: TradingSignal) -> List[str]:
        """Validate business rules for a signal.
        
        Args:
            signal: Validated signal object
            
        Returns:
            List of business rule validation errors
        """
        errors = []
        
        # Validate bias
        if signal.bias not in self.validation_rules['valid_biases']:
            errors.append(f"Invalid bias: {signal.bias}. Must be one of {self.validation_rules['valid_biases']}")
        
        # Validate risk per trade
        if signal.risk_per_trade_pct > self.validation_rules['max_risk_per_trade']:
            errors.append(f"Risk per trade {signal.risk_per_trade_pct}% exceeds maximum {self.validation_rules['max_risk_per_trade']}%")
        
        # Validate TP1 close percentage
        if not (0 < signal.tp1_close_pct <= 1):
            errors.append(f"TP1 close percentage must be between 0 and 1, got {signal.tp1_close_pct}")
        
        # Validate each setup
        for i, setup in enumerate(signal.setups):
            setup_errors = self._validate_setup(setup, i)
            errors.extend(setup_errors)
        
        # Validate signal consistency
        consistency_errors = self._validate_signal_consistency(signal)
        errors.extend(consistency_errors)
        
        return errors
    
    def _validate_setup(self, setup: TradingSetup, setup_index: int) -> List[str]:
        """Validate a single trading setup.
        
        Args:
            setup: Trading setup to validate
            setup_index: Index of setup in signal
            
        Returns:
            List of validation errors for this setup
        """
        errors = []
        prefix = f"Setup {setup_index + 1}: "
        
        # Validate setup type
        if setup.type not in self.validation_rules['valid_setup_types']:
            errors.append(f"{prefix}Invalid type: {setup.type}. Must be one of {self.validation_rules['valid_setup_types']}")
        
        # Validate entry style
        if setup.entry_style not in self.validation_rules['valid_entry_styles']:
            errors.append(f"{prefix}Invalid entry style: {setup.entry_style}")
        
        # Validate confidence
        if not (self.validation_rules['min_confidence'] <= setup.confidence <= self.validation_rules['max_confidence']):
            errors.append(f"{prefix}Confidence {setup.confidence}% outside valid range {self.validation_rules['min_confidence']}-{self.validation_rules['max_confidence']}%")
        
        # Validate entry zone
        if len(setup.entry_zone) != 2:
            errors.append(f"{prefix}Entry zone must have exactly 2 values [low, high]")
        elif setup.entry_zone[0] >= setup.entry_zone[1]:
            errors.append(f"{prefix}Entry zone low ({setup.entry_zone[0]}) must be less than high ({setup.entry_zone[1]})")
        else:
            # Check entry zone spread with symbol-specific limits
            symbol = getattr(self, '_current_symbol', 'UNKNOWN')
            is_exotic = any(exotic in symbol for exotic in ['RUB', 'TRY', 'ZAR', 'MXN', 'BRL'])
            
            if is_exotic:
                # For exotic pairs, use different pip calculation and limits
                entry_spread_pips = abs(setup.entry_zone[1] - setup.entry_zone[0]) * 1000  # 3-decimal for exotics
                max_spread = self.validation_rules['max_entry_zone_spread_pips_exotic']
            else:
                # For major pairs, use standard calculation
                entry_spread_pips = abs(setup.entry_zone[1] - setup.entry_zone[0]) * 10000  # 4-decimal for majors
                max_spread = self.validation_rules['max_entry_zone_spread_pips']
            
            if entry_spread_pips > max_spread:
                errors.append(f"{prefix}Entry zone spread {entry_spread_pips:.1f} pips exceeds maximum {max_spread} pips for {'exotic' if is_exotic else 'major'} pair")
        
        # Validate stop loss with symbol-specific limits
        if len(setup.entry_zone) == 2:
            entry_mid = (setup.entry_zone[0] + setup.entry_zone[1]) / 2
            symbol = getattr(self, '_current_symbol', 'UNKNOWN')
            is_exotic = any(exotic in symbol for exotic in ['RUB', 'TRY', 'ZAR', 'MXN', 'BRL'])
            
            if is_exotic:
                sl_distance_pips = abs(setup.sl - entry_mid) * 1000  # 3-decimal for exotics
                max_sl_distance = self.validation_rules['max_sl_distance_pips_exotic']
            else:
                sl_distance_pips = abs(setup.sl - entry_mid) * 10000  # 4-decimal for majors
                max_sl_distance = self.validation_rules['max_sl_distance_pips']
            
            if sl_distance_pips < self.validation_rules['min_sl_distance_pips']:
                errors.append(f"{prefix}SL distance {sl_distance_pips:.1f} pips below minimum {self.validation_rules['min_sl_distance_pips']} pips")
            elif sl_distance_pips > max_sl_distance:
                errors.append(f"{prefix}SL distance {sl_distance_pips:.1f} pips exceeds maximum {max_sl_distance} pips for {'exotic' if is_exotic else 'major'} pair")
            
            # Validate SL direction
            if setup.type == "BUY" and setup.sl >= entry_mid:
                errors.append(f"{prefix}BUY setup SL ({setup.sl}) must be below entry zone ({entry_mid})")
            elif setup.type == "SELL" and setup.sl <= entry_mid:
                errors.append(f"{prefix}SELL setup SL ({setup.sl}) must be above entry zone ({entry_mid})")
        
        # Validate take profits
        if not setup.tp:
            errors.append(f"{prefix}At least one take profit level required")
        else:
            # Validate TP direction and order
            entry_mid = (setup.entry_zone[0] + setup.entry_zone[1]) / 2 if len(setup.entry_zone) == 2 else setup.entry_zone[0]
            
            for j, tp in enumerate(setup.tp):
                if setup.type == "BUY" and tp <= entry_mid:
                    errors.append(f"{prefix}BUY setup TP{j+1} ({tp}) must be above entry zone ({entry_mid})")
                elif setup.type == "SELL" and tp >= entry_mid:
                    errors.append(f"{prefix}SELL setup TP{j+1} ({tp}) must be below entry zone ({entry_mid})")
            
            # Check TP order (TP1 should be closer to entry than TP2)
            if len(setup.tp) >= 2:
                tp1_distance = abs(setup.tp[0] - entry_mid)
                tp2_distance = abs(setup.tp[1] - entry_mid)
                if tp2_distance <= tp1_distance:
                    errors.append(f"{prefix}TP2 should be further from entry than TP1")
        
        # Validate risk-reward ratio
        if len(setup.entry_zone) == 2 and setup.tp:
            entry_mid = (setup.entry_zone[0] + setup.entry_zone[1]) / 2
            sl_distance = abs(setup.sl - entry_mid)
            tp1_distance = abs(setup.tp[0] - entry_mid)
            
            if sl_distance > 0:
                rr_ratio = tp1_distance / sl_distance
                if rr_ratio < self.validation_rules['min_rr_ratio']:
                    errors.append(f"{prefix}Risk-reward ratio {rr_ratio:.2f} below minimum {self.validation_rules['min_rr_ratio']}")
        
        return errors
    
    def _validate_signal_consistency(self, signal: TradingSignal) -> List[str]:
        """Validate signal consistency across setups.
        
        Args:
            signal: Complete trading signal
            
        Returns:
            List of consistency validation errors
        """
        errors = []
        
        if not signal.setups:
            errors.append("Signal must have at least one setup")
            return errors
        
        # Check bias consistency with setup types
        bullish_setups = sum(1 for setup in signal.setups if setup.type == "BUY")
        bearish_setups = sum(1 for setup in signal.setups if setup.type == "SELL")
        
        if signal.bias == "BULLISH" and bearish_setups > bullish_setups:
            errors.append("BULLISH bias inconsistent with majority SELL setups")
        elif signal.bias == "BEARISH" and bullish_setups > bearish_setups:
            errors.append("BEARISH bias inconsistent with majority BUY setups")
        
        # Check for duplicate setups
        setup_signatures = []
        for i, setup in enumerate(signal.setups):
            signature = f"{setup.type}_{setup.entry_zone[0] if setup.entry_zone else 0}_{setup.sl}"
            if signature in setup_signatures:
                errors.append(f"Setup {i+1} appears to be duplicate of previous setup")
            setup_signatures.append(signature)
        
        return errors
    
    def validate_signal_json(self, json_string: str) -> tuple[Optional[TradingSignal], List[str]]:
        """Validate signal from JSON string.
        
        Args:
            json_string: JSON string containing signal data
            
        Returns:
            Tuple of (validated_signal, validation_errors)
        """
        try:
            signal_data = json.loads(json_string)
            return self.validate_signal(signal_data)
        except json.JSONDecodeError as e:
            return None, [f"Invalid JSON: {e}"]
    
    def get_validation_summary(self, signal: TradingSignal) -> Dict[str, Any]:
        """Get validation summary for a signal.
        
        Args:
            signal: Validated trading signal
            
        Returns:
            Validation summary dictionary
        """
        summary = {
            'signal_id': signal.id,
            'symbol': signal.symbol,
            'bias': signal.bias,
            'setup_count': len(signal.setups),
            'avg_confidence': sum(setup.confidence for setup in signal.setups) / len(signal.setups) if signal.setups else 0,
            'risk_per_trade_pct': signal.risk_per_trade_pct,
            'has_multiple_tp': any(len(setup.tp) > 1 for setup in signal.setups),
            'risk_reward_ratios': []
        }
        
        # Calculate RR ratios for each setup
        for setup in signal.setups:
            if len(setup.entry_zone) == 2 and setup.tp:
                entry_mid = (setup.entry_zone[0] + setup.entry_zone[1]) / 2
                sl_distance = abs(setup.sl - entry_mid)
                tp1_distance = abs(setup.tp[0] - entry_mid)
                
                if sl_distance > 0:
                    rr_ratio = tp1_distance / sl_distance
                    summary['risk_reward_ratios'].append(round(rr_ratio, 2))
        
        return summary
