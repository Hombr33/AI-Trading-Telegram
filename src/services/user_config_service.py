"""User configuration service for managing user-specific trading settings."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..core.logging import get_logger
from ..database.session import SessionLocal
from ..models.telegram_users import TelegramUser, UserConfiguration

logger = get_logger(__name__)


class UserConfigService:
    """Service for managing user-specific configuration settings."""

    def __init__(self):
        self.default_config = {
            "notifications": {
                "signals": True,
                "positions": True,
                "orders": True,
                "risk": True,
                "performance": True,
                "system": True,
            },
            "trading": {
                "auto_trading": False,
                "risk_per_trade_pct": 2.0,
                "max_open_positions": 5,
                "allowed_symbols": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"],
                "max_daily_loss_usd": 25.0,
            },
            "risk": {
                "max_drawdown_pct": 15.0,
                "max_daily_loss_pct": 5.0,
                "max_position_size_pct": 10.0,
                "stop_on_consecutive_losses": 4,
            },
            "system": {
                "timezone": "UTC",
                "update_frequency_seconds": 60,
                "log_level": "INFO",
                "preferred_timeframe": "H1",
            },
        }

    async def get_user_config(self, telegram_id: int) -> Dict[str, Any]:
        """Get user configuration, creating default if not exists.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User configuration dictionary
        """
        try:
            session = SessionLocal()
            try:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    # Create new user with default config
                    user = TelegramUser(
                        telegram_id=telegram_id,
                        username=f"user_{telegram_id}",
                        first_name="Unknown",
                        is_active=True,
                        created_at=datetime.utcnow(),
                    )
                    session.add(user)
                    session.commit()
                    logger.info(f"Created new user: {telegram_id}")

                # Get all configuration entries for user
                configs = (
                    session.query(UserConfiguration)
                    .filter(
                        UserConfiguration.user_id == user.id,
                        UserConfiguration.is_active == True,
                    )
                    .all()
                )

                # Start with deep copy of default config
                import copy

                user_config = copy.deepcopy(self.default_config)

                # Update with user-specific configurations
                for config in configs:
                    if config.config_type in user_config:
                        # Merge user config over defaults
                        user_config[config.config_type].update(config.config_data)
                    else:
                        # New config section not in defaults
                        user_config[config.config_type] = config.config_data

                # Create missing default configurations if needed
                need_defaults = []
                for config_type in self.default_config.keys():
                    if not any(c.config_type == config_type for c in configs):
                        need_defaults.append(config_type)
                        default_config = UserConfiguration(
                            user_id=user.id,
                            config_type=config_type,
                            config_data=self.default_config[config_type],
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )
                        session.add(default_config)

                if need_defaults:
                    session.commit()
                logger.info(f"Retrieved/created config for user: {telegram_id}")

                return user_config
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error getting user config for {telegram_id}: {e}")
            return self.default_config.copy()

    async def update_user_config(
        self, telegram_id: int, config_section: str, key: str, value: Any
    ) -> bool:
        """Update a specific configuration value for a user.

        Args:
            telegram_id: Telegram user ID
            config_section: Configuration section (notifications, trading, risk, system)
            key: Configuration key
            value: New value

        Returns:
            Success status
        """
        try:
            session = SessionLocal()
            try:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    logger.error(f"User not found: {telegram_id}")
                    return False

                # Find the specific configuration section
                config = (
                    session.query(UserConfiguration)
                    .filter(
                        UserConfiguration.user_id == user.id,
                        UserConfiguration.config_type == config_section,
                        UserConfiguration.is_active == True,
                    )
                    .first()
                )

                if not config:
                    # Create new configuration section
                    config_data = self.default_config.get(config_section, {}).copy()
                    config_data[key] = value

                    config = UserConfiguration(
                        user_id=user.id,
                        config_type=config_section,
                        config_data=config_data,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    session.add(config)
                else:
                    # Update existing configuration
                    if config.config_data is None:
                        config.config_data = {}

                    config.config_data[key] = value
                    config.updated_at = datetime.utcnow()

                    # Mark the JSON field as modified for SQLAlchemy
                    flag_modified(config, "config_data")

                session.commit()

                logger.info(
                    f"Updated config for user {telegram_id}: {config_section}.{key} = {value}"
                )
                return True
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error updating user config for {telegram_id}: {e}")
            return False

    async def update_user_symbols(self, telegram_id: int, symbols: List[str]) -> bool:
        """Update allowed trading symbols for a user.

        Args:
            telegram_id: Telegram user ID
            symbols: List of trading symbols

        Returns:
            Success status
        """
        return await self.update_user_config(
            telegram_id, "trading", "allowed_symbols", symbols
        )

    async def toggle_notification(
        self, telegram_id: int, notification_type: str
    ) -> bool:
        """Toggle a specific notification setting.

        Args:
            telegram_id: Telegram user ID
            notification_type: Type of notification to toggle

        Returns:
            New state of the notification
        """
        try:
            config = await self.get_user_config(telegram_id)
            current_state = config.get("notifications", {}).get(notification_type, True)
            new_state = not current_state

            success = await self.update_user_config(
                telegram_id, "notifications", notification_type, new_state
            )

            if success:
                return new_state
            return current_state

        except Exception as e:
            logger.error(
                f"Error toggling notification {notification_type} for {telegram_id}: {e}"
            )
            return False

    async def get_user_symbols(self, telegram_id: int) -> List[str]:
        """Get allowed trading symbols for a user.

        Args:
            telegram_id: Telegram user ID

        Returns:
            List of allowed symbols
        """
        try:
            config = await self.get_user_config(telegram_id)
            return config.get("trading", {}).get(
                "allowed_symbols", self.default_config["trading"]["allowed_symbols"]
            )
        except Exception as e:
            logger.error(f"Error getting user symbols for {telegram_id}: {e}")
            return self.default_config["trading"]["allowed_symbols"]

    async def get_user_risk_settings(self, telegram_id: int) -> Dict[str, Any]:
        """Get risk management settings for a user.

        Args:
            telegram_id: Telegram user ID

        Returns:
            Risk settings dictionary
        """
        try:
            config = await self.get_user_config(telegram_id)
            return config.get("risk", self.default_config["risk"])
        except Exception as e:
            logger.error(f"Error getting risk settings for {telegram_id}: {e}")
            return self.default_config["risk"]

    async def validate_config_update(
        self, config_section: str, key: str, value: Any
    ) -> tuple[bool, str]:
        """Validate a configuration update.

        Args:
            config_section: Configuration section
            key: Configuration key
            value: Proposed value

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if config_section == "risk":
                if key in [
                    "max_drawdown_pct",
                    "max_daily_loss_pct",
                    "max_position_size_pct",
                ]:
                    if not isinstance(value, (int, float)) or value <= 0 or value > 100:
                        return False, "Percentage must be between 0 and 100"
                elif key == "stop_on_consecutive_losses":
                    if not isinstance(value, int) or value < 1 or value > 20:
                        return False, "Consecutive losses must be between 1 and 20"

            elif config_section == "trading":
                if key == "risk_per_trade_pct":
                    if not isinstance(value, (int, float)) or value <= 0 or value > 10:
                        return False, "Risk per trade must be between 0 and 10%"
                elif key == "max_open_positions":
                    if not isinstance(value, int) or value < 1 or value > 50:
                        return False, "Max positions must be between 1 and 50"
                elif key == "max_daily_loss_usd":
                    if not isinstance(value, (int, float)) or value <= 0:
                        return False, "Max daily loss must be positive"
                elif key == "allowed_symbols":
                    if not isinstance(value, list) or not all(
                        isinstance(s, str) for s in value
                    ):
                        return False, "Symbols must be a list of strings"

            elif config_section == "system":
                if key == "update_frequency_seconds":
                    if not isinstance(value, int) or value < 10 or value > 3600:
                        return (
                            False,
                            "Update frequency must be between 10 and 3600 seconds",
                        )

            return True, ""

        except Exception as e:
            return False, f"Validation error: {str(e)}"
