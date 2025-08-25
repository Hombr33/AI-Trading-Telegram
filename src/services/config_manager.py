"""
Configuration management service for multi-user trading system.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.telegram_users import (
    TelegramUser, UserConfiguration, ServerConfiguration
)
from ..database.connection import get_db_session

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
                {"losses": 4, "action": "emergency_stop", "pause_minutes": 1440}
            ],
            "correlation_limits": {
                "max_correlation": 0.70,
                "high_correlation_max_positions": 2,
                "medium_correlation_max_positions": 4,
                "low_correlation_max_positions": 8
            }
        },
        "symbol": {
            "active_symbols": ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD"],
            "symbol_settings": {
                "XAUUSD": {"min_confidence": 70, "max_spread": 5, "preferred_sessions": ["london", "newyork"]},
                "EURUSD": {"min_confidence": 65, "max_spread": 3, "preferred_sessions": ["london", "newyork"]},
                "GBPUSD": {"min_confidence": 65, "max_spread": 4, "preferred_sessions": ["london", "newyork"]},
                "USDJPY": {"min_confidence": 60, "max_spread": 3, "preferred_sessions": ["london", "newyork", "asian"]},
                "USDCAD": {"min_confidence": 60, "max_spread": 4, "preferred_sessions": ["london", "newyork"]}
            }
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
                "batch": {"min_confidence": 40, "batch_interval_minutes": 60}
            }
        },
        "model": {
            "openai_model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 2000,
            "timeout_seconds": 30,
            "retry_attempts": 3,
            "analysis_prompt_version": "v2.1",
            "context_window_candles": 1000
        },
        "trading": {
            "position_sizing_method": "risk_percent_of_equity",
            "order_types": {
                "preferred": "limit",
                "fallback": "market",
                "breakout": "stop"
            },
            "execution_settings": {
                "slippage_points": 10,
                "magic_number": 1001,
                "order_filling": "FOK",
                "order_time": "GTC"
            },
            "stop_loss_rules": {
                "never_widen": True,
                "move_to_breakeven_at_rr": 1.0,
                "trailing_stop_enabled": True,
                "trailing_start_points": 250,
                "trailing_step_points": 50
            },
            "take_profit_rules": {
                "tp1_rr": 1.5,
                "tp1_close_pct": 0.5,
                "tp2_rr": 3.0,
                "tp2_close_pct": 0.5
            }
        },
        "rules": {
            "session_filters": {
                "london": {"active": True, "risk_multiplier": 1.0},
                "newyork": {"active": True, "risk_multiplier": 1.0},
                "asian": {"active": True, "risk_multiplier": 0.5},
                "overlap": {"active": True, "risk_multiplier": 1.2}
            },
            "news_filters": {
                "avoid_high_impact": True,
                "buffer_minutes_before": 30,
                "buffer_minutes_after": 30,
                "close_positions_on_news": True
            },
            "volatility_filters": {
                "high_volatility_action": "reduce_size_25_percent",
                "extreme_volatility_action": "no_new_positions",
                "atr_multiplier_threshold": 2.0
            }
        }
    }

    async def get_user_config(self, telegram_id: int, config_type: str) -> Optional[Dict[str, Any]]:
        """Get user configuration by type."""
        try:
            with get_db_session() as session:
                user = session.query(TelegramUser).filter(
                    TelegramUser.telegram_id == telegram_id
                ).first()

                if not user:
                    return None

                config = session.query(UserConfiguration).filter(
                    UserConfiguration.user_id == user.id,
                    UserConfiguration.config_type == config_type,
                    UserConfiguration.is_active == True
                ).first()

                if config:
                    return config.config_data
                else:
                    # Return default configuration
                    return self.DEFAULT_CONFIGS.get(config_type, {})

        except Exception as e:
            logger.error(f"Error getting user configuration: {e}")
            return None

    async def set_user_config(self, telegram_id: int, config_type: str, 
                             config_data: Dict[str, Any]) -> bool:
        """Set user configuration."""
        try:
            with get_db_session() as session:
                user = session.query(TelegramUser).filter(
                    TelegramUser.telegram_id == telegram_id
                ).first()

                if not user:
                    return False

                # Validate config type
                if config_type not in self.DEFAULT_CONFIGS:
                    return False

                # Check if configuration already exists
                existing_config = session.query(UserConfiguration).filter(
                    UserConfiguration.user_id == user.id,
                    UserConfiguration.config_type == config_type,
                    UserConfiguration.is_active == True
                ).first()

                if existing_config:
                    existing_config.config_data = config_data
                    existing_config.updated_at = datetime.utcnow()
                else:
                    new_config = UserConfiguration(
                        user_id=user.id,
                        config_type=config_type,
                        config_data=config_data
                    )
                    session.add(new_config)

                session.commit()
                logger.info(f"Configuration '{config_type}' updated for user {telegram_id}")
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
                config = session.query(ServerConfiguration).filter(
                    ServerConfiguration.config_key == config_type,
                    ServerConfiguration.is_active == True
                ).first()

                return config.config_value if config else None

        except Exception as e:
            logger.error(f"Error getting server configuration: {e}")
            return None

    async def set_server_config(self, admin_telegram_id: int, config_key: str, 
                               config_value: Any, description: str = None) -> bool:
        """Set server configuration (admin only)."""
        # Check admin privileges
        try:
            with get_db_session() as session:
                admin_user = session.query(TelegramUser).filter(
                    TelegramUser.telegram_id == admin_telegram_id,
                    TelegramUser.role == "admin"
                ).first()

                if not admin_user:
                    return False

                # Check if configuration exists
                existing_config = session.query(ServerConfiguration).filter(
                    ServerConfiguration.config_key == config_key
                ).first()

                if existing_config:
                    existing_config.config_value = config_value
                    existing_config.description = description or existing_config.description
                    existing_config.updated_at = datetime.utcnow()
                else:
                    new_config = ServerConfiguration(
                        config_key=config_key,
                        config_value=config_value,
                        description=description
                    )
                    session.add(new_config)

                session.commit()
                logger.info(f"Server configuration '{config_key}' updated by admin {admin_telegram_id}")
                return True

        except Exception as e:
            logger.error(f"Error setting server configuration: {e}")
            return False

    async def get_all_server_configs(self, admin_telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get all server configurations (admin only)."""
        try:
            with get_db_session() as session:
                admin_user = session.query(TelegramUser).filter(
                    TelegramUser.telegram_id == admin_telegram_id,
                    TelegramUser.role == "admin"
                ).first()

                if not admin_user:
                    return None

                configs = session.query(ServerConfiguration).filter(
                    ServerConfiguration.is_active == True
                ).all()

                return {
                    config.config_key: {
                        "value": config.config_value,
                        "description": config.description,
                        "updated_at": config.updated_at
                    }
                    for config in configs
                }
        except Exception as e:
            logger.error(f"Error getting all server configurations: {e}")
            return None

    async def validate_config(self, config_type: str, config_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate configuration data."""
        if config_type not in self.DEFAULT_CONFIGS:
            return False, f"Invalid configuration type: {config_type}"

        default_config = self.DEFAULT_CONFIGS[config_type]
        
        # Basic validation based on config type
        if config_type == "risk":
            if not isinstance(config_data.get("risk_per_trade_pct"), (int, float)) or \
               config_data.get("risk_per_trade_pct", 0) <= 0 or \
               config_data.get("risk_per_trade_pct", 0) > 10:
                return False, "Risk per trade must be between 0.1% and 10%"
                
            if not isinstance(config_data.get("max_daily_drawdown_pct"), (int, float)) or \
               config_data.get("max_daily_drawdown_pct", 0) <= 0 or \
               config_data.get("max_daily_drawdown_pct", 0) > 20:
                return False, "Max daily drawdown must be between 0.1% and 20%"

        elif config_type == "signal":
            if not isinstance(config_data.get("min_confidence_threshold"), int) or \
               config_data.get("min_confidence_threshold", 0) < 30 or \
               config_data.get("min_confidence_threshold", 0) > 95:
                return False, "Minimum confidence threshold must be between 30 and 95"

        elif config_type == "symbol":
            active_symbols = config_data.get("active_symbols", [])
            if not isinstance(active_symbols, list) or len(active_symbols) == 0:
                return False, "At least one active symbol must be specified"

        return True, "Configuration is valid"
