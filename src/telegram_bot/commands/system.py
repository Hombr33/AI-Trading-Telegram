"""System commands for Telegram bot."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.services.user_config_service import UserConfigService
from src.telegram_bot.services.system_data_service import SystemDataService
from src.telegram_bot.utils.keyboards import create_keyboard

from .base import BaseCommandHandler

logger = get_logger(__name__)


class SystemCommandHandler(BaseCommandHandler):
    """System command handler for Telegram bot."""

    def __init__(self):
        super().__init__()
        self.system_service = SystemDataService()
        self.user_config_service = UserConfigService()
        self._register_commands()
        self._register_callbacks()

    def _register_commands(self):
        """Register system commands."""
        self.commands = {
            "start": self.start_command,
            "help": self.help_command,
            "status": self.status_command,
            "settings": self.settings_command,
            "health": self.health_command,
            "info": self.info_command,
        }

    def _register_callbacks(self):
        """Register system callbacks."""
        self.callbacks = {
            "status": self.status_command,
            "refresh_status": self.status_command,
            "health": self.health_command,
            "refresh_health": self.health_command,
            "info": self.info_command,
            "refresh_info": self.info_command,
            "settings": self.settings_command,
            "settings_notifications": self.settings_notifications,
            "settings_trading": self.settings_trading,
            "settings_risk": self.settings_risk,
            "settings_system": self.settings_system,
            "toggle_notification": self.toggle_notification_callback,
            "toggle_auto_trading": self.toggle_auto_trading_callback,
            "back_to_settings": self.settings_command,
        }

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Get user info
            user = update.effective_user
            first_name = user.first_name or "Trader"

            # Get system status for welcome message
            system_status = await self.system_service.get_system_status()

            welcome_message = (
                f"🚀 **Welcome to AI Trading Bot, {first_name}!** 🚀\n\n"
                f"🤖 **Bot Status**: {system_status['bot_status']}\n"
                f"📊 **MT5 Connection**: {system_status['mt5_connection']}\n"
                f"⚡ **AI Analyzer**: {system_status['ai_analyzer']}\n"
                f"🛡️ **Risk Manager**: {system_status['risk_manager']}\n\n"
                f"**Quick Commands**:\n"
                f"📊 `/status` - System status\n"
                f"📈 `/positions` - Open positions\n"
                f"📋 `/orders` - Pending orders\n"
                f"💰 `/account` - Account info\n"
                f"📊 `/performance` - Performance metrics\n"
                f"⚠️ `/risk` - Risk analysis\n"
                f"📖 `/journal` - Trading journal\n"
                f"🔍 `/signals` - Trading signals\n"
                f"⚙️ `/settings` - Bot settings\n"
                f"❓ `/help` - Help menu\n\n"
                f"**System Uptime**: {system_status['uptime']}\n"
                f"**Last Update**: {system_status['last_update']}"
            )

            # Create welcome keyboard
            keyboard = create_keyboard(
                [
                    [("📊 Status", "status"), ("📈 Positions", "positions")],
                    [("💰 Account", "account"), ("📋 Orders", "orders")],
                    [("📊 Performance", "performance"), ("⚠️ Risk", "risk")],
                    [("🔍 Signals", "signals"), ("⚙️ Settings", "settings")],
                ]
            )

            await self.send_message(update, context, welcome_message, keyboard)

        except Exception as e:
            logger.error(f"Error in start command: {e}")
            error_message = (
                f"❌ **Welcome Error**\n\n"
                f"There was an issue starting the bot.\n"
                f"Please try again in a moment."
            )
            await self.send_message(update, context, error_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            help_message = (
                f"❓ **HELP MENU** ❓\n\n"
                f"**Trading Commands**:\n"
                f"📈 `/positions` - View open positions\n"
                f"📋 `/orders` - View pending orders\n"
                f"💰 `/account` - Account information\n"
                f"🔍 `/signals` - Trading signals\n\n"
                f"**Analysis Commands**:\n"
                f"📊 `/performance` - Performance metrics\n"
                f"⚠️ `/risk` - Risk analysis\n"
                f"📖 `/journal` - Trading journal\n"
                f"🔍 `/analysis` - Market analysis\n\n"
                f"**System Commands**:\n"
                f"📊 `/status` - System status\n"
                f"⚙️ `/settings` - Bot settings\n"
                f"🏥 `/health` - System health\n"
                f"ℹ️ `/info` - System information\n\n"
                f"**Admin Commands**:\n"
                f"👑 `/admin` - Admin panel\n"
                f"👥 `/users` - User management\n"
                f"📋 `/logs` - System logs\n"
                f"🔄 `/restart` - Restart system\n\n"
                f"**Need More Help?**\n"
                f"Contact support or check documentation for detailed information."
            )

            # Create help keyboard
            keyboard = create_keyboard(
                [
                    [("📊 Status", "status"), ("📈 Positions", "positions")],
                    [("💰 Account", "account"), ("📊 Performance", "performance")],
                    [("⚠️ Risk", "risk"), ("🔍 Signals", "signals")],
                    [("⚙️ Settings", "settings"), ("🏥 Health", "health")],
                ]
            )

            await self.send_message(update, context, help_message, keyboard)

        except Exception as e:
            logger.error(f"Error in help command: {e}")
            error_message = (
                f"❌ **Help Error**\n\n"
                f"There was an issue loading help information.\n"
                f"Please try again in a moment."
            )
            await self.send_message(update, context, error_message)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /status command.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Get real system status data
            system_status = await self.system_service.get_system_status()

            # Format the status message
            status_emoji = "🟢" if system_status["status"] == "Online" else "🔴"
            mt5_emoji = "🟢" if system_status["mt5_connection"] == "Connected" else "🔴"
            ai_emoji = "🟢" if system_status["ai_analyzer"] == "Active" else "🔴"
            risk_emoji = "🟢" if system_status["risk_manager"] == "Active" else "🔴"

            message = (
                f"📊 **SYSTEM STATUS** 📊\n\n"
                f"{status_emoji} **Bot Status**: {system_status['bot_status']}\n"
                f"{mt5_emoji} **MT5 Connection**: {system_status['mt5_connection']}\n"
                f"{ai_emoji} **AI Analyzer**: {system_status['ai_analyzer']}\n"
                f"{risk_emoji} **Risk Manager**: {system_status['risk_manager']}\n\n"
                f"**System Metrics**:\n"
                f"🕐 Uptime: {system_status['uptime']}\n"
                f"💻 CPU Usage: {system_status['cpu_usage']:.1f}%\n"
                f"🧠 Memory Usage: {system_status['memory_usage']:.1f}%\n"
                f"📉 Daily Drawdown: {system_status['daily_drawdown']:.2f}%\n\n"
                f"**Trading Status**:\n"
                f"📈 Open Positions: {system_status['open_positions']}\n"
                f"📋 Pending Orders: {system_status['pending_orders']}\n"
                f"🔍 Pending Signals: {system_status['pending_signals']}\n"
                f"🎯 Active Strategies: {system_status['active_strategies']}\n\n"
                f"**Last Updated**: {system_status['last_update']}"
            )

            # Create status keyboard
            keyboard = create_keyboard(
                [
                    [("🔄 Refresh", "refresh_status"), ("🏥 Health", "health")],
                    [("📈 Positions", "positions"), ("📋 Orders", "orders")],
                    [("💰 Account", "account"), ("📊 Performance", "performance")],
                    [("⚙️ Settings", "settings"), ("🏠 Menu", "start")],
                ]
            )

            # If this is a callback query, edit the message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in status command: {e}")
            error_message = (
                f"❌ **Error Loading Status**\n\n"
                f"There was an issue loading system status.\n"
                f"Please try again in a moment."
            )
            keyboard = create_keyboard(
                [[("🔄 Retry", "refresh_status"), ("🏥 Health", "health")]]
            )

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)

    async def health_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /health command.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Get real health status data
            health_status = await self.system_service.get_health_status()

            # Format the health message
            health_emoji = {
                "Healthy": "🟢",
                "Warning": "🟡",
                "Critical": "🔴",
                "Unknown": "⚪",
            }

            overall_emoji = health_emoji.get(health_status["overall_health"], "⚪")

            message = (
                f"🏥 **SYSTEM HEALTH CHECK** 🏥\n\n"
                f"{overall_emoji} **Overall Health**: {health_status['overall_health']}\n"
                f"🕐 **Last Check**: {health_status['last_check'][:19]}\n\n"
                f"**Component Status**:\n"
            )

            # Add component statuses
            for component_name, component in health_status["components"].items():
                severity_emoji = {"info": "🟢", "warning": "🟡", "error": "🔴"}
                emoji = severity_emoji.get(component.get("severity", "info"), "⚪")
                message += (
                    f"{emoji} **{component_name.title()}**: {component['status']}\n"
                )

            # Add recommendations
            if health_status["recommendations"]:
                message += f"\n**Recommendations**:\n"
                for rec in health_status["recommendations"]:
                    message += f"💡 {rec}\n"

            # Create health keyboard
            keyboard = create_keyboard(
                [
                    [("🔄 Refresh", "refresh_health"), ("📊 Status", "status")],
                    [("ℹ️ Info", "info"), ("⚙️ Settings", "settings")],
                    [("📈 Positions", "positions"), ("💰 Account", "account")],
                ]
            )

            # If this is a callback query, edit the message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in health command: {e}")
            error_message = (
                f"❌ **Error Loading Health**\n\n"
                f"There was an issue loading health status.\n"
                f"Please try again in a moment."
            )
            keyboard = create_keyboard(
                [[("🔄 Retry", "refresh_health"), ("📊 Status", "status")]]
            )

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)

    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /info command.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Get real system info data
            system_info = await self.system_service.get_system_info()

            # Format the info message
            message = (
                f"ℹ️ **SYSTEM INFORMATION** ℹ️\n\n"
                f"**Resource Usage**:\n"
                f"💻 CPU: {system_info['cpu_usage']:.1f}%\n"
                f"🧠 Memory: {system_info['memory_usage']:.1f}%\n"
                f"💾 Disk: {system_info['disk_usage']:.1f}%\n"
                f"🌐 Network Latency: {system_info['network_latency']}ms\n\n"
                f"**System Details**:\n"
                f"🕐 Uptime: {system_info['uptime']}\n"
                f"💾 Last Backup: {system_info['last_backup']}\n"
                f"❌ Errors (24h): {system_info['errors_24h']}\n"
                f"⚠️ Warnings (24h): {system_info['warnings_24h']}\n\n"
                f"**Platform Info**:\n"
                f"🖥️ Platform: {system_info['system_info']['platform']}\n"
                f"🐍 Python: {system_info['system_info']['python_version']}\n"
                f"🏗️ Architecture: {system_info['system_info']['architecture']}\n"
                f"🖥️ Hostname: {system_info['system_info']['hostname']}\n\n"
                f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Create info keyboard
            keyboard = create_keyboard(
                [
                    [("🔄 Refresh", "refresh_info"), ("🏥 Health", "health")],
                    [("📊 Status", "status"), ("⚙️ Settings", "settings")],
                    [("📈 Positions", "positions"), ("💰 Account", "account")],
                ]
            )

            # If this is a callback query, edit the message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in info command: {e}")
            error_message = (
                f"❌ **Error Loading Info**\n\n"
                f"There was an issue loading system information.\n"
                f"Please try again in a moment."
            )
            keyboard = create_keyboard(
                [[("🔄 Retry", "refresh_info"), ("📊 Status", "status")]]
            )

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)

    async def settings_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle the /settings command - Main settings menu.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)

            # Get quick stats from config
            auto_trading = config.get("trading", {}).get("auto_trading", False)
            risk_per_trade = config.get("trading", {}).get("risk_per_trade_pct", 2.0)
            max_positions = config.get("trading", {}).get("max_open_positions", 5)

            # Count active notifications
            notifications = config.get("notifications", {})
            active_notifications = sum(1 for v in notifications.values() if v)

            message = (
                f"⚙️ **USER SETTINGS** ⚙️\n\n"
                f"**Current Configuration**:\n"
                f"🤖 Auto Trading: {'✅ Enabled' if auto_trading else '❌ Disabled'}\n"
                f"📊 Risk per Trade: {risk_per_trade}%\n"
                f"🎯 Max Positions: {max_positions}\n"
                f"🔔 Active Notifications: {active_notifications}/6\n\n"
                f"**Configure Your Settings**:\n"
                f"Select a category below to customize your trading bot experience."
            )

            # Create settings keyboard
            keyboard = create_keyboard(
                [
                    [
                        ("🔔 Notifications", "settings_notifications"),
                        ("📊 Trading", "settings_trading"),
                    ],
                    [
                        ("⚠️ Risk Management", "settings_risk"),
                        ("🔧 System", "settings_system"),
                    ],
                    [("📈 Trading", "positions"), ("💰 Account", "account")],
                    [("🏠 Main Menu", "start")],
                ]
            )

            # If this is a callback query, edit the message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in settings command: {e}")
            error_message = (
                f"❌ **Error Loading Settings**\n\n"
                f"There was an issue loading your settings.\n"
                f"Please try again in a moment."
            )
            keyboard = create_keyboard(
                [[("🔄 Retry", "settings"), ("🏠 Main Menu", "start")]]
            )

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)

    async def settings_notifications(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle notifications settings submenu."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            notifications = config.get("notifications", {})

            # Create status indicators
            def status_icon(enabled):
                return "✅" if enabled else "❌"

            message = (
                f"🔔 **NOTIFICATION SETTINGS** 🔔\n\n"
                f"**Current Status**:\n"
                f"{status_icon(notifications.get('signals', True))} Trading Signals\n"
                f"{status_icon(notifications.get('positions', True))} Position Updates\n"
                f"{status_icon(notifications.get('orders', True))} Order Updates\n"
                f"{status_icon(notifications.get('risk', True))} Risk Alerts\n"
                f"{status_icon(notifications.get('performance', True))} Performance Reports\n"
                f"{status_icon(notifications.get('system', True))} System Alerts\n\n"
                f"**Toggle Notifications**:\n"
                f"Click any notification type below to enable/disable it."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("📈 Signals", "toggle_notification:signals"),
                        ("📊 Positions", "toggle_notification:positions"),
                    ],
                    [
                        ("📋 Orders", "toggle_notification:orders"),
                        ("⚠️ Risk", "toggle_notification:risk"),
                    ],
                    [
                        ("📊 Performance", "toggle_notification:performance"),
                        ("🔧 System", "toggle_notification:system"),
                    ],
                    [("⬅️ Back", "back_to_settings"), ("🏠 Main", "start")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in notifications settings: {e}")
            await self._handle_settings_error(update, context, "notifications")

    async def settings_trading(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle trading settings submenu."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            trading = config.get("trading", {})

            message = (
                f"📊 **TRADING SETTINGS** 📊\n\n"
                f"**Current Configuration**:\n"
                f"🤖 Auto Trading: {'✅ Enabled' if trading.get('auto_trading', False) else '❌ Disabled'}\n"
                f"📈 Risk per Trade: {trading.get('risk_per_trade_pct', 2.0)}%\n"
                f"🎯 Max Positions: {trading.get('max_open_positions', 5)}\n"
                f"💰 Max Daily Loss: ${trading.get('max_daily_loss_usd', 25.0)}\n"
                f"📋 Allowed Symbols: {len(trading.get('allowed_symbols', []))}\n\n"
                f"**Quick Actions**:\n"
                f"Select a setting to modify:"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("🤖 Auto Trading", "toggle_auto_trading"),
                        ("📈 Risk %", "edit_risk_percent"),
                    ],
                    [
                        ("🎯 Max Positions", "edit_max_positions"),
                        ("💰 Daily Loss", "edit_daily_loss"),
                    ],
                    [
                        ("📋 Symbols", "manage_symbols"),
                        ("🔄 Reset Defaults", "reset_trading"),
                    ],
                    [("⬅️ Back", "back_to_settings"), ("🏠 Main", "start")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in trading settings: {e}")
            await self._handle_settings_error(update, context, "trading")

    async def settings_risk(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle risk management settings submenu."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            risk = config.get("risk", {})

            message = (
                f"⚠️ **RISK MANAGEMENT** ⚠️\n\n"
                f"**Current Settings**:\n"
                f"📉 Max Drawdown: {risk.get('max_drawdown_pct', 15.0)}%\n"
                f"💸 Daily Loss Limit: {risk.get('max_daily_loss_pct', 5.0)}%\n"
                f"💼 Max Position Size: {risk.get('max_position_size_pct', 10.0)}%\n"
                f"🛑 Stop After Losses: {risk.get('stop_on_consecutive_losses', 4)}\n\n"
                f"**Risk Controls**:\n"
                f"These settings protect your account from excessive losses."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("📉 Drawdown %", "edit_max_drawdown"),
                        ("💸 Daily Loss %", "edit_daily_loss_pct"),
                    ],
                    [
                        ("💼 Position Size %", "edit_position_size"),
                        ("🛑 Stop Losses", "edit_stop_losses"),
                    ],
                    [
                        ("🔄 Reset Defaults", "reset_risk"),
                        ("📊 Risk Report", "risk_report"),
                    ],
                    [("⬅️ Back", "back_to_settings"), ("🏠 Main", "start")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in risk settings: {e}")
            await self._handle_settings_error(update, context, "risk")

    async def settings_system(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle system settings submenu."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            system = config.get("system", {})

            message = (
                f"🔧 **SYSTEM SETTINGS** 🔧\n\n"
                f"**Current Configuration**:\n"
                f"🌍 Timezone: {system.get('timezone', 'UTC')}\n"
                f"⏱️ Update Frequency: {system.get('update_frequency_seconds', 60)}s\n"
                f"📝 Log Level: {system.get('log_level', 'INFO')}\n"
                f"📊 Timeframe: {system.get('preferred_timeframe', 'H1')}\n\n"
                f"**System Preferences**:\n"
                f"Configure how the bot operates and displays information."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("🌍 Timezone", "edit_timezone"),
                        ("⏱️ Update Rate", "edit_update_freq"),
                    ],
                    [
                        ("📝 Log Level", "edit_log_level"),
                        ("📊 Timeframe", "edit_timeframe"),
                    ],
                    [
                        ("🔄 Reset Defaults", "reset_system"),
                        ("📊 System Info", "system_info"),
                    ],
                    [("⬅️ Back", "back_to_settings"), ("🏠 Main", "start")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in system settings: {e}")
            await self._handle_settings_error(update, context, "system")

    async def toggle_notification_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle notification toggle callbacks."""
        try:
            query = update.callback_query
            notification_type = query.data.split(":")[1]
            telegram_id = update.effective_user.id

            # Toggle the notification
            new_state = await self.user_config_service.toggle_notification(
                telegram_id, notification_type
            )

            # Show confirmation
            state_text = "enabled" if new_state else "disabled"
            await query.answer(
                f"✅ {notification_type.title()} notifications {state_text}"
            )

            # Refresh the notifications settings page
            await self.settings_notifications(update, context)

        except Exception as e:
            logger.error(f"Error toggling notification: {e}")
            await update.callback_query.answer("❌ Error updating notification setting")

    async def _handle_settings_error(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, section: str
    ):
        """Handle settings errors."""
        error_message = (
            f"❌ **Error Loading {section.title()} Settings**\n\n"
            f"There was an issue loading your {section} settings.\n"
            f"Please try again in a moment."
        )
        keyboard = create_keyboard(
            [[("🔄 Retry", f"settings_{section}"), ("⬅️ Back", "back_to_settings")]]
        )

        await self.edit_message(update, context, error_message, keyboard)

    async def toggle_auto_trading_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle auto trading toggle callback."""
        try:
            telegram_id = update.effective_user.id

            # Get current config
            config = await self.user_config_service.get_user_config(telegram_id)
            current_state = config.get("trading", {}).get("auto_trading", False)
            new_state = not current_state

            # Update the setting
            success = await self.user_config_service.update_user_config(
                telegram_id, "trading", "auto_trading", new_state
            )

            if success:
                state_text = "enabled" if new_state else "disabled"
                await update.callback_query.answer(f"✅ Auto trading {state_text}")
                # Refresh the trading settings page
                await self.settings_trading(update, context)
            else:
                await update.callback_query.answer(
                    "❌ Error updating auto trading setting"
                )

        except Exception as e:
            logger.error(f"Error toggling auto trading: {e}")
            await update.callback_query.answer("❌ Error updating auto trading setting")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in command processing.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            error_message = (
                f"❌ **Command Error**\n\n"
                f"An error occurred while processing your command.\n"
                f"Please try again or contact support if the issue persists.\n\n"
                f"**Error Details**: {context.error}\n"
                f"**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Create error keyboard
            keyboard = create_keyboard(
                [
                    [("🔄 Retry", "start"), ("📊 Status", "status")],
                    [("❓ Help", "help"), ("🏠 Menu", "start")],
                ]
            )

            await self.send_message(update, context, error_message, keyboard)

        except Exception as e:
            logger.error(f"Error in error handler: {e}")
            # Fallback error message
            fallback_message = (
                f"❌ **System Error**\n\n"
                f"A critical error occurred.\n"
                f"Please contact support immediately."
            )
            await self.send_message(update, context, fallback_message)
