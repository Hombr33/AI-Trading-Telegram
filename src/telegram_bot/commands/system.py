"""System commands for Telegram bot."""

from typing import Dict, Any, List, Optional
import platform
import psutil
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.utils.keyboards import create_keyboard
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
        }

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command.
        
        Args:
            update: The update object.
            context: The context object.
        """
        user = update.effective_user
        message = (
            f"👋 Hello, {user.first_name}!\n\n"
            f"Welcome to the AI Trading Bot. I'm here to help you monitor and manage your trading activities.\n\n"
            f"Here are some quick actions to get started:\n"
            f"• /status - Check system status\n"
            f"• /account - View account information\n"
            f"• /positions - View open positions\n"
            f"• /orders - View pending orders\n"
            f"• /signals - View trading signals\n"
            f"• /risk - View risk metrics\n"
            f"• /performance - View performance metrics\n"
            f"• /monitor - Monitor system resources\n"
            f"• /help - Show all available commands\n\n"
            f"Let me know if you need any assistance!"
        )

        # Create an inline keyboard with quick actions
        keyboard = create_keyboard([
            [("Status", "status"), ("Account", "account")],
            [("Positions", "positions"), ("Orders", "orders")],
            [("Signals", "signals"), ("Risk", "risk")],
            [("Performance", "performance"), ("Monitor", "monitor")],
            [("Help", "help")]
        ])

        await self.send_message(update, context, message, keyboard)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command.
        
        Args:
            update: The update object.
            context: The context object.
        """
        message = (
            f"🤖 **AI Trading Bot Help** 🤖\n\n"
            f"Here are all the available commands:\n\n"
            f"**System Commands**:\n"
            f"• /start - Start the bot\n"
            f"• /help - Show this help message\n"
            f"• /status - Check system status\n"
            f"• /monitor - Monitor system resources\n"
            f"• /settings - Configure bot settings\n\n"
            f"**Trading Commands**:\n"
            f"• /account - View account information\n"
            f"• /positions - View open positions\n"
            f"• /orders - View pending orders\n"
            f"• /signals - View trading signals\n\n"
            f"**Analysis Commands**:\n"
            f"• /risk - View risk metrics\n"
            f"• /performance - View performance metrics\n"
            f"• /journal - View trading journal\n\n"
            f"Click on any button below to execute the corresponding command."
        )

        # Create an inline keyboard with all commands
        keyboard = create_keyboard([
            [("Status", "status"), ("Account", "account")],
            [("Positions", "positions"), ("Orders", "orders")],
            [("Signals", "signals"), ("Risk", "risk")],
            [("Performance", "performance"), ("Journal", "journal")],
            [("Monitor", "monitor"), ("Settings", "settings")]
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
            f"📊 **SYSTEM STATUS** 📊\n\n"
            f"🔄 **Status**: {status_data['status']}\n"
            f"⏰ **Uptime**: {status_data['uptime']}\n"
            f"🔌 **Connection**: {status_data['connection']}\n"
            f"📈 **CPU Usage**: {status_data['cpu_usage']}%\n"
            f"💾 **Memory Usage**: {status_data['memory_usage']}%\n\n"
            f"**Active Strategies**: {status_data['active_strategies']}\n"
            f"**Open Positions**: {status_data['open_positions']}\n"
            f"**Pending Orders**: {status_data['pending_orders']}\n\n"
            f"**Last Updated**: {status_data['last_updated']}"
        )

        # Create an inline keyboard for status actions
        keyboard = create_keyboard([
            [("Refresh", "refresh_status"), ("Positions", "positions")],
            [("Orders", "orders"), ("Account", "account")],
            [("Monitor", "monitor"), ("Settings", "settings")]
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