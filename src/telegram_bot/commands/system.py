"""System commands for Telegram bot."""

from typing import Dict, Any, List, Optional
import platform
import psutil
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.utils.keyboards import (
    create_keyboard, 
    get_main_menu_keyboard, 
    create_trading_dashboard_keyboard,
    create_emoji_status_keyboard,
    create_progress_keyboard
)
from src.telegram_bot.utils.mock_data import get_system_status, get_system_info
from .base import BaseCommandHandler

logger = get_logger(__name__)


class SystemCommandHandler(BaseCommandHandler):
    """System command handler for Telegram bot."""

    def _register_commands(self):
        """Register system commands."""
        self.commands = {
            "start": self.start_command,
            "help": self.help_command,
            "status": self.status_command,
            "monitor": self.monitor_command,
            "settings": self.settings_command,
            "mt5status": self.mt5_status_command,
        }

    def _register_callbacks(self):
        """Register system callbacks."""
        self.callbacks = {
            "help": self.help_command,
            "status": self.status_command,
            "refresh_status": self.status_command,
            "monitor": self.monitor_command,
            "refresh_monitor": self.monitor_command,
            "settings": self.settings_command,
            "mt5status": self.mt5_status_command,
            "refresh_mt5": self.mt5_status_command,
        }

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command."""
        user = update.effective_user
        welcome_text = (
            f"🚀 Welcome, {user.first_name}! 🚀\n\n"
            "🤖 AI Trading Bot is ready to help you dominate the markets!\n\n"
            "Use /help to see all available commands."
        )
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command."""
        help_text = """
                    Welcome to AI Trading Bot! Here are the available commands:

                    Trading Commands:
                    /positions - View open positions
                    /orders - View pending orders
                    /account - View account info
                    /signals - View recent trading signals

                    Symbol Management:
                    /symbols [broker] - List symbol mappings
                    /addsymbol <standard> <broker> <broker_name> - Add mapping
                    /delsymbol <standard> <broker_name> - Delete mapping

                    System Commands:
                    /status - Check system status
                    /monitor - View performance metrics
                    /settings - Configure bot settings
                    /help - Show this help message
                    """
        await update.message.reply_text(help_text)

        # Create main trading dashboard
        inline_keyboard = create_trading_dashboard_keyboard()

        await self.send_message(update, context, message, inline_keyboard, 
                               reply_keyboard=get_main_menu_keyboard())

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command.
        
        Args:
            update: The update object.
            context: The context object.
        """
        message = (
            f"🎯 **AI Trading Bot Help Center** 🎯\n\n"
            f"🔧 **System Commands**:\n"
            f"🚀 `/start` - Launch bot dashboard\n"
            f"❓ `/help` - Display this help menu\n"
            f"📊 `/status` - Real-time system status\n"
            f"🖥️ `/monitor` - Resource monitoring\n"
            f"⚙️ `/settings` - Bot configuration\n\n"
            f"💹 **Trading Commands**:\n"
            f"💰 `/account` - Account balance & equity\n"
            f"📈 `/positions` - Active trading positions\n"
            f"📋 `/orders` - Pending order management\n"
            f"🎯 `/signals` - AI-generated trading signals\n\n"
            f"📈 **Analysis Commands**:\n"
            f"⚠️ `/risk` - Risk metrics & exposure\n"
            f"📊 `/performance` - Trading performance stats\n"
            f"📝 `/journal` - Trading journal & history\n\n"
            f"💡 **Tap any button to execute instantly!**"
        )

        # Create an inline keyboard with all commands
        keyboard = create_keyboard([
            [("📊 Status", "status"), ("💰 Account", "account")],
            [("📈 Positions", "positions"), ("📋 Orders", "orders")],
            [("🎯 Signals", "signals"), ("⚠️ Risk", "risk")],
            [("📊 Performance", "performance"), ("📝 Journal", "journal")],
            [("🖥️ Monitor", "monitor"), ("⚙️ Settings", "settings")]
        ])

        # If this is a callback query, edit the message
        if update.callback_query:
            await self.edit_message(update, context, message, keyboard)
        else:
            await self.send_message(update, context, message, keyboard)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /status command.
        
        Args:
            update: The update object.
            context: The context object.
        """
        # Get system status data
        status_data = get_system_status()

        # Format the status message
        message = (
            f"📊 **SYSTEM STATUS DASHBOARD** 📊\n\n"
            f"🟢 **Status**: {status_data['status']}\n"
            f"⏰ **Uptime**: {status_data['uptime']}\n"
            f"🔌 **MT5 Connection**: {status_data['connection']}\n"
            f"📈 **CPU**: {status_data['cpu_usage']}%\n"
            f"💾 **Memory**: {status_data['memory_usage']}%\n\n"
            f"📈 **Trading Overview**:\n"
            f"🎯 Active Strategies: **{status_data['active_strategies']}**\n"
            f"📊 Open Positions: **{status_data['open_positions']}**\n"
            f"📋 Pending Orders: **{status_data['pending_orders']}**\n\n"
            f"🕐 **Last Updated**: {status_data['last_updated']}"
        )

        # Create an inline keyboard for status actions
        keyboard = create_keyboard([
            [("🔄 Refresh", "refresh_status"), ("📈 Positions", "positions")],
            [("📋 Orders", "orders"), ("💰 Account", "account")],
            [("🖥️ Monitor", "monitor"), ("⚙️ Settings", "settings")]
        ])

        # If this is a callback query, edit the message
        if update.callback_query:
            await self.edit_message(update, context, message, keyboard)
        else:
            await self.send_message(update, context, message, keyboard)

    async def monitor_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /monitor command.
        
        Args:
            update: The update object.
            context: The context object.
        """
        # Get system info data
        system_info = self._get_system_info()

        # Format the monitor message
        message = (
            f"🖥️ **SYSTEM MONITOR** 🖥️\n\n"
            f"**CPU Usage**: {system_info['cpu_usage']}%\n"
            f"**Memory Usage**: {system_info['memory_usage']}%\n"
            f"**Disk Usage**: {system_info['disk_usage']}%\n\n"
            f"**System Uptime**: {system_info['uptime']}\n"
            f"**Python Version**: {system_info['python_version']}\n"
            f"**Platform**: {system_info['platform']}\n\n"
            f"**Last Updated**: {system_info['last_updated']}"
        )

        # Create an inline keyboard for monitor actions
        keyboard = create_keyboard([
            [("Refresh", "refresh_monitor"), ("Status", "status")],
            [("Account", "account"), ("Settings", "settings")]
        ])

        # If this is a callback query, edit the message
        if update.callback_query:
            await self.edit_message(update, context, message, keyboard)
        else:
            await self.send_message(update, context, message, keyboard)

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information.
        
        Returns:
            Dict containing system information.
        """
        try:
            # Get real system information
            cpu_usage = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))
            python_version = platform.python_version()
            platform_info = f"{platform.system()} {platform.release()}"
            
            return {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "uptime": uptime_str,
                "python_version": python_version,
                "platform": platform_info,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            # Fallback to mock data
            return get_system_info()

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /settings command.
        
        Args:
            update: The update object.
            context: The context object.
        """
        # Mock settings data
        settings = {
            "notifications": {
                "signals": True,
                "positions": True,
                "orders": True,
                "risk": True,
                "performance": True,
                "system": True
            },
            "trading": {
                "auto_trading": False,
                "risk_per_trade": "2%",
                "max_open_positions": 5,
                "allowed_symbols": "BTC, ETH, SOL, BNB, XRP"
            },
            "risk": {
                "max_drawdown": "15%",
                "max_daily_loss": "5%",
                "max_position_size": "10%"
            },
            "system": {
                "timezone": "UTC",
                "update_frequency": "1 minute",
                "log_level": "INFO"
            }
        }

        # Format the settings message
        message = (
            f"⚙️ **SETTINGS** ⚙️\n\n"
            f"**Notification Settings**:\n"
            f"• Signals: {'✅' if settings['notifications']['signals'] else '❌'}\n"
            f"• Positions: {'✅' if settings['notifications']['positions'] else '❌'}\n"
            f"• Orders: {'✅' if settings['notifications']['orders'] else '❌'}\n"
            f"• Risk: {'✅' if settings['notifications']['risk'] else '❌'}\n"
            f"• Performance: {'✅' if settings['notifications']['performance'] else '❌'}\n"
            f"• System: {'✅' if settings['notifications']['system'] else '❌'}\n\n"
            f"**Trading Settings**:\n"
            f"• Auto Trading: {'✅' if settings['trading']['auto_trading'] else '❌'}\n"
            f"• Risk Per Trade: {settings['trading']['risk_per_trade']}\n"
            f"• Max Open Positions: {settings['trading']['max_open_positions']}\n"
            f"• Allowed Symbols: {settings['trading']['allowed_symbols']}\n\n"
            f"**Risk Settings**:\n"
            f"• Max Drawdown: {settings['risk']['max_drawdown']}\n"
            f"• Max Daily Loss: {settings['risk']['max_daily_loss']}\n"
            f"• Max Position Size: {settings['risk']['max_position_size']}\n\n"
            f"**System Settings**:\n"
            f"• Timezone: {settings['system']['timezone']}\n"
            f"• Update Frequency: {settings['system']['update_frequency']}\n"
            f"• Log Level: {settings['system']['log_level']}"
        )

        # Create an inline keyboard for settings actions
        keyboard = create_keyboard([
            [("Edit Notifications", "edit_notifications"), ("Edit Trading", "edit_trading")],
            [("Edit Risk", "edit_risk"), ("Edit System", "edit_system")],
            [("Status", "status"), ("Help", "help")]
        ])

        # If this is a callback query, edit the message
        if update.callback_query:
            await self.edit_message(update, context, message, keyboard)
        else:
            await self.send_message(update, context, message, keyboard)

    async def mt5_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /mt5status command to show MT5 connection status and setup guide.
        
        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Try to get MT5 executor status
            from src.core.config import AppConfig
            config = AppConfig()
            
            # Check if MT5 is configured
            is_configured = config.mt5.is_configured
            
            if is_configured:
                # MT5 is configured, check connection status
                try:
                    import MetaTrader5 as mt5
                    if mt5.initialize():
                        terminal_info = mt5.terminal_info()
                        account_info = mt5.account_info()
                        
                        if terminal_info and account_info:
                            status_emoji = "🟢"
                            status_text = "Connected"
                            connection_details = (
                                f"**Account**: {account_info.login}\n"
                                f"**Server**: {account_info.server}\n"
                                f"**Balance**: ${account_info.balance:.2f}\n"
                                f"**Equity**: ${account_info.equity:.2f}\n"
                                f"**Company**: {account_info.company}\n"
                                f"**Terminal**: {terminal_info.name} v{terminal_info.version}"
                            )
                        else:
                            status_emoji = "🟡"
                            status_text = "Initialized but not logged in"
                            connection_details = "MT5 terminal is running but not connected to account"
                        mt5.shutdown()
                    else:
                        status_emoji = "🔴"
                        status_text = "Failed to initialize"
                        connection_details = "MT5 terminal could not be initialized"
                except Exception as e:
                    status_emoji = "🔴"
                    status_text = "Connection error"
                    connection_details = f"Error: {str(e)}"
            else:
                # MT5 is not configured
                status_emoji = "🟡"
                status_text = "Using Mock Mode"
                missing_fields = []
                if not config.mt5.login or config.mt5.login == 0:
                    missing_fields.append("login")
                if not config.mt5.password:
                    missing_fields.append("password")
                if not config.mt5.server:
                    missing_fields.append("server")
                if not config.mt5.broker_name:
                    missing_fields.append("broker_name")
                
                connection_details = (
                    f"**Missing Configuration**: {', '.join(missing_fields)}\n\n"
                    f"📋 **Setup Required**:\n"
                    f"1. Edit `config/settings.yaml`\n"
                    f"2. Add your MT5 credentials\n"
                    f"3. Restart the bot\n\n"
                    f"📖 **See**: `docs/MT5_SETUP_GUIDE.md`"
                )

            message = (
                f"🔌 **MetaTrader 5 STATUS** 🔌\n\n"
                f"{status_emoji} **Status**: {status_text}\n\n"
                f"{connection_details}\n\n"
                f"💡 **Why Mock Mode?**\n"
                f"The bot uses mock (fake) data when:\n"
                f"• MT5 credentials are not configured\n"
                f"• MT5 terminal is not running\n"
                f"• Connection to broker fails\n\n"
                f"🔧 **To use real data**:\n"
                f"• Configure MT5 credentials in settings\n"
                f"• Ensure MT5 terminal is running\n"
                f"• Enable algorithmic trading in MT5\n\n"
                f"🕐 **Updated**: {datetime.now().strftime('%H:%M:%S')}"
            )

            # Create keyboard with helpful actions
            keyboard = create_keyboard([
                [("🔄 Refresh", "refresh_mt5"), ("📖 Setup Guide", "setup_guide")],
                [("📊 Status", "status"), ("⚙️ Settings", "settings")],
                [("💰 Account", "account"), ("❓ Help", "help")]
            ])

            # If this is a callback query, edit the message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in mt5_status_command: {e}")
            error_message = (
                f"❌ **Error checking MT5 status**\n\n"
                f"Could not retrieve MT5 status information.\n"
                f"Error: {str(e)}\n\n"
                f"Please check the logs for more details."
            )
            
            keyboard = create_keyboard([
                [("📊 Status", "status"), ("❓ Help", "help")]
            ])
            
            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)