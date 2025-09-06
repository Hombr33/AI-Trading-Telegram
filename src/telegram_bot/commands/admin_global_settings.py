"""Admin global settings commands for Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.services.user_config_service import UserConfigService
from src.telegram_bot.commands.base import BaseCommandHandler
from src.telegram_bot.utils.keyboards import create_keyboard

logger = get_logger(__name__)


class AdminGlobalSettingsHandler(BaseCommandHandler):
    """Admin global settings command handler for Telegram bot."""

    def __init__(self):
        super().__init__()
        self.user_config_service = UserConfigService()
        self._register_commands()
        self._register_callbacks()

    def _register_commands(self):
        """Register admin global settings commands."""
        self.commands = {
            "admin_global": self.admin_global_command,
            "global_pairs": self.global_pairs_command,
            "global_intervals": self.global_intervals_command,
        }

    def _register_callbacks(self):
        """Register admin global settings callbacks."""
        self.callbacks = {
            "admin_global": self.admin_global_command,
            "global_pairs": self.global_pairs_command,
            "global_intervals": self.global_intervals_command,
            "set_global_pairs": self.global_pairs_command,
            "set_global_intervals": self.global_intervals_command,
            "add_global_pair": self._add_global_pair_callback,
            "remove_global_pair": self._remove_global_pair_callback,
            "reset_global_pairs": self._reset_global_pairs_callback,
            "set_global_interval": self._set_global_interval_callback,
            "reset_global_intervals": self._reset_global_intervals_callback,
        }

    async def admin_global_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle the /admin_global command - Main admin global settings menu."""
        try:
            # Check if user is admin
            if not await self._is_admin(update):
                await self.send_message(
                    update,
                    context,
                    "❌ **Access Denied**\n\nYou don't have admin privileges to access global settings.",
                )
                return

            message = (
                f"👑 **ADMIN GLOBAL SETTINGS** 👑\n\n"
                f"**Global Configuration Management**:\n"
                f"Configure system-wide settings that affect all users.\n\n"
                f"**Available Settings**:\n"
                f"📋 **Global Trading Pairs** - Set default trading pairs for all users\n"
                f"⏰ **Global Notification Intervals** - Set default notification intervals\n"
                f"🔧 **System Configuration** - Global system settings\n\n"
                f"**Note**: Changes here will affect all users unless they have custom settings."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("📋 Global Pairs", "global_pairs"),
                        ("⏰ Global Intervals", "global_intervals"),
                    ],
                    [
                        ("🔧 System Config", "global_system"),
                        ("📊 Global Stats", "global_stats"),
                    ],
                    [("⬅️ Admin Panel", "admin"), ("🏠 Main Menu", "start")],
                ]
            )

            await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in admin_global_command: {e}")
            error_message = (
                "❌ **Error Loading Global Settings**\n\n"
                "There was an issue loading admin global settings.\n"
                "Please try again in a moment."
            )
            await self.send_message(update, context, error_message)

    async def global_pairs_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle global trading pairs settings."""
        try:
            # Check if user is admin
            if not await self._is_admin(update):
                await self.send_message(
                    update,
                    context,
                    "❌ **Access Denied**\n\nYou don't have admin privileges.",
                )
                return

            # Get global trading pairs from config
            global_pairs = await self._get_global_trading_pairs()

            message = (
                f"📋 **GLOBAL TRADING PAIRS** 📋\n\n" f"**Current Global Pairs**:\n"
            )

            if global_pairs:
                for pair in global_pairs:
                    message += f"• {pair}\n"
            else:
                message += "• No global pairs configured\n"

            message += f"\n**Total**: {len(global_pairs)} pairs\n\n"
            message += "**Global Pairs**:\n"
            message += "These pairs will be available to all users by default.\n"
            message += "Users can still customize their own pairs in settings.\n\n"
            message += "**Popular Categories**:\n"
            message += "• Forex: EURUSD, GBPUSD, USDJPY, USDCAD\n"
            message += "• Crypto: BTCUSD, ETHUSD, XRPUSD\n"
            message += "• Metals: XAUUSD, XAGUSD\n"
            message += "• Indices: SPX500, NAS100, GER30"

            keyboard = create_keyboard(
                [
                    [
                        ("➕ Add Global Pair", "add_global_pair"),
                        ("➖ Remove Global Pair", "remove_global_pair"),
                    ],
                    [
                        ("📋 Popular Forex", "add_global_forex"),
                        ("📋 Popular Crypto", "add_global_crypto"),
                    ],
                    [
                        ("🔄 Reset Defaults", "reset_global_pairs"),
                        ("📊 View All", "view_global_pairs"),
                    ],
                    [("⬅️ Back", "admin_global"), ("🏠 Main", "start")],
                ]
            )

            await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in global_pairs_command: {e}")
            await self._handle_admin_error(update, context, "global_pairs")

    async def global_intervals_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle global notification intervals settings."""
        try:
            # Check if user is admin
            if not await self._is_admin(update):
                await self.send_message(
                    update,
                    context,
                    "❌ **Access Denied**\n\nYou don't have admin privileges.",
                )
                return

            # Get global intervals from config
            global_intervals = await self._get_global_notification_intervals()

            message = (
                f"⏰ **GLOBAL NOTIFICATION INTERVALS** ⏰\n\n"
                f"**Current Global Intervals**:\n"
                f"📈 Signals: {global_intervals.get('signals_minutes', 5)} minutes\n"
                f"📊 Positions: {global_intervals.get('positions_minutes', 1)} minutes\n"
                f"⚠️ Risk: {global_intervals.get('risk_minutes', 15)} minutes\n"
                f"📈 Performance: {global_intervals.get('performance_hours', 4)} hours\n"
                f"🔧 System: {global_intervals.get('system_minutes', 30)} minutes\n\n"
                f"**Global Intervals**:\n"
                f"These intervals will be the default for all new users.\n"
                f"Existing users can still customize their own intervals.\n\n"
                f"**Token Management**:\n"
                f"Longer intervals = fewer notifications = lower token usage\n"
                f"Shorter intervals = more notifications = higher token usage\n\n"
                f"**Recommended Settings**:\n"
                f"• Conservative: 15min signals, 4h performance\n"
                f"• Moderate: 5min signals, 2h performance\n"
                f"• Aggressive: 1min signals, 1h performance"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("📈 Signal Interval", "set_global_interval:signals"),
                        ("📊 Position Interval", "set_global_interval:positions"),
                    ],
                    [
                        ("⚠️ Risk Interval", "set_global_interval:risk"),
                        ("📈 Performance Interval", "set_global_interval:performance"),
                    ],
                    [
                        ("🔧 System Interval", "set_global_interval:system"),
                        ("🔄 Reset All", "reset_global_intervals"),
                    ],
                    [("⬅️ Back", "admin_global"), ("🏠 Main", "start")],
                ]
            )

            await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in global_intervals_command: {e}")
            await self._handle_admin_error(update, context, "global_intervals")

    async def add_global_pair_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle add global trading pair callback."""
        try:
            # Check if user is admin
            if not await self._is_admin(update):
                await update.callback_query.answer("❌ Access denied")
                return

            message = (
                f"➕ **ADD GLOBAL TRADING PAIR** ➕\n\n"
                f"**Popular Trading Pairs**:\n\n"
                f"**Forex Major Pairs**:\n"
                f"• EURUSD - Euro/US Dollar\n"
                f"• GBPUSD - British Pound/US Dollar\n"
                f"• USDJPY - US Dollar/Japanese Yen\n"
                f"• USDCAD - US Dollar/Canadian Dollar\n\n"
                f"**Crypto Pairs**:\n"
                f"• BTCUSD - Bitcoin/US Dollar\n"
                f"• ETHUSD - Ethereum/US Dollar\n"
                f"• XRPUSD - Ripple/US Dollar\n\n"
                f"**Metals**:\n"
                f"• XAUUSD - Gold/US Dollar\n"
                f"• XAGUSD - Silver/US Dollar\n\n"
                f"**Indices**:\n"
                f"• SPX500 - S&P 500\n"
                f"• NAS100 - NASDAQ 100\n"
                f"• GER30 - German DAX"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("EURUSD", "add_global_pair:EURUSD"),
                        ("GBPUSD", "add_global_pair:GBPUSD"),
                        ("USDJPY", "add_global_pair:USDJPY"),
                    ],
                    [
                        ("USDCAD", "add_global_pair:USDCAD"),
                        ("AUDUSD", "add_global_pair:AUDUSD"),
                        ("NZDUSD", "add_global_pair:NZDUSD"),
                    ],
                    [
                        ("BTCUSD", "add_global_pair:BTCUSD"),
                        ("ETHUSD", "add_global_pair:ETHUSD"),
                        ("XRPUSD", "add_global_pair:XRPUSD"),
                    ],
                    [
                        ("XAUUSD", "add_global_pair:XAUUSD"),
                        ("XAGUSD", "add_global_pair:XAGUSD"),
                        ("SPX500", "add_global_pair:SPX500"),
                    ],
                    [("Custom", "custom_add_global_pair"), ("⬅️ Back", "global_pairs")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in add_global_pair_callback: {e}")
            await self._handle_admin_error(update, context, "add_global_pair")

    async def remove_global_pair_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle remove global trading pair callback."""
        try:
            # Check if user is admin
            if not await self._is_admin(update):
                await update.callback_query.answer("❌ Access denied")
                return

            global_pairs = await self._get_global_trading_pairs()

            if not global_pairs:
                message = (
                    f"➖ **REMOVE GLOBAL TRADING PAIR** ➖\n\n"
                    f"**No global pairs to remove**\n\n"
                    f"No global trading pairs are currently configured.\n"
                    f"Add some pairs first to be able to remove them."
                )
                keyboard = create_keyboard(
                    [
                        [
                            ("➕ Add Global Pairs", "add_global_pair"),
                            ("⬅️ Back", "global_pairs"),
                        ]
                    ]
                )
            else:
                message = (
                    f"➖ **REMOVE GLOBAL TRADING PAIR** ➖\n\n"
                    f"**Current Global Pairs**:\n"
                )
                for pair in global_pairs:
                    message += f"• {pair}\n"

                message += f"\n**Select pair to remove**:"

                # Create buttons for each pair (max 2 per row)
                buttons = []
                for i in range(0, len(global_pairs), 2):
                    row = []
                    for j in range(2):
                        if i + j < len(global_pairs):
                            pair = global_pairs[i + j]
                            row.append((pair, f"remove_global_pair:{pair}"))
                    buttons.append(row)

                buttons.append([("⬅️ Back", "global_pairs")])
                keyboard = create_keyboard(buttons)

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in remove_global_pair_callback: {e}")
            await self._handle_admin_error(update, context, "remove_global_pair")

    async def reset_global_pairs_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle reset global trading pairs callback."""
        try:
            # Check if user is admin
            if not await self._is_admin(update):
                await update.callback_query.answer("❌ Access denied")
                return

            # Reset to default global trading pairs
            default_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "XAUUSD", "BTCUSD"]
            success = await self._set_global_trading_pairs(default_pairs)

            if success:
                await update.callback_query.answer(
                    "✅ Global trading pairs reset to defaults"
                )
                await self.global_pairs_command(update, context)
            else:
                await update.callback_query.answer(
                    "❌ Error resetting global trading pairs"
                )

        except Exception as e:
            logger.error(f"Error in reset_global_pairs_callback: {e}")
            await update.callback_query.answer(
                "❌ Error resetting global trading pairs"
            )

    async def set_global_interval_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle set global interval callback."""
        try:
            # Check if user is admin
            if not await self._is_admin(update):
                await update.callback_query.answer("❌ Access denied")
                return

            query = update.callback_query
            interval_type = query.data.split(":")[1]
            global_intervals = await self._get_global_notification_intervals()

            current_interval = global_intervals.get(f"{interval_type}_minutes", 5)
            if interval_type == "performance":
                current_interval = global_intervals.get(f"{interval_type}_hours", 4)

            message = (
                f"⏰ **SET GLOBAL {interval_type.upper()} INTERVAL** ⏰\n\n"
                f"**Current Global Interval**: {current_interval} {'hours' if interval_type == 'performance' else 'minutes'}\n\n"
                f"**Select New Global Interval**:\n"
                f"This will be the default for all new users.\n"
                f"Choose how often to receive {interval_type} notifications globally."
            )

            if interval_type == "performance":
                # Performance intervals in hours
                keyboard = create_keyboard(
                    [
                        [
                            ("1h", f"update_global_interval:{interval_type}:1"),
                            ("2h", f"update_global_interval:{interval_type}:2"),
                            ("4h", f"update_global_interval:{interval_type}:4"),
                        ],
                        [
                            ("6h", f"update_global_interval:{interval_type}:6"),
                            ("8h", f"update_global_interval:{interval_type}:8"),
                            ("12h", f"update_global_interval:{interval_type}:12"),
                        ],
                        [
                            ("24h", f"update_global_interval:{interval_type}:24"),
                            ("Custom", f"custom_global_interval:{interval_type}"),
                        ],
                        [("⬅️ Back", "global_intervals")],
                    ]
                )
            else:
                # Other intervals in minutes
                keyboard = create_keyboard(
                    [
                        [
                            ("1m", f"update_global_interval:{interval_type}:1"),
                            ("5m", f"update_global_interval:{interval_type}:5"),
                            ("15m", f"update_global_interval:{interval_type}:15"),
                        ],
                        [
                            ("30m", f"update_global_interval:{interval_type}:30"),
                            ("60m", f"update_global_interval:{interval_type}:60"),
                            ("120m", f"update_global_interval:{interval_type}:120"),
                        ],
                        [
                            ("240m", f"update_global_interval:{interval_type}:240"),
                            ("Custom", f"custom_global_interval:{interval_type}"),
                        ],
                        [("⬅️ Back", "global_intervals")],
                    ]
                )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in set_global_interval_callback: {e}")
            await self._handle_admin_error(update, context, "set_global_interval")

    async def reset_global_intervals_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle reset global intervals callback."""
        try:
            # Check if user is admin
            if not await self._is_admin(update):
                await update.callback_query.answer("❌ Access denied")
                return

            # Reset to default global intervals
            default_intervals = {
                "signals_minutes": 5,
                "positions_minutes": 1,
                "risk_minutes": 15,
                "performance_hours": 4,
                "system_minutes": 30,
            }
            success = await self._set_global_notification_intervals(default_intervals)

            if success:
                await update.callback_query.answer(
                    "✅ Global intervals reset to defaults"
                )
                await self.global_intervals_command(update, context)
            else:
                await update.callback_query.answer(
                    "❌ Error resetting global intervals"
                )

        except Exception as e:
            logger.error(f"Error in reset_global_intervals_callback: {e}")
            await update.callback_query.answer("❌ Error resetting global intervals")

    # Helper methods
    async def _is_admin(self, update: Update) -> bool:
        """Check if user is admin."""
        try:
            # This should be implemented based on your admin system
            # For now, return True for testing
            return True
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False

    async def _get_global_trading_pairs(self) -> list:
        """Get global trading pairs from config."""
        try:
            # This should read from a global config or database
            # For now, return default pairs
            return ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "XAUUSD"]
        except Exception as e:
            logger.error(f"Error getting global trading pairs: {e}")
            return []

    async def _set_global_trading_pairs(self, pairs: list) -> bool:
        """Set global trading pairs in config."""
        try:
            # This should write to a global config or database
            # For now, just return True
            logger.info(f"Setting global trading pairs: {pairs}")
            return True
        except Exception as e:
            logger.error(f"Error setting global trading pairs: {e}")
            return False

    async def _get_global_notification_intervals(self) -> dict:
        """Get global notification intervals from config."""
        try:
            # This should read from a global config or database
            # For now, return default intervals
            return {
                "signals_minutes": 5,
                "positions_minutes": 1,
                "risk_minutes": 15,
                "performance_hours": 4,
                "system_minutes": 30,
            }
        except Exception as e:
            logger.error(f"Error getting global notification intervals: {e}")
            return {}

    async def _set_global_notification_intervals(self, intervals: dict) -> bool:
        """Set global notification intervals in config."""
        try:
            # This should write to a global config or database
            # For now, just return True
            logger.info(f"Setting global notification intervals: {intervals}")
            return True
        except Exception as e:
            logger.error(f"Error setting global notification intervals: {e}")
            return False

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries for admin global settings."""
        query = update.callback_query
        await query.answer()

        data = query.data

        # Route to appropriate callback handler
        if data in self.callbacks:
            await self.callbacks[data](update, context)
        elif data.startswith("add_global_pair:"):
            symbol = data.split(":")[1]
            await self._add_global_pair(update, context, symbol)
        elif data.startswith("remove_global_pair:"):
            symbol = data.split(":")[1]
            await self._remove_global_pair(update, context, symbol)
        elif data.startswith("update_global_interval:"):
            parts = data.split(":")
            interval_type = parts[1]
            value = int(parts[2])
            await self._update_global_interval(update, context, interval_type, value)
        else:
            await query.edit_message_text(
                f"❌ **Unknown Callback**\n\n"
                f"Callback '{data}' not recognized.\n"
                f"Please try again or use /admin_global.",
                parse_mode="Markdown",
            )

    async def _add_global_pair(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str
    ):
        """Add a global trading pair."""
        try:
            # Check if user is admin
            if not await self._is_admin(update):
                await update.callback_query.answer("❌ Access denied")
                return

            global_pairs = await self._get_global_trading_pairs()
            if symbol not in global_pairs:
                global_pairs.append(symbol)
                success = await self._set_global_trading_pairs(global_pairs)
                if success:
                    await update.callback_query.answer(
                        f"✅ Added {symbol} to global pairs"
                    )
                    await self.global_pairs_command(update, context)
                else:
                    await update.callback_query.answer("❌ Error adding global pair")
            else:
                await update.callback_query.answer(
                    f"❌ {symbol} already in global pairs"
                )

        except Exception as e:
            logger.error(f"Error adding global pair: {e}")
            await update.callback_query.answer("❌ Error adding global pair")

    async def _remove_global_pair(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str
    ):
        """Remove a global trading pair."""
        try:
            # Check if user is admin
            if not await self._is_admin(update):
                await update.callback_query.answer("❌ Access denied")
                return

            global_pairs = await self._get_global_trading_pairs()
            if symbol in global_pairs:
                global_pairs.remove(symbol)
                success = await self._set_global_trading_pairs(global_pairs)
                if success:
                    await update.callback_query.answer(
                        f"✅ Removed {symbol} from global pairs"
                    )
                    await self.global_pairs_command(update, context)
                else:
                    await update.callback_query.answer("❌ Error removing global pair")
            else:
                await update.callback_query.answer(f"❌ {symbol} not in global pairs")

        except Exception as e:
            logger.error(f"Error removing global pair: {e}")
            await update.callback_query.answer("❌ Error removing global pair")

    async def _update_global_interval(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        interval_type: str,
        value: int,
    ):
        """Update a global notification interval."""
        try:
            # Check if user is admin
            if not await self._is_admin(update):
                await update.callback_query.answer("❌ Access denied")
                return

            global_intervals = await self._get_global_notification_intervals()

            if interval_type == "performance":
                global_intervals[f"{interval_type}_hours"] = value
            else:
                global_intervals[f"{interval_type}_minutes"] = value

            success = await self._set_global_notification_intervals(global_intervals)
            if success:
                unit = "hours" if interval_type == "performance" else "minutes"
                await update.callback_query.answer(
                    f"✅ Global {interval_type} interval set to {value} {unit}"
                )
                await self.global_intervals_command(update, context)
            else:
                await update.callback_query.answer(
                    f"❌ Error updating global {interval_type} interval"
                )

        except Exception as e:
            logger.error(f"Error updating global interval: {e}")
            await update.callback_query.answer(
                f"❌ Error updating global {interval_type} interval"
            )

    async def _handle_admin_error(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, section: str
    ):
        """Handle admin errors."""
        error_message = (
            f"❌ **Error Loading {section.title()}**\n\n"
            f"There was an issue loading admin {section} settings.\n"
            f"Please try again in a moment."
        )
        keyboard = create_keyboard(
            [[("🔄 Retry", f"admin_{section}"), ("⬅️ Back", "admin_global")]]
        )

        await self.edit_message(update, context, error_message, keyboard)

    async def _add_global_pair_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle adding a global trading pair."""
        if not await self._is_admin(update):
            await update.callback_query.answer("❌ Access denied")
            return

        # This would typically show a menu to select pairs
        await update.callback_query.answer("ℹ️ Use the menu to add pairs")
        await self.global_pairs_command(update, context)

    async def _remove_global_pair_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle removing a global trading pair."""
        if not await self._is_admin(update):
            await update.callback_query.answer("❌ Access denied")
            return

        # This would typically show a menu to select pairs to remove
        await update.callback_query.answer("ℹ️ Use the menu to remove pairs")
        await self.global_pairs_command(update, context)

    async def _reset_global_pairs_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle resetting global trading pairs."""
        if not await self._is_admin(update):
            await update.callback_query.answer("❌ Access denied")
            return

        try:
            default_pairs = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"]
            success = await self._set_global_trading_pairs(default_pairs)
            if success:
                await update.callback_query.answer(
                    "✅ Global trading pairs reset to defaults"
                )
                await self.global_pairs_command(update, context)
            else:
                await update.callback_query.answer(
                    "❌ Error resetting global trading pairs"
                )
        except Exception as e:
            logger.error(f"Error resetting global trading pairs: {e}")
            await update.callback_query.answer(
                "❌ Error resetting global trading pairs"
            )

    async def _set_global_interval_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle setting global notification intervals."""
        if not await self._is_admin(update):
            await update.callback_query.answer("❌ Access denied")
            return

        # This would typically show a menu to set intervals
        await update.callback_query.answer("ℹ️ Use the menu to set intervals")
        await self.global_intervals_command(update, context)

    async def _reset_global_intervals_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle resetting global notification intervals."""
        if not await self._is_admin(update):
            await update.callback_query.answer("❌ Access denied")
            return

        try:
            default_intervals = {
                "signals_minutes": 5,
                "positions_minutes": 1,
                "risk_minutes": 15,
                "performance_hours": 4,
                "system_minutes": 30,
            }
            success = await self._set_global_notification_intervals(default_intervals)
            if success:
                await update.callback_query.answer(
                    "✅ Global notification intervals reset to defaults"
                )
                await self.global_intervals_command(update, context)
            else:
                await update.callback_query.answer(
                    "❌ Error resetting global notification intervals"
                )
        except Exception as e:
            logger.error(f"Error resetting global notification intervals: {e}")
            await update.callback_query.answer(
                "❌ Error resetting global notification intervals"
            )
