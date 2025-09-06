"""
Signal distribution service for multi-user trading system.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..database.connection import get_db_session
from ..models.telegram_users import SignalSubscription, TelegramUser
from ..services.config_manager import ConfigManager
from ..services.user_manager import UserManager

logger = logging.getLogger(__name__)


class SignalDistributor:
    """Service for distributing trading signals to subscribed users."""

    def __init__(self):
        self.user_manager = UserManager()
        self.config_manager = ConfigManager()

    async def get_subscribed_users(
        self, symbol: str, min_confidence: int = 60
    ) -> List[Dict[str, Any]]:
        """Get users subscribed to a symbol with minimum confidence."""
        try:
            with get_db_session() as session:
                # Get all active users with subscriptions to this symbol
                subscribers = (
                    session.query(TelegramUser, SignalSubscription)
                    .join(
                        SignalSubscription,
                        TelegramUser.id == SignalSubscription.user_id,
                    )
                    .filter(
                        TelegramUser.is_active == True,
                        TelegramUser.subscription_status == "active",
                        SignalSubscription.symbol == symbol,
                        SignalSubscription.is_active == True,
                        SignalSubscription.min_confidence <= min_confidence,
                    )
                    .all()
                )

                return [
                    {
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "min_confidence": subscription.min_confidence,
                        "is_admin": user.is_admin,
                    }
                    for user, subscription in subscribers
                ]
        except Exception as e:
            logger.error(f"Failed to get subscribed users: {e}")
            return []

    async def should_distribute_signal(
        self, signal_data: Dict[str, Any], user_config: Dict[str, Any]
    ) -> bool:
        """Check if signal should be distributed to user based on their configuration."""
        signal_confidence = signal_data.get("confidence", 0)
        user_min_confidence = user_config.get("signal", {}).get(
            "min_confidence_threshold", 60
        )

        # Check confidence threshold
        if signal_confidence < user_min_confidence:
            return False

        # Check symbol settings
        symbol = signal_data.get("symbol")
        symbol_settings = user_config.get("symbol", {}).get("symbol_settings", {})

        if symbol in symbol_settings:
            symbol_min_confidence = symbol_settings[symbol].get("min_confidence", 60)
            if signal_confidence < symbol_min_confidence:
                return False

        # Check session filters
        current_session = self._get_current_session()
        session_filters = user_config.get("rules", {}).get("session_filters", {})

        if current_session in session_filters:
            if not session_filters[current_session].get("active", True):
                return False

        return True

    async def distribute_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Distribute signal to subscribed users."""
        try:
            with get_db_session() as session:
                symbol = signal_data.get("symbol")
                confidence = signal_data.get("confidence", 0)

                if not symbol:
                    logger.error("Signal missing symbol information")
                    return {"distributed": [], "skipped": []}

                # Get potential subscribers
                subscribers = await self.get_subscribed_users(symbol, confidence)

                distributed = []
                skipped = []

                for subscriber in subscribers:
                    telegram_id = subscriber["telegram_id"]

                    # Get user configuration
                    user_config = await self.config_manager.get_all_user_configs(
                        telegram_id
                    )

                    # Check if signal should be distributed
                    if await self.should_distribute_signal(signal_data, user_config):
                        distributed.append(telegram_id)
                        logger.info(
                            f"Signal distributed to user {telegram_id} for {symbol}"
                        )
                    else:
                        skipped.append(telegram_id)
                        logger.debug(
                            f"Signal skipped for user {telegram_id} for {symbol}"
                        )

                return {
                    "distributed": distributed,
                    "skipped": skipped,
                    "total_subscribers": len(subscribers),
                }
        except Exception as e:
            logger.error(f"Failed to distribute signal: {e}")
            return {"distributed": [], "skipped": []}

    async def get_user_signal_preferences(self, telegram_id: int) -> Dict[str, Any]:
        """Get user's signal distribution preferences."""
        user_config = await self.config_manager.get_user_config(telegram_id, "signal")
        if not user_config:
            return {}

        distribution_rules = user_config.get("distribution_rules", {})

        return {
            "immediate_threshold": distribution_rules.get("immediate", {}).get(
                "min_confidence", 80
            ),
            "delayed_threshold": distribution_rules.get("delayed", {}).get(
                "min_confidence", 60
            ),
            "batch_threshold": distribution_rules.get("batch", {}).get(
                "min_confidence", 40
            ),
            "delay_minutes": distribution_rules.get("delayed", {}).get(
                "delay_minutes", 5
            ),
            "batch_interval": distribution_rules.get("batch", {}).get(
                "batch_interval_minutes", 60
            ),
        }

    async def categorize_signal_distribution(
        self, signal_data: Dict[str, Any], subscribers: List[int]
    ) -> Dict[str, List[int]]:
        """Categorize signal distribution based on user preferences."""
        immediate = []
        delayed = []
        batch = []

        for telegram_id in subscribers:
            preferences = await self.get_user_signal_preferences(telegram_id)
            confidence = signal_data.get("confidence", 0)

            if confidence >= preferences.get("immediate_threshold", 80):
                immediate.append(telegram_id)
            elif confidence >= preferences.get("delayed_threshold", 60):
                delayed.append(telegram_id)
            elif confidence >= preferences.get("batch_threshold", 40):
                batch.append(telegram_id)

        return {"immediate": immediate, "delayed": delayed, "batch": batch}

    async def format_signal_message(
        self, signal_data: Dict[str, Any], telegram_id: int
    ) -> str:
        """Format signal message for user."""
        symbol = signal_data.get("symbol", "N/A")
        bias = signal_data.get("bias", "N/A")
        confidence = signal_data.get("confidence", 0)

        # Get first setup (assuming single setup for now)
        setups = signal_data.get("setups", [])
        if not setups:
            return "❌ Invalid signal format"

        setup = setups[0]
        signal_type = setup.get("type", "N/A")
        entry_zone = setup.get("entry_zone", [])
        sl = setup.get("sl", 0)
        tp = setup.get("tp", [])
        notes = setup.get("notes", "")

        # Format entry zone
        if len(entry_zone) == 2:
            entry_str = f"{entry_zone[0]} - {entry_zone[1]}"
        elif len(entry_zone) == 1:
            entry_str = str(entry_zone[0])
        else:
            entry_str = "N/A"

        # Format take profit levels
        tp_str = " | ".join(
            [f"TP{i+1}: {tp_level}" for i, tp_level in enumerate(tp[:2])]
        )

        # Get user's risk configuration
        risk_config = await self.config_manager.get_user_config(telegram_id, "risk")
        risk_pct = risk_config.get("risk_per_trade_pct", 2.0) if risk_config else 2.0

        message = f"""🚨 **AI TRADING SIGNAL** 🚨

📊 **Symbol:** {symbol}
📈 **Bias:** {bias}
🎯 **Type:** {signal_type}

💰 **Entry Zone:** {entry_str}
🛑 **Stop Loss:** {sl}
🎯 **Take Profit:** {tp_str}

📊 **Confidence:** {confidence}%
⚖️ **Risk:** {risk_pct}%

📝 **Analysis:** {notes}

⏰ Generated at {datetime.now().strftime('%H:%M:%S')}
"""

        return message

    def _get_current_session(self) -> str:
        """Get current trading session based on UTC time."""
        current_hour = datetime.utcnow().hour

        # London session: 07:00-16:00 UTC
        if 7 <= current_hour < 16:
            return "london"
        # New York session: 12:00-21:00 UTC
        elif 12 <= current_hour < 21:
            return (
                "newyork" if current_hour >= 16 else "overlap"
            )  # Overlap: 12:00-16:00
        # Asian session: 23:00-08:00 UTC
        else:
            return "asian"

    async def get_user_active_symbols(self, telegram_id: int) -> List[str]:
        """Get user's active symbol subscriptions."""
        with get_db_session() as session:
            user = (
                session.query(TelegramUser)
                .filter(TelegramUser.telegram_id == telegram_id)
                .first()
            )

            if not user:
                return []

            subscriptions = (
                session.query(SignalSubscription)
                .filter(
                    SignalSubscription.user_id == user.id,
                    SignalSubscription.is_active == True,
                )
                .all()
            )

            return [sub.symbol for sub in subscriptions]

    async def update_user_symbol_subscription(
        self, telegram_id: int, symbol: str, active: bool, min_confidence: int = 60
    ) -> bool:
        """Update user's symbol subscription."""
        return (
            await self.user_manager.subscribe_to_symbol(
                telegram_id, symbol, min_confidence
            )
            if active
            else True
        )
