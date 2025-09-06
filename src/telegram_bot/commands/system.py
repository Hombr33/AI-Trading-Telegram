"""System commands for Telegram bot."""

from datetime import datetime

from telegram import Update
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
            "manage_symbols": self.manage_symbols_callback,
            "edit_risk_percent": self.edit_risk_percent_callback,
            "edit_max_positions": self.edit_max_positions_callback,
            "edit_daily_loss": self.edit_daily_loss_callback,
            "reset_trading": self.reset_trading_callback,
            "edit_max_drawdown": self.edit_max_drawdown_callback,
            "edit_daily_loss_pct": self.edit_daily_loss_pct_callback,
            "edit_position_size": self.edit_position_size_callback,
            "edit_stop_losses": self.edit_stop_losses_callback,
            "reset_risk": self.reset_risk_callback,
            "risk_report": self.risk_report_callback,
            "edit_timezone": self.edit_timezone_callback,
            "edit_update_freq": self.edit_update_freq_callback,
            "edit_log_level": self.edit_log_level_callback,
            "edit_timeframe": self.edit_timeframe_callback,
            "reset_system": self.reset_system_callback,
            "system_info": self.info_command,
            "notification_intervals": self.notification_intervals_callback,
            "notification_trading_pairs": self.notification_trading_pairs_callback,
            "set_interval": self.set_interval_callback,
            "trading_pairs": self.trading_pairs_callback,
            "add_trading_pair": self.add_trading_pair_callback,
            "remove_trading_pair": self.remove_trading_pair_callback,
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
                "❌ **Welcome Error**\n\n"
                "There was an issue starting the bot.\n"
                "Please try again in a moment."
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
                "❓ **HELP MENU** ❓\n\n"
                "**Trading Commands**:\n"
                "📈 `/positions` - View open positions\n"
                "📋 `/orders` - View pending orders\n"
                "💰 `/account` - Account information\n"
                "🔍 `/signals` - Trading signals\n\n"
                "**Analysis Commands**:\n"
                "📊 `/performance` - Performance metrics\n"
                "⚠️ `/risk` - Risk analysis\n"
                "📖 `/journal` - Trading journal\n"
                "🔍 `/analysis` - Market analysis\n\n"
                "**System Commands**:\n"
                "📊 `/status` - System status\n"
                "⚙️ `/settings` - Bot settings\n"
                "🏥 `/health` - System health\n"
                "ℹ️ `/info` - System information\n\n"
                "**Admin Commands**:\n"
                "👑 `/admin` - Admin panel\n"
                "👥 `/users` - User management\n"
                "📋 `/logs` - System logs\n"
                "🔄 `/restart` - Restart system\n\n"
                "**Need More Help?**\n"
                "Contact support or check documentation for detailed information."
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
                "❌ **Help Error**\n\n"
                "There was an issue loading help information.\n"
                "Please try again in a moment."
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
                "❌ **Error Loading Status**\n\n"
                "There was an issue loading system status.\n"
                "Please try again in a moment."
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
                message += "\n**Recommendations**:\n"
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
                "❌ **Error Loading Health**\n\n"
                "There was an issue loading health status.\n"
                "Please try again in a moment."
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
                "❌ **Error Loading Info**\n\n"
                "There was an issue loading system information.\n"
                "Please try again in a moment."
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
                    [
                        ("⏰ Intervals", "notification_intervals"),
                        ("📈 Performance", "performance"),
                    ],
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
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading your settings.\n"
                "Please try again in a moment."
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

            # Get trading config for allowed symbols
            trading = config.get("trading", {})
            allowed_symbols = trading.get("allowed_symbols", [])

            message = (
                f"🔔 **NOTIFICATION SETTINGS** 🔔\n\n"
                f"**Current Status**:\n"
                f"{status_icon(notifications.get('signals', True))} Trading Signals\n"
                f"{status_icon(notifications.get('positions', True))} Position Updates\n"
                f"{status_icon(notifications.get('orders', True))} Order Updates\n"
                f"{status_icon(notifications.get('risk', True))} Risk Alerts\n"
                f"{status_icon(notifications.get('performance', True))} Performance Reports\n"
                f"{status_icon(notifications.get('system', True))} System Alerts\n\n"
                f"**Trading Pairs**: {len(allowed_symbols)} pairs configured\n"
                f"**Configure**: Select options below to customize notifications."
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
                    [
                        ("📋 Trading Pairs", "notification_trading_pairs"),
                        ("⏰ Intervals", "notification_intervals"),
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
                "❌ **System Error**\n\n"
                "A critical error occurred.\n"
                "Please contact support immediately."
            )
            await self.send_message(update, context, fallback_message)

    # Trading Settings Callbacks
    async def manage_symbols_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle manage symbols callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            allowed_symbols = config.get("trading", {}).get("allowed_symbols", [])

            message = (
                f"📋 **MANAGE TRADING SYMBOLS** 📋\n\n"
                f"**Current Allowed Symbols**:\n"
            )

            if allowed_symbols:
                for symbol in allowed_symbols:
                    message += f"• {symbol}\n"
            else:
                message += "• No symbols configured\n"

            message += f"\n**Total**: {len(allowed_symbols)} symbols\n\n"
            message += "**Available Actions**:\n"
            message += "• Add new trading pairs\n"
            message += "• Remove existing pairs\n"
            message += "• Reset to default pairs"

            keyboard = create_keyboard(
                [
                    [
                        ("➕ Add Symbol", "add_trading_pair"),
                        ("➖ Remove Symbol", "remove_trading_pair"),
                    ],
                    [
                        ("🔄 Reset Defaults", "reset_symbols"),
                        ("📋 View All", "view_all_symbols"),
                    ],
                    [("⬅️ Back", "settings_trading"), ("🏠 Main", "start")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in manage_symbols_callback: {e}")
            await self._handle_settings_error(update, context, "symbols")

    async def edit_risk_percent_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle edit risk percent callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            current_risk = config.get("trading", {}).get("risk_per_trade_pct", 2.0)

            message = (
                f"📈 **EDIT RISK PER TRADE** 📈\n\n"
                f"**Current Risk**: {current_risk}%\n\n"
                f"**Select New Risk Level**:\n"
                f"Choose a risk percentage for each trade."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("0.5%", "set_risk:0.5"),
                        ("1.0%", "set_risk:1.0"),
                        ("1.5%", "set_risk:1.5"),
                    ],
                    [
                        ("2.0%", "set_risk:2.0"),
                        ("2.5%", "set_risk:2.5"),
                        ("3.0%", "set_risk:3.0"),
                    ],
                    [("Custom", "custom_risk"), ("⬅️ Back", "settings_trading")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in edit_risk_percent_callback: {e}")
            await self._handle_settings_error(update, context, "risk")

    async def edit_max_positions_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle edit max positions callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            current_max = config.get("trading", {}).get("max_open_positions", 5)

            message = (
                f"🎯 **EDIT MAX POSITIONS** 🎯\n\n"
                f"**Current Max**: {current_max} positions\n\n"
                f"**Select New Maximum**:\n"
                f"Choose maximum number of open positions."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("1", "set_max_pos:1"),
                        ("2", "set_max_pos:2"),
                        ("3", "set_max_pos:3"),
                    ],
                    [
                        ("5", "set_max_pos:5"),
                        ("10", "set_max_pos:10"),
                        ("15", "set_max_pos:15"),
                    ],
                    [("Custom", "custom_max_pos"), ("⬅️ Back", "settings_trading")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in edit_max_positions_callback: {e}")
            await self._handle_settings_error(update, context, "positions")

    async def edit_daily_loss_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle edit daily loss callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            current_loss = config.get("trading", {}).get("max_daily_loss_usd", 25.0)

            message = (
                f"💰 **EDIT DAILY LOSS LIMIT** 💰\n\n"
                f"**Current Limit**: ${current_loss}\n\n"
                f"**Select New Limit**:\n"
                f"Choose maximum daily loss in USD."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("$10", "set_daily_loss:10"),
                        ("$25", "set_daily_loss:25"),
                        ("$50", "set_daily_loss:50"),
                    ],
                    [
                        ("$100", "set_daily_loss:100"),
                        ("$200", "set_daily_loss:200"),
                        ("$500", "set_daily_loss:500"),
                    ],
                    [("Custom", "custom_daily_loss"), ("⬅️ Back", "settings_trading")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in edit_daily_loss_callback: {e}")
            await self._handle_settings_error(update, context, "daily_loss")

    async def reset_trading_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle reset trading settings callback."""
        try:
            telegram_id = update.effective_user.id

            # Reset to default trading settings
            default_trading = {
                "auto_trading": False,
                "risk_per_trade_pct": 2.0,
                "max_open_positions": 5,
                "max_daily_loss_usd": 25.0,
                "allowed_symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"],
            }

            success = await self.user_config_service.update_user_config(
                telegram_id, "trading", None, default_trading
            )

            if success:
                await update.callback_query.answer(
                    "✅ Trading settings reset to defaults"
                )
                await self.settings_trading(update, context)
            else:
                await update.callback_query.answer(
                    "❌ Error resetting trading settings"
                )

        except Exception as e:
            logger.error(f"Error in reset_trading_callback: {e}")
            await update.callback_query.answer("❌ Error resetting trading settings")

    # Risk Management Callbacks
    async def edit_max_drawdown_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle edit max drawdown callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            current_drawdown = config.get("risk", {}).get("max_drawdown_pct", 15.0)

            message = (
                f"📉 **EDIT MAX DRAWDOWN** 📉\n\n"
                f"**Current Limit**: {current_drawdown}%\n\n"
                f"**Select New Limit**:\n"
                f"Choose maximum drawdown percentage."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("5%", "set_drawdown:5"),
                        ("10%", "set_drawdown:10"),
                        ("15%", "set_drawdown:15"),
                    ],
                    [
                        ("20%", "set_drawdown:20"),
                        ("25%", "set_drawdown:25"),
                        ("30%", "set_drawdown:30"),
                    ],
                    [("Custom", "custom_drawdown"), ("⬅️ Back", "settings_risk")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in edit_max_drawdown_callback: {e}")
            await self._handle_settings_error(update, context, "drawdown")

    async def edit_daily_loss_pct_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle edit daily loss percentage callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            current_loss_pct = config.get("risk", {}).get("max_daily_loss_pct", 5.0)

            message = (
                f"💸 **EDIT DAILY LOSS %** 💸\n\n"
                f"**Current Limit**: {current_loss_pct}%\n\n"
                f"**Select New Limit**:\n"
                f"Choose maximum daily loss percentage."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("2%", "set_daily_loss_pct:2"),
                        ("3%", "set_daily_loss_pct:3"),
                        ("5%", "set_daily_loss_pct:5"),
                    ],
                    [
                        ("7%", "set_daily_loss_pct:7"),
                        ("10%", "set_daily_loss_pct:10"),
                        ("15%", "set_daily_loss_pct:15"),
                    ],
                    [("Custom", "custom_daily_loss_pct"), ("⬅️ Back", "settings_risk")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in edit_daily_loss_pct_callback: {e}")
            await self._handle_settings_error(update, context, "daily_loss_pct")

    async def edit_position_size_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle edit position size callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            current_size = config.get("risk", {}).get("max_position_size_pct", 10.0)

            message = (
                f"💼 **EDIT POSITION SIZE** 💼\n\n"
                f"**Current Limit**: {current_size}%\n\n"
                f"**Select New Limit**:\n"
                f"Choose maximum position size percentage."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("5%", "set_position_size:5"),
                        ("10%", "set_position_size:10"),
                        ("15%", "set_position_size:15"),
                    ],
                    [
                        ("20%", "set_position_size:20"),
                        ("25%", "set_position_size:25"),
                        ("30%", "set_position_size:30"),
                    ],
                    [("Custom", "custom_position_size"), ("⬅️ Back", "settings_risk")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in edit_position_size_callback: {e}")
            await self._handle_settings_error(update, context, "position_size")

    async def edit_stop_losses_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle edit stop losses callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            current_stop = config.get("risk", {}).get("stop_on_consecutive_losses", 4)

            message = (
                f"🛑 **EDIT STOP AFTER LOSSES** 🛑\n\n"
                f"**Current Setting**: {current_stop} consecutive losses\n\n"
                f"**Select New Setting**:\n"
                f"Choose when to stop trading after losses."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("2", "set_stop_losses:2"),
                        ("3", "set_stop_losses:3"),
                        ("4", "set_stop_losses:4"),
                    ],
                    [
                        ("5", "set_stop_losses:5"),
                        ("6", "set_stop_losses:6"),
                        ("7", "set_stop_losses:7"),
                    ],
                    [("Custom", "custom_stop_losses"), ("⬅️ Back", "settings_risk")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in edit_stop_losses_callback: {e}")
            await self._handle_settings_error(update, context, "stop_losses")

    async def reset_risk_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle reset risk settings callback."""
        try:
            telegram_id = update.effective_user.id

            # Reset to default risk settings
            default_risk = {
                "max_drawdown_pct": 15.0,
                "max_daily_loss_pct": 5.0,
                "max_position_size_pct": 10.0,
                "stop_on_consecutive_losses": 4,
            }

            success = await self.user_config_service.update_user_config(
                telegram_id, "risk", None, default_risk
            )

            if success:
                await update.callback_query.answer("✅ Risk settings reset to defaults")
                await self.settings_risk(update, context)
            else:
                await update.callback_query.answer("❌ Error resetting risk settings")

        except Exception as e:
            logger.error(f"Error in reset_risk_callback: {e}")
            await update.callback_query.answer("❌ Error resetting risk settings")

    async def risk_report_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle risk report callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            risk_config = config.get("risk", {})

            message = (
                f"📊 **RISK MANAGEMENT REPORT** 📊\n\n"
                f"**Current Risk Settings**:\n"
                f"📉 Max Drawdown: {risk_config.get('max_drawdown_pct', 15.0)}%\n"
                f"💸 Daily Loss Limit: {risk_config.get('max_daily_loss_pct', 5.0)}%\n"
                f"💼 Max Position Size: {risk_config.get('max_position_size_pct', 10.0)}%\n"
                f"🛑 Stop After Losses: {risk_config.get('stop_on_consecutive_losses', 4)}\n\n"
                f"**Risk Assessment**:\n"
                f"• Conservative: Drawdown ≤ 10%, Daily Loss ≤ 3%\n"
                f"• Moderate: Drawdown ≤ 15%, Daily Loss ≤ 5%\n"
                f"• Aggressive: Drawdown ≤ 25%, Daily Loss ≤ 10%\n\n"
                f"**Recommendations**:\n"
                f"• Monitor positions daily\n"
                f"• Adjust limits based on performance\n"
                f"• Use stop losses consistently"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("📉 Edit Drawdown", "edit_max_drawdown"),
                        ("💸 Edit Daily Loss", "edit_daily_loss_pct"),
                    ],
                    [
                        ("💼 Edit Position Size", "edit_position_size"),
                        ("🛑 Edit Stop Losses", "edit_stop_losses"),
                    ],
                    [("⬅️ Back", "settings_risk"), ("🏠 Main", "start")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in risk_report_callback: {e}")
            await self._handle_settings_error(update, context, "risk_report")

    # System Settings Callbacks
    async def edit_timezone_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle edit timezone callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            current_tz = config.get("system", {}).get("timezone", "UTC")

            message = (
                f"🌍 **EDIT TIMEZONE** 🌍\n\n"
                f"**Current Timezone**: {current_tz}\n\n"
                f"**Select New Timezone**:\n"
                f"Choose your preferred timezone."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("UTC", "set_timezone:UTC"),
                        ("EST", "set_timezone:EST"),
                        ("PST", "set_timezone:PST"),
                    ],
                    [
                        ("GMT", "set_timezone:GMT"),
                        ("CET", "set_timezone:CET"),
                        ("JST", "set_timezone:JST"),
                    ],
                    [
                        ("Asia/Jakarta", "set_timezone:Asia/Jakarta"),
                        ("Custom", "custom_timezone"),
                    ],
                    [("⬅️ Back", "settings_system")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in edit_timezone_callback: {e}")
            await self._handle_settings_error(update, context, "timezone")

    async def edit_update_freq_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle edit update frequency callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            current_freq = config.get("system", {}).get("update_frequency_seconds", 60)

            message = (
                f"⏱️ **EDIT UPDATE FREQUENCY** ⏱️\n\n"
                f"**Current Frequency**: {current_freq} seconds\n\n"
                f"**Select New Frequency**:\n"
                f"Choose how often the system updates."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("30s", "set_update_freq:30"),
                        ("60s", "set_update_freq:60"),
                        ("120s", "set_update_freq:120"),
                    ],
                    [
                        ("300s", "set_update_freq:300"),
                        ("600s", "set_update_freq:600"),
                        ("1800s", "set_update_freq:1800"),
                    ],
                    [("Custom", "custom_update_freq"), ("⬅️ Back", "settings_system")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in edit_update_freq_callback: {e}")
            await self._handle_settings_error(update, context, "update_freq")

    async def edit_log_level_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle edit log level callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            current_level = config.get("system", {}).get("log_level", "INFO")

            message = (
                f"📝 **EDIT LOG LEVEL** 📝\n\n"
                f"**Current Level**: {current_level}\n\n"
                f"**Select New Level**:\n"
                f"Choose logging detail level."
            )

            keyboard = create_keyboard(
                [
                    [("DEBUG", "set_log_level:DEBUG"), ("INFO", "set_log_level:INFO")],
                    [
                        ("WARNING", "set_log_level:WARNING"),
                        ("ERROR", "set_log_level:ERROR"),
                    ],
                    [("⬅️ Back", "settings_system")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in edit_log_level_callback: {e}")
            await self._handle_settings_error(update, context, "log_level")

    async def edit_timeframe_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle edit timeframe callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            current_tf = config.get("system", {}).get("preferred_timeframe", "H1")

            message = (
                f"📊 **EDIT PREFERRED TIMEFRAME** 📊\n\n"
                f"**Current Timeframe**: {current_tf}\n\n"
                f"**Select New Timeframe**:\n"
                f"Choose your preferred trading timeframe."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("M1", "set_timeframe:M1"),
                        ("M5", "set_timeframe:M5"),
                        ("M15", "set_timeframe:M15"),
                    ],
                    [
                        ("M30", "set_timeframe:M30"),
                        ("H1", "set_timeframe:H1"),
                        ("H4", "set_timeframe:H4"),
                    ],
                    [("D1", "set_timeframe:D1"), ("⬅️ Back", "settings_system")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in edit_timeframe_callback: {e}")
            await self._handle_settings_error(update, context, "timeframe")

    async def reset_system_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle reset system settings callback."""
        try:
            telegram_id = update.effective_user.id

            # Reset to default system settings
            default_system = {
                "timezone": "UTC",
                "update_frequency_seconds": 60,
                "log_level": "INFO",
                "preferred_timeframe": "H1",
            }

            success = await self.user_config_service.update_user_config(
                telegram_id, "system", None, default_system
            )

            if success:
                await update.callback_query.answer(
                    "✅ System settings reset to defaults"
                )
                await self.settings_system(update, context)
            else:
                await update.callback_query.answer("❌ Error resetting system settings")

        except Exception as e:
            logger.error(f"Error in reset_system_callback: {e}")
            await update.callback_query.answer("❌ Error resetting system settings")

    # Notification Intervals Callbacks
    async def notification_intervals_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle notification intervals callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            intervals = config.get("notification_intervals", {})

            message = (
                f"⏰ **NOTIFICATION INTERVALS** ⏰\n\n"
                f"**Current Settings**:\n"
                f"📈 Signals: {intervals.get('signals_minutes', 5)} minutes\n"
                f"📊 Positions: {intervals.get('positions_minutes', 1)} minutes\n"
                f"⚠️ Risk: {intervals.get('risk_minutes', 15)} minutes\n"
                f"📈 Performance: {intervals.get('performance_hours', 4)} hours\n"
                f"🔧 System: {intervals.get('system_minutes', 30)} minutes\n\n"
                f"**Token Saving**:\n"
                f"Longer intervals = fewer notifications = lower token usage\n"
                f"Shorter intervals = more notifications = higher token usage"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("📈 Signal Interval", "set_interval:signals"),
                        ("📊 Position Interval", "set_interval:positions"),
                    ],
                    [
                        ("⚠️ Risk Interval", "set_interval:risk"),
                        ("📈 Performance Interval", "set_interval:performance"),
                    ],
                    [
                        ("🔧 System Interval", "set_interval:system"),
                        ("🔄 Reset All", "reset_intervals"),
                    ],
                    [("⬅️ Back", "settings"), ("🏠 Main", "start")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in notification_intervals_callback: {e}")
            await self._handle_settings_error(update, context, "intervals")

    async def notification_trading_pairs_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle notification trading pairs callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            allowed_symbols = config.get("trading", {}).get("allowed_symbols", [])

            message = (
                f"📋 **NOTIFICATION TRADING PAIRS** 📋\n\n"
                f"**Current Allowed Pairs**:\n"
            )

            if allowed_symbols:
                for symbol in allowed_symbols:
                    message += f"• {symbol}\n"
            else:
                message += "• No pairs configured\n"

            message += f"\n**Total**: {len(allowed_symbols)} pairs\n\n"
            message += "**Popular Pairs**:\n"
            message += "• Forex: EURUSD, GBPUSD, USDJPY, USDCAD\n"
            message += "• Crypto: BTCUSD, ETHUSD, XRPUSD\n"
            message += "• Metals: XAUUSD, XAGUSD\n"
            message += "• Indices: SPX500, NAS100, GER30\n\n"
            message += (
                "**Configure**: Select options below to manage your trading pairs."
            )

            keyboard = create_keyboard(
                [
                    [
                        ("➕ Add Pair", "add_trading_pair"),
                        ("➖ Remove Pair", "remove_trading_pair"),
                    ],
                    [
                        ("📋 Popular Forex", "add_popular_forex"),
                        ("📋 Popular Crypto", "add_popular_crypto"),
                    ],
                    [
                        ("🔄 Reset Defaults", "reset_trading_pairs"),
                        ("📊 View All", "view_all_pairs"),
                    ],
                    [("⬅️ Back", "settings_notifications"), ("🏠 Main", "start")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in notification_trading_pairs_callback: {e}")
            await self._handle_settings_error(update, context, "trading_pairs")

    async def set_interval_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle set interval callback."""
        try:
            query = update.callback_query
            interval_type = query.data.split(":")[1]
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            intervals = config.get("notification_intervals", {})

            current_interval = intervals.get(f"{interval_type}_minutes", 5)
            if interval_type == "performance":
                current_interval = intervals.get(f"{interval_type}_hours", 4)

            message = (
                f"⏰ **SET {interval_type.upper()} INTERVAL** ⏰\n\n"
                f"**Current Interval**: {current_interval} {'hours' if interval_type == 'performance' else 'minutes'}\n\n"
                f"**Select New Interval**:\n"
                f"Choose how often to receive {interval_type} notifications."
            )

            if interval_type == "performance":
                # Performance intervals in hours
                keyboard = create_keyboard(
                    [
                        [
                            ("1h", f"update_interval:{interval_type}:1"),
                            ("2h", f"update_interval:{interval_type}:2"),
                            ("4h", f"update_interval:{interval_type}:4"),
                        ],
                        [
                            ("6h", f"update_interval:{interval_type}:6"),
                            ("8h", f"update_interval:{interval_type}:8"),
                            ("12h", f"update_interval:{interval_type}:12"),
                        ],
                        [
                            ("24h", f"update_interval:{interval_type}:24"),
                            ("Custom", f"custom_interval:{interval_type}"),
                        ],
                        [("⬅️ Back", "notification_intervals")],
                    ]
                )
            else:
                # Other intervals in minutes
                keyboard = create_keyboard(
                    [
                        [
                            ("1m", f"update_interval:{interval_type}:1"),
                            ("5m", f"update_interval:{interval_type}:5"),
                            ("15m", f"update_interval:{interval_type}:15"),
                        ],
                        [
                            ("30m", f"update_interval:{interval_type}:30"),
                            ("60m", f"update_interval:{interval_type}:60"),
                            ("120m", f"update_interval:{interval_type}:120"),
                        ],
                        [
                            ("240m", f"update_interval:{interval_type}:240"),
                            ("Custom", f"custom_interval:{interval_type}"),
                        ],
                        [("⬅️ Back", "notification_intervals")],
                    ]
                )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in set_interval_callback: {e}")
            await self._handle_settings_error(update, context, "interval")

    # Trading Pairs Callbacks
    async def trading_pairs_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle trading pairs callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            allowed_symbols = config.get("trading", {}).get("allowed_symbols", [])

            message = (
                f"📋 **TRADING PAIRS SETTINGS** 📋\n\n" f"**Current Allowed Pairs**:\n"
            )

            if allowed_symbols:
                for symbol in allowed_symbols:
                    message += f"• {symbol}\n"
            else:
                message += "• No pairs configured\n"

            message += f"\n**Total**: {len(allowed_symbols)} pairs\n\n"
            message += "**Popular Pairs**:\n"
            message += "• Forex: EURUSD, GBPUSD, USDJPY, USDCAD\n"
            message += "• Crypto: BTCUSD, ETHUSD, XRPUSD\n"
            message += "• Metals: XAUUSD, XAGUSD\n"
            message += "• Indices: SPX500, NAS100, GER30"

            keyboard = create_keyboard(
                [
                    [
                        ("➕ Add Pair", "add_trading_pair"),
                        ("➖ Remove Pair", "remove_trading_pair"),
                    ],
                    [
                        ("📋 Popular Forex", "add_popular_forex"),
                        ("📋 Popular Crypto", "add_popular_crypto"),
                    ],
                    [
                        ("🔄 Reset Defaults", "reset_trading_pairs"),
                        ("📊 View All", "view_all_pairs"),
                    ],
                    [("⬅️ Back", "settings"), ("🏠 Main", "start")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in trading_pairs_callback: {e}")
            await self._handle_settings_error(update, context, "trading_pairs")

    async def add_trading_pair_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle add trading pair callback."""
        try:
            message = (
                f"➕ **ADD TRADING PAIR** ➕\n\n"
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
                        ("EURUSD", "add_pair:EURUSD"),
                        ("GBPUSD", "add_pair:GBPUSD"),
                        ("USDJPY", "add_pair:USDJPY"),
                    ],
                    [
                        ("USDCAD", "add_pair:USDCAD"),
                        ("AUDUSD", "add_pair:AUDUSD"),
                        ("NZDUSD", "add_pair:NZDUSD"),
                    ],
                    [
                        ("BTCUSD", "add_pair:BTCUSD"),
                        ("ETHUSD", "add_pair:ETHUSD"),
                        ("XRPUSD", "add_pair:XRPUSD"),
                    ],
                    [
                        ("XAUUSD", "add_pair:XAUUSD"),
                        ("XAGUSD", "add_pair:XAGUSD"),
                        ("SPX500", "add_pair:SPX500"),
                    ],
                    [("Custom", "custom_add_pair"), ("⬅️ Back", "trading_pairs")],
                ]
            )

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in add_trading_pair_callback: {e}")
            await self._handle_settings_error(update, context, "add_pair")

    async def remove_trading_pair_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle remove trading pair callback."""
        try:
            telegram_id = update.effective_user.id
            config = await self.user_config_service.get_user_config(telegram_id)
            allowed_symbols = config.get("trading", {}).get("allowed_symbols", [])

            if not allowed_symbols:
                message = (
                    f"➖ **REMOVE TRADING PAIR** ➖\n\n"
                    f"**No pairs to remove**\n\n"
                    f"You don't have any trading pairs configured.\n"
                    f"Add some pairs first to be able to remove them."
                )
                keyboard = create_keyboard(
                    [
                        [
                            ("➕ Add Pairs", "add_trading_pair"),
                            ("⬅️ Back", "trading_pairs"),
                        ]
                    ]
                )
            else:
                message = f"➖ **REMOVE TRADING PAIR** ➖\n\n" f"**Current Pairs**:\n"
                for symbol in allowed_symbols:
                    message += f"• {symbol}\n"

                message += f"\n**Select pair to remove**:"

                # Create buttons for each symbol (max 8 per row)
                buttons = []
                for i in range(0, len(allowed_symbols), 2):
                    row = []
                    for j in range(2):
                        if i + j < len(allowed_symbols):
                            symbol = allowed_symbols[i + j]
                            row.append((symbol, f"remove_pair:{symbol}"))
                    buttons.append(row)

                buttons.append([("⬅️ Back", "trading_pairs")])
                keyboard = create_keyboard(buttons)

            await self.edit_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in remove_trading_pair_callback: {e}")
            await self._handle_settings_error(update, context, "remove_pair")
