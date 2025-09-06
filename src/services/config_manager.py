"""
Configuration management service for multi-user trading system.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database.connection import get_db_session
from ..models.telegram_users import ServerConfiguration, TelegramUser, UserConfiguration

logger = logging.getLogger(__name__)


class ConfigManager:
    """Service for managing user and server configurations."""

    # Default configuration templates
    DEFAULT_CONFIGS = {
        "risk": {
            "risk_per_trade_pct": 2.0,
            "max_daily_drawdown_pct": 6.0,
            "max_daily_loss_usd": 25.0,
            "target_daily_profit_usd": 50.0,
            "max_open_positions": 10,
            "max_daily_trades": 50,
            "consecutive_loss_rules": [
                {"losses": 2, "action": "reduce_size_50_percent", "pause_minutes": 30},
                {"losses": 3, "action": "pause_and_review", "pause_minutes": 120},
                {"losses": 4, "action": "emergency_stop", "pause_minutes": 1440},
            ],
            "correlation_limits": {
                "max_correlation": 0.70,
                "high_correlation_max_positions": 2,
                "medium_correlation_max_positions": 4,
                "low_correlation_max_positions": 8,
            },
        },
        "symbol": {
            "active_symbols": ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD"],
            "symbol_settings": {
                "XAUUSD": {
                    "min_confidence": 70,
                    "max_spread": 5,
                    "preferred_sessions": ["london", "newyork"],
                },
                "EURUSD": {
                    "min_confidence": 65,
                    "max_spread": 3,
                    "preferred_sessions": ["london", "newyork"],
                },
                "GBPUSD": {
                    "min_confidence": 65,
                    "max_spread": 4,
                    "preferred_sessions": ["london", "newyork"],
                },
                "USDJPY": {
                    "min_confidence": 60,
                    "max_spread": 3,
                    "preferred_sessions": ["london", "newyork", "asian"],
                },
                "USDCAD": {
                    "min_confidence": 60,
                    "max_spread": 4,
                    "preferred_sessions": ["london", "newyork"],
                },
            },
        },
        "signal": {
            "min_confidence_threshold": 60,
            "analysis_frequency_minutes": 5,
            "timeframes": ["H4", "H1", "M15", "M5", "M1"],
            "required_confluences": 3,
            "min_risk_reward_ratio": 1.5,
            "signal_expiry_minutes": 90,
            "distribution_rules": {
                "immediate": {"min_confidence": 80},
                "delayed": {"min_confidence": 60, "delay_minutes": 5},
                "batch": {"min_confidence": 40, "batch_interval_minutes": 60},
            },
        },
        "model": {
            "openai_model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 2000,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "analysis_prompt_version": "v2.1",
            "context_window_candles": 1000,
        },
        "trading": {
            "position_sizing_method": "risk_percent_of_equity",
            "order_types": {
                "preferred": "limit",
                "fallback": "market",
                "breakout": "stop",
            },
            "execution_settings": {
                "slippage_points": 10,
                "magic_number": 1001,
                "order_filling": "FOK",
                "order_time": "GTC",
            },
            "stop_loss_rules": {
                "never_widen": True,
                "move_to_breakeven_at_rr": 1.0,
                "trailing_stop_enabled": True,
                "trailing_start_points": 250,
                "trailing_step_points": 50,
            },
            "take_profit_rules": {
                "tp1_rr": 1.5,
                "tp1_close_pct": 0.5,
                "tp2_rr": 3.0,
                "tp2_close_pct": 0.5,
            },
        },
        "rules": {
            "session_filters": {
                "london": {"active": True, "risk_multiplier": 1.0},
                "newyork": {"active": True, "risk_multiplier": 1.0},
                "asian": {"active": True, "risk_multiplier": 0.5},
                "overlap": {"active": True, "risk_multiplier": 1.2},
            },
            "news_filters": {
                "avoid_high_impact": True,
                "buffer_minutes_before": 30,
                "buffer_minutes_after": 30,
                "close_positions_on_news": True,
            },
            "volatility_filters": {
                "high_volatility_action": "reduce_size_25_percent",
                "extreme_volatility_action": "no_new_positions",
                "atr_multiplier_threshold": 2.0,
            },
        },
    }

    async def get_user_config(
        self, telegram_id: int, config_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get user configuration by type."""
        try:
            with get_db_session() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    return None

                config = (
                    session.query(UserConfiguration)
                    .filter(
                        UserConfiguration.user_id == user.id,
                        UserConfiguration.config_type == config_type,
                        UserConfiguration.is_active == True,
                    )
                    .first()
                )

                if config:
                    return config.config_data
                else:
                    # Return default configuration
                    return self.DEFAULT_CONFIGS.get(config_type, {})

        except Exception as e:
            logger.error(f"Error getting user configuration: {e}")
            return None

    async def set_user_config(
        self,
        telegram_id: int,
        config_type: str,
        config_data: Dict[str, Any],
        validate: bool = True,
    ) -> bool:
        """Set user configuration."""
        try:
            with get_db_session() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    return False

                # Validate config type
                if config_type not in self.DEFAULT_CONFIGS:
                    return False

                # Validate configuration data if requested
                if validate:
                    is_valid, error_msg = await self.validate_config_comprehensive(
                        config_type, config_data
                    )
                    if not is_valid:
                        logger.warning(
                            f"Configuration validation failed for user {telegram_id}: {error_msg}"
                        )
                        return False

                # Check for configuration dependencies
                dependency_errors = await self._check_config_dependencies(
                    config_type, config_data, telegram_id
                )
                if dependency_errors:
                    logger.warning(
                        f"Configuration dependency issues for user {telegram_id}: {dependency_errors}"
                    )
                    # Don't block on dependencies, just log warnings

                # Check if configuration already exists
                existing_config = (
                    session.query(UserConfiguration)
                    .filter(
                        UserConfiguration.user_id == user.id,
                        UserConfiguration.config_type == config_type,
                        UserConfiguration.is_active == True,
                    )
                    .first()
                )

                if existing_config:
                    existing_config.config_data = config_data
                    existing_config.updated_at = datetime.utcnow()
                else:
                    new_config = UserConfiguration(
                        user_id=user.id,
                        config_type=config_type,
                        config_data=config_data,
                    )
                    session.add(new_config)

                session.commit()

                # Invalidate cache for this user
                await self.invalidate_user_cache(telegram_id)

                logger.info(
                    f"Configuration '{config_type}' updated for user {telegram_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Error setting user configuration: {e}")
            return False

    async def get_all_user_configs(self, telegram_id: int) -> Dict[str, Dict[str, Any]]:
        """Get all configurations for a user."""
        try:
            configs = {}
            for config_type in self.DEFAULT_CONFIGS.keys():
                config_data = await self.get_user_config(telegram_id, config_type)
                if config_data:
                    configs[config_type] = config_data
            return configs

        except Exception as e:
            logger.error(f"Error getting all user configurations: {e}")
            return {}

    async def reset_user_config(self, telegram_id: int, config_type: str) -> bool:
        """Reset user configuration to default."""
        if config_type not in self.DEFAULT_CONFIGS:
            return False

        return await self.set_user_config(
            telegram_id, config_type, self.DEFAULT_CONFIGS[config_type]
        )

    async def get_server_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        """Get server configuration by type."""
        try:
            with get_db_session() as session:
                config = (
                    session.query(ServerConfiguration)
                    .filter(
                        ServerConfiguration.config_key == config_type,
                        ServerConfiguration.is_active == True,
                    )
                    .first()
                )

                return config.config_value if config else None

        except Exception as e:
            logger.error(f"Error getting server configuration: {e}")
            return None

    async def set_server_config(
        self,
        admin_telegram_id: int,
        config_key: str,
        config_value: Any,
        description: str = None,
    ) -> bool:
        """Set server configuration (admin only)."""
        # Check admin privileges
        try:
            with get_db_session() as session:
                admin_user = (
                    session.query(TelegramUser)
                    .filter(
                        TelegramUser.telegram_id == admin_telegram_id,
                        TelegramUser.role == "admin",
                    )
                    .first()
                )

                if not admin_user:
                    return False

                # Check if configuration exists
                existing_config = (
                    session.query(ServerConfiguration)
                    .filter(ServerConfiguration.config_key == config_key)
                    .first()
                )

                if existing_config:
                    existing_config.config_value = config_value
                    existing_config.description = (
                        description or existing_config.description
                    )
                    existing_config.updated_at = datetime.utcnow()
                else:
                    new_config = ServerConfiguration(
                        config_key=config_key,
                        config_value=config_value,
                        description=description,
                    )
                    session.add(new_config)

                session.commit()
                logger.info(
                    f"Server configuration '{config_key}' updated by admin {admin_telegram_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Error setting server configuration: {e}")
            return False

    async def get_all_server_configs(
        self, admin_telegram_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get all server configurations (admin only)."""
        try:
            with get_db_session() as session:
                admin_user = (
                    session.query(TelegramUser)
                    .filter(
                        TelegramUser.telegram_id == admin_telegram_id,
                        TelegramUser.role == "admin",
                    )
                    .first()
                )

                if not admin_user:
                    return None

                configs = (
                    session.query(ServerConfiguration)
                    .filter(ServerConfiguration.is_active == True)
                    .all()
                )

                return {
                    config.config_key: {
                        "value": config.config_value,
                        "description": config.description,
                        "updated_at": config.updated_at,
                    }
                    for config in configs
                }
        except Exception as e:
            logger.error(f"Error getting all server configurations: {e}")
            return None

    async def validate_config(
        self, config_type: str, config_data: Dict[str, Any]
    ) -> tuple[bool, str]:
        """Validate configuration data."""
        if config_type not in self.DEFAULT_CONFIGS:
            return False, f"Invalid configuration type: {config_type}"

        default_config = self.DEFAULT_CONFIGS[config_type]

        # Basic validation based on config type
        if config_type == "risk":
            if (
                not isinstance(config_data.get("risk_per_trade_pct"), (int, float))
                or config_data.get("risk_per_trade_pct", 0) <= 0
                or config_data.get("risk_per_trade_pct", 0) > 10
            ):
                return False, "Risk per trade must be between 0.1% and 10%"

            if (
                not isinstance(config_data.get("max_daily_drawdown_pct"), (int, float))
                or config_data.get("max_daily_drawdown_pct", 0) <= 0
                or config_data.get("max_daily_drawdown_pct", 0) > 20
            ):
                return False, "Max daily drawdown must be between 0.1% and 20%"

        elif config_type == "signal":
            if (
                not isinstance(config_data.get("min_confidence_threshold"), int)
                or config_data.get("min_confidence_threshold", 0) < 30
                or config_data.get("min_confidence_threshold", 0) > 95
            ):
                return False, "Minimum confidence threshold must be between 30 and 95"

        elif config_type == "symbol":
            active_symbols = config_data.get("active_symbols", [])
            if not isinstance(active_symbols, list) or len(active_symbols) == 0:
                return False, "At least one active symbol must be specified"

        return True, "Configuration is valid"

    async def validate_config_comprehensive(
        self, config_type: str, config_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Comprehensive configuration validation with detailed checks."""
        if config_type not in self.DEFAULT_CONFIGS:
            return False, f"Invalid configuration type: {config_type}"

        default_config = self.DEFAULT_CONFIGS[config_type]
        errors = []

        try:
            if config_type == "risk":
                errors.extend(self._validate_risk_config(config_data))
            elif config_type == "symbol":
                errors.extend(self._validate_symbol_config(config_data))
            elif config_type == "signal":
                errors.extend(self._validate_signal_config(config_data))
            elif config_type == "model":
                errors.extend(self._validate_model_config(config_data))
            elif config_type == "trading":
                errors.extend(self._validate_trading_config(config_data))
            elif config_type == "rules":
                errors.extend(self._validate_rules_config(config_data))

            if errors:
                return False, "; ".join(errors)
            return True, "Configuration is valid"

        except Exception as e:
            logger.error(f"Error during comprehensive validation: {e}")
            return False, f"Validation error: {str(e)}"

    def _validate_risk_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Validate risk configuration."""
        errors = []

        # Risk per trade validation
        risk_pct = config_data.get("risk_per_trade_pct")
        if not isinstance(risk_pct, (int, float)) or risk_pct <= 0 or risk_pct > 10:
            errors.append("Risk per trade must be between 0.1% and 10%")

        # Daily drawdown validation
        drawdown_pct = config_data.get("max_daily_drawdown_pct")
        if (
            not isinstance(drawdown_pct, (int, float))
            or drawdown_pct <= 0
            or drawdown_pct > 20
        ):
            errors.append("Max daily drawdown must be between 0.1% and 20%")

        # Daily loss validation
        daily_loss = config_data.get("max_daily_loss_usd")
        if (
            not isinstance(daily_loss, (int, float))
            or daily_loss <= 0
            or daily_loss > 1000
        ):
            errors.append("Max daily loss must be between $1 and $1000")

        # Target profit validation
        target_profit = config_data.get("target_daily_profit_usd")
        if (
            not isinstance(target_profit, (int, float))
            or target_profit <= 0
            or target_profit > 2000
        ):
            errors.append("Target daily profit must be between $1 and $2000")

        # Position limits validation
        max_positions = config_data.get("max_open_positions")
        if (
            not isinstance(max_positions, int)
            or max_positions < 1
            or max_positions > 50
        ):
            errors.append("Max open positions must be between 1 and 50")

        # Daily trades validation
        max_trades = config_data.get("max_daily_trades")
        if not isinstance(max_trades, int) or max_trades < 1 or max_trades > 200:
            errors.append("Max daily trades must be between 1 and 200")

        # Consecutive loss rules validation
        loss_rules = config_data.get("consecutive_loss_rules", [])
        if not isinstance(loss_rules, list) or len(loss_rules) == 0:
            errors.append("Consecutive loss rules must be a non-empty list")
        else:
            for i, rule in enumerate(loss_rules):
                if not isinstance(rule, dict):
                    errors.append(f"Loss rule {i+1} must be a dictionary")
                    continue
                if "losses" not in rule or "action" not in rule:
                    errors.append(
                        f"Loss rule {i+1} must have 'losses' and 'action' fields"
                    )

        return errors

    def _validate_symbol_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Validate symbol configuration."""
        errors = []

        # Active symbols validation
        active_symbols = config_data.get("active_symbols", [])
        if not isinstance(active_symbols, list) or len(active_symbols) == 0:
            errors.append("At least one active symbol must be specified")
        else:
            valid_symbols = [
                "XAUUSD",
                "EURUSD",
                "GBPUSD",
                "USDJPY",
                "USDCAD",
                "AUDUSD",
                "USDCHF",
                "NZDUSD",
            ]
            for symbol in active_symbols:
                if symbol not in valid_symbols:
                    errors.append(f"Invalid symbol: {symbol}")

        # Symbol settings validation
        symbol_settings = config_data.get("symbol_settings", {})
        if not isinstance(symbol_settings, dict):
            errors.append("Symbol settings must be a dictionary")
        else:
            for symbol, settings in symbol_settings.items():
                if not isinstance(settings, dict):
                    errors.append(f"Settings for {symbol} must be a dictionary")
                    continue

                # Confidence validation
                min_conf = settings.get("min_confidence")
                if not isinstance(min_conf, int) or min_conf < 30 or min_conf > 95:
                    errors.append(
                        f"Min confidence for {symbol} must be between 30 and 95"
                    )

                # Spread validation
                max_spread = settings.get("max_spread")
                if (
                    not isinstance(max_spread, (int, float))
                    or max_spread < 0
                    or max_spread > 20
                ):
                    errors.append(f"Max spread for {symbol} must be between 0 and 20")

        return errors

    def _validate_signal_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Validate signal configuration."""
        errors = []

        # Confidence threshold validation
        min_conf = config_data.get("min_confidence_threshold")
        if not isinstance(min_conf, int) or min_conf < 30 or min_conf > 95:
            errors.append("Minimum confidence threshold must be between 30 and 95")

        # Analysis frequency validation
        freq = config_data.get("analysis_frequency_minutes")
        if not isinstance(freq, int) or freq < 1 or freq > 60:
            errors.append("Analysis frequency must be between 1 and 60 minutes")

        # Timeframes validation
        timeframes = config_data.get("timeframes", [])
        if not isinstance(timeframes, list) or len(timeframes) == 0:
            errors.append("At least one timeframe must be specified")
        else:
            valid_timeframes = ["H4", "H1", "M15", "M5", "M1"]
            for tf in timeframes:
                if tf not in valid_timeframes:
                    errors.append(f"Invalid timeframe: {tf}")

        # Risk-reward validation
        min_rr = config_data.get("min_risk_reward_ratio")
        if not isinstance(min_rr, (int, float)) or min_rr < 1.0 or min_rr > 5.0:
            errors.append("Minimum risk-reward ratio must be between 1.0 and 5.0")

        return errors

    def _validate_model_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Validate model configuration."""
        errors = []

        # Model name validation
        model = config_data.get("openai_model")
        valid_models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        if model not in valid_models:
            errors.append(f"Invalid model: {model}. Must be one of {valid_models}")

        # Temperature validation
        temp = config_data.get("temperature")
        if not isinstance(temp, (int, float)) or temp < 0 or temp > 1:
            errors.append("Temperature must be between 0 and 1")

        # Max tokens validation
        max_tokens = config_data.get("max_tokens")
        if not isinstance(max_tokens, int) or max_tokens < 100 or max_tokens > 4000:
            errors.append("Max tokens must be between 100 and 4000")

        # Timeout validation
        timeout = config_data.get("timeout_seconds")
        if not isinstance(timeout, int) or timeout < 10 or timeout > 120:
            errors.append("Timeout must be between 10 and 120 seconds")

        return errors

    def _validate_trading_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Validate trading configuration."""
        errors = []

        # Position sizing validation
        sizing = config_data.get("position_sizing_method")
        valid_methods = ["risk_percent_of_equity", "fixed_lot", "martingale"]
        if sizing not in valid_methods:
            errors.append(f"Invalid position sizing method: {sizing}")

        # Order types validation
        order_types = config_data.get("order_types", {})
        if not isinstance(order_types, dict):
            errors.append("Order types must be a dictionary")
        else:
            required_keys = ["preferred", "fallback", "breakout"]
            for key in required_keys:
                if key not in order_types:
                    errors.append(f"Missing order type: {key}")

        return errors

    def _validate_rules_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Validate rules configuration."""
        errors = []

        # Session filters validation
        session_filters = config_data.get("session_filters", {})
        if not isinstance(session_filters, dict):
            errors.append("Session filters must be a dictionary")
        else:
            required_sessions = ["london", "newyork", "asian", "overlap"]
            for session in required_sessions:
                if session not in session_filters:
                    errors.append(f"Missing session filter: {session}")

        return errors

    async def get_config_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a configuration template by name."""
        templates = {
            "conservative": {
                "risk": {
                    "risk_per_trade_pct": 1.0,
                    "max_daily_drawdown_pct": 3.0,
                    "max_daily_loss_usd": 15.0,
                    "max_open_positions": 5,
                    "max_daily_trades": 20,
                },
                "signal": {
                    "min_confidence_threshold": 75,
                    "required_confluences": 4,
                    "min_risk_reward_ratio": 2.0,
                },
            },
            "aggressive": {
                "risk": {
                    "risk_per_trade_pct": 3.0,
                    "max_daily_drawdown_pct": 8.0,
                    "max_daily_loss_usd": 40.0,
                    "max_open_positions": 15,
                    "max_daily_trades": 80,
                },
                "signal": {
                    "min_confidence_threshold": 55,
                    "required_confluences": 2,
                    "min_risk_reward_ratio": 1.2,
                },
            },
            "scalping": {
                "risk": {
                    "risk_per_trade_pct": 0.5,
                    "max_daily_drawdown_pct": 2.0,
                    "max_daily_loss_usd": 10.0,
                    "max_open_positions": 20,
                    "max_daily_trades": 150,
                },
                "signal": {
                    "min_confidence_threshold": 65,
                    "analysis_frequency_minutes": 2,
                    "timeframes": ["M15", "M5", "M1"],
                    "signal_expiry_minutes": 30,
                },
            },
        }

        return templates.get(template_name)

    async def apply_config_template(self, telegram_id: int, template_name: str) -> bool:
        """Apply a configuration template to a user."""
        template = await self.get_config_template(template_name)
        if not template:
            return False

        success = True
        for config_type, config_data in template.items():
            if not await self.set_user_config(telegram_id, config_type, config_data):
                success = False

        return success

    async def bulk_set_user_configs(
        self, telegram_id: int, configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, bool]:
        """Set multiple user configurations at once."""
        results = {}
        for config_type, config_data in configs.items():
            # Validate each configuration
            is_valid, error_msg = await self.validate_config_comprehensive(
                config_type, config_data
            )
            if is_valid:
                results[config_type] = await self.set_user_config(
                    telegram_id, config_type, config_data
                )
            else:
                logger.warning(f"Invalid config for {config_type}: {error_msg}")
                results[config_type] = False

        return results

    async def export_user_configs(self, telegram_id: int) -> Optional[str]:
        """Export all user configurations as JSON string."""
        try:
            configs = await self.get_all_user_configs(telegram_id)
            if not configs:
                return None

            export_data = {
                "telegram_id": telegram_id,
                "exported_at": datetime.utcnow().isoformat(),
                "version": "1.0",
                "configurations": configs,
            }

            return json.dumps(export_data, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error exporting user configurations: {e}")
            return None

    async def import_user_configs(self, telegram_id: int, config_json: str) -> bool:
        """Import user configurations from JSON string."""
        try:
            import_data = json.loads(config_json)

            if "configurations" not in import_data:
                return False

            configs = import_data["configurations"]
            results = await self.bulk_set_user_configs(telegram_id, configs)

            # Check if all configurations were imported successfully
            return all(results.values())

        except json.JSONDecodeError:
            logger.error("Invalid JSON format for configuration import")
            return False
        except Exception as e:
            logger.error(f"Error importing user configurations: {e}")
            return False

    async def get_config_history(
        self, telegram_id: int, config_type: str = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get configuration change history for a user."""
        try:
            with get_db_session() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    return []

                query = session.query(UserConfiguration).filter(
                    UserConfiguration.user_id == user.id
                )

                if config_type:
                    query = query.filter(UserConfiguration.config_type == config_type)

                configs = (
                    query.order_by(desc(UserConfiguration.updated_at))
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "config_type": config.config_type,
                        "config_data": config.config_data,
                        "updated_at": config.updated_at.isoformat(),
                        "is_active": config.is_active,
                    }
                    for config in configs
                ]

        except Exception as e:
            logger.error(f"Error getting configuration history: {e}")
            return []

    async def clone_user_config(
        self,
        source_telegram_id: int,
        target_telegram_id: int,
        config_types: List[str] = None,
    ) -> bool:
        """Clone configuration from one user to another."""
        try:
            source_configs = await self.get_all_user_configs(source_telegram_id)
            if not source_configs:
                return False

            # Filter configurations if specific types are requested
            if config_types:
                filtered_configs = {
                    config_type: config_data
                    for config_type, config_data in source_configs.items()
                    if config_type in config_types
                }
            else:
                filtered_configs = source_configs

            results = await self.bulk_set_user_configs(
                target_telegram_id, filtered_configs
            )
            return all(results.values())

        except Exception as e:
            logger.error(f"Error cloning user configuration: {e}")
            return False

    async def get_users_with_config(
        self, config_type: str, config_key: str = None, config_value: Any = None
    ) -> List[int]:
        """Get telegram IDs of users with specific configuration."""
        try:
            with get_db_session() as session:
                query = (
                    session.query(TelegramUser.telegram_id)
                    .join(UserConfiguration)
                    .filter(
                        UserConfiguration.config_type == config_type,
                        UserConfiguration.is_active == True,
                    )
                )

                if config_key and config_value is not None:
                    # This is a simplified check - in production, you'd want more sophisticated JSON querying
                    query = query.filter(
                        UserConfiguration.config_data.contains(
                            {config_key: config_value}
                        )
                    )

                users = query.all()
                return [user.telegram_id for user in users]

        except Exception as e:
            logger.error(f"Error getting users with configuration: {e}")
            return []

    @lru_cache(maxsize=128)
    def _get_cached_config(
        self, telegram_id: int, config_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached configuration (internal method)."""
        # This would be called by the main get_user_config method
        # In a real implementation, you'd want to invalidate cache on updates
        return None

    async def invalidate_user_cache(self, telegram_id: int):
        """Invalidate cached configurations for a user."""
        # Clear cache entries for this user
        self._get_cached_config.cache_clear()

    async def get_config_statistics(
        self, admin_telegram_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get configuration statistics (admin only)."""
        try:
            with get_db_session() as session:
                admin_user = (
                    session.query(TelegramUser)
                    .filter(
                        TelegramUser.telegram_id == admin_telegram_id,
                        TelegramUser.role == "admin",
                    )
                    .first()
                )

                if not admin_user:
                    return None

                # Count configurations by type
                config_counts = (
                    session.query(
                        UserConfiguration.config_type,
                        UserConfiguration.is_active,
                        session.func.count(UserConfiguration.id),
                    )
                    .group_by(
                        UserConfiguration.config_type, UserConfiguration.is_active
                    )
                    .all()
                )

                stats = {
                    "total_configurations": 0,
                    "active_configurations": 0,
                    "inactive_configurations": 0,
                    "configurations_by_type": {},
                }

                for config_type, is_active, count in config_counts:
                    if config_type not in stats["configurations_by_type"]:
                        stats["configurations_by_type"][config_type] = {
                            "active": 0,
                            "inactive": 0,
                            "total": 0,
                        }

                    if is_active:
                        stats["configurations_by_type"][config_type]["active"] += count
                        stats["active_configurations"] += count
                    else:
                        stats["configurations_by_type"][config_type][
                            "inactive"
                        ] += count
                        stats["inactive_configurations"] += count

                    stats["configurations_by_type"][config_type]["total"] += count
                    stats["total_configurations"] += count

                return stats

        except Exception as e:
            logger.error(f"Error getting configuration statistics: {e}")
            return None

    async def _check_config_dependencies(
        self, config_type: str, config_data: Dict[str, Any], telegram_id: int
    ) -> List[str]:
        """Check configuration dependencies and return warnings."""
        warnings = []

        try:
            if config_type == "symbol":
                # Check if signal configuration exists for the symbols
                signal_config = await self.get_user_config(telegram_id, "signal")
                if signal_config:
                    active_symbols = config_data.get("active_symbols", [])
                    min_conf_threshold = signal_config.get(
                        "min_confidence_threshold", 60
                    )

                    symbol_settings = config_data.get("symbol_settings", {})
                    for symbol in active_symbols:
                        symbol_min_conf = symbol_settings.get(symbol, {}).get(
                            "min_confidence", 60
                        )
                        if symbol_min_conf < min_conf_threshold:
                            warnings.append(
                                f"Symbol {symbol} min confidence ({symbol_min_conf}) is below signal threshold ({min_conf_threshold})"
                            )

            elif config_type == "signal":
                # Check if risk configuration is compatible
                risk_config = await self.get_user_config(telegram_id, "risk")
                if risk_config:
                    min_rr = config_data.get("min_risk_reward_ratio", 1.5)
                    risk_pct = risk_config.get("risk_per_trade_pct", 2.0)

                    # High risk with low RR ratio warning
                    if risk_pct > 3.0 and min_rr < 1.5:
                        warnings.append(
                            "High risk per trade with low risk-reward ratio may be dangerous"
                        )

            elif config_type == "risk":
                # Check trading configuration compatibility
                trading_config = await self.get_user_config(telegram_id, "trading")
                if trading_config:
                    max_positions = config_data.get("max_open_positions", 10)
                    sizing_method = trading_config.get(
                        "position_sizing_method", "risk_percent_of_equity"
                    )

                    if sizing_method == "fixed_lot" and max_positions > 20:
                        warnings.append(
                            "Fixed lot sizing with many open positions may increase risk"
                        )

            return warnings

        except Exception as e:
            logger.error(f"Error checking configuration dependencies: {e}")
            return []

    async def get_user_config_with_fallbacks(
        self, telegram_id: int, config_type: str
    ) -> Dict[str, Any]:
        """Get user configuration with intelligent fallbacks."""
        try:
            # Try to get user-specific configuration
            user_config = await self.get_user_config(telegram_id, config_type)
            if user_config:
                return user_config

            # Fall back to default configuration
            default_config = self.DEFAULT_CONFIGS.get(config_type, {})

            # For some config types, try to get server-wide defaults
            if config_type in ["model", "rules"]:
                server_config = await self.get_server_config(f"default_{config_type}")
                if server_config:
                    # Merge server defaults with base defaults
                    merged_config = default_config.copy()
                    merged_config.update(server_config)
                    return merged_config

            return default_config

        except Exception as e:
            logger.error(f"Error getting configuration with fallbacks: {e}")
            return self.DEFAULT_CONFIGS.get(config_type, {})

    async def migrate_user_config(
        self, telegram_id: int, config_type: str, migration_function
    ) -> bool:
        """Migrate user configuration using a migration function."""
        try:
            current_config = await self.get_user_config(telegram_id, config_type)
            if not current_config:
                return False

            # Apply migration function
            migrated_config = migration_function(current_config)

            # Validate migrated configuration
            is_valid, error_msg = await self.validate_config_comprehensive(
                config_type, migrated_config
            )
            if not is_valid:
                logger.error(f"Migration failed validation: {error_msg}")
                return False

            # Save migrated configuration
            return await self.set_user_config(
                telegram_id, config_type, migrated_config, validate=False
            )

        except Exception as e:
            logger.error(f"Error migrating user configuration: {e}")
            return False

    async def get_config_diff(
        self, telegram_id: int, config_type: str
    ) -> Dict[str, Any]:
        """Get differences between user config and default config."""
        try:
            user_config = await self.get_user_config(telegram_id, config_type)
            default_config = self.DEFAULT_CONFIGS.get(config_type, {})

            if not user_config:
                return {
                    "differences": {},
                    "message": "User has no custom configuration",
                }

            differences = {}
            for key, default_value in default_config.items():
                user_value = user_config.get(key)
                if user_value != default_value:
                    differences[key] = {
                        "user_value": user_value,
                        "default_value": default_value,
                    }

            return {
                "differences": differences,
                "has_differences": len(differences) > 0,
                "message": f"Found {len(differences)} differences from default",
            }

        except Exception as e:
            logger.error(f"Error getting configuration differences: {e}")
            return {"differences": {}, "message": "Error calculating differences"}

    async def backup_user_configs(self, telegram_id: int) -> Optional[str]:
        """Create a backup of all user configurations."""
        try:
            export_data = await self.export_user_configs(telegram_id)
            if not export_data:
                return None

            # Add backup metadata
            backup_data = {
                "backup_type": "user_configurations",
                "telegram_id": telegram_id,
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0",
                "data": json.loads(export_data),
            }

            return json.dumps(backup_data, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error creating configuration backup: {e}")
            return None

    async def restore_user_configs(self, telegram_id: int, backup_json: str) -> bool:
        """Restore user configurations from backup."""
        try:
            backup_data = json.loads(backup_json)

            if backup_data.get("backup_type") != "user_configurations":
                logger.error("Invalid backup type")
                return False

            if backup_data.get("telegram_id") != telegram_id:
                logger.error("Backup is for different user")
                return False

            config_data = json.dumps(backup_data.get("data", {}))
            return await self.import_user_configs(telegram_id, config_data)

        except json.JSONDecodeError:
            logger.error("Invalid backup JSON format")
            return False
        except Exception as e:
            logger.error(f"Error restoring configuration backup: {e}")
            return False
