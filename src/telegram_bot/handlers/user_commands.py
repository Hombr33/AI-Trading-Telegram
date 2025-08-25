"""
Telegram bot command handlers for user management and configuration.
"""

import logging
from typing import Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from ...services.user_manager import UserManager
from ...services.config_manager import ConfigManager
from ...bridge.ea_bridge import EABridge
from ...bridge.signal_distributor import SignalDistributor
from ...models.telegram_users import PlatformType, SubscriptionStatus

logger = logging.getLogger(__name__)

# Conversation states
WAITING_API_KEY, WAITING_CONFIG_TYPE, WAITING_CONFIG_VALUE = range(3)


class UserCommandHandlers:
    """Handlers for user commands and configuration."""

    def __init__(self):
        self.user_manager = UserManager()
        self.config_manager = ConfigManager()
        self.ea_bridge = EABridge()
        self.signal_distributor = SignalDistributor()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        telegram_id = user.id

        # Get or create user
        db_user = await self.user_manager.get_or_create_user(
            telegram_id=telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

        if db_user.is_admin:
            welcome_msg = """🎯 **Welcome to AI Trading Bot - Admin Panel**

You have administrator privileges. Available commands:

**User Management:**
/users - View all registered users
/add_admin - Add new administrator
/remove_admin - Remove administrator
/set_subscription - Manage user subscriptions

**Configuration:**
/config - Manage your trading settings
/server_config - Manage server settings
/restart - Restart trading system

**Trading:**
/register_mt5 - Register MT5 EA connection
/register_crypto - Register crypto exchange
/positions - View current positions
/history - View trading history

**Monitoring:**
/status - System status
/performance - Trading performance
/signals - Recent signals

Type /help for detailed command descriptions."""

        elif await self.user_manager.is_user_authorized(telegram_id):
            welcome_msg = """🎯 **Welcome to AI Trading Bot**

Your subscription is active. Available commands:

**Configuration:**
/config - Manage your trading settings
/symbols - Manage symbol subscriptions

**Trading:**
/register_mt5 - Register MT5 EA connection
/register_crypto - Register crypto exchange
/positions - View current positions
/history - View trading history

**Monitoring:**
/status - Account status
/performance - Your trading performance
/signals - Recent signals

Type /help for detailed command descriptions."""

        else:
            welcome_msg = """🎯 **Welcome to AI Trading Bot**

❌ Your subscription is not active. Please contact an administrator to activate your account.

Once activated, you'll have access to:
- AI-powered trading signals
- Multi-platform trading (MT5/Crypto)
- Advanced risk management
- Real-time position monitoring
- Performance analytics

Contact support for subscription activation."""

        await update.message.reply_text(welcome_msg, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        telegram_id = update.effective_user.id
        is_admin = await self.user_manager.is_admin(telegram_id)
        is_authorized = await self.user_manager.is_user_authorized(telegram_id)

        if is_admin:
            help_text = """📚 **Admin Commands Help**

**User Management:**
/users - List all registered users with status
/add_admin <user_id> - Promote user to admin
/remove_admin <user_id> - Remove admin privileges
/set_subscription <user_id> <status> - Set user subscription

**Server Configuration:**
/server_config - View/edit server settings
/restart - Restart the trading system
/logs - View system logs

**Trading Management:**
/config - Your personal trading configuration
/register_mt5 - Register MT5 EA connection
/positions - View current positions across all users
/close_all - Emergency close all positions

**Monitoring:**
/status - Complete system status
/performance - System-wide performance metrics
/signals - Recent signal distribution stats"""

        elif is_authorized:
            help_text = """📚 **User Commands Help**

**Configuration:**
/config - Manage your trading settings
  - Risk settings (position size, drawdown limits)
  - Symbol preferences and filters
  - Signal generation parameters
  - Trading rules and sessions

/symbols - Manage symbol subscriptions
  - Subscribe/unsubscribe to trading pairs
  - Set minimum confidence thresholds
  - Configure symbol-specific settings

**Platform Integration:**
/register_mt5 - Register your MT5 EA
  - Enter API key from EA popup
  - Configure server endpoint
  - Test connection

/register_crypto - Register crypto exchange
  - Add API key and secret
  - Select exchange (Binance, Bybit)
  - Configure trading pairs

**Trading Operations:**
/positions - View your current positions
/close <ticket> - Close specific position
/modify <ticket> - Modify stop loss/take profit
/history - View your trading history

**Monitoring:**
/status - Your account and system status
/performance - Your trading performance metrics
/signals - Recent signals for your symbols"""

        else:
            help_text = """📚 **Available Commands**

❌ Your subscription is not active.

**Available:**
/start - Welcome message
/help - This help message

**After Activation:**
- Full trading functionality
- Configuration management
- Position monitoring
- Performance analytics

Contact an administrator for subscription activation."""

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /config command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text("❌ Subscription required to access configuration.")
            return

        # Create configuration menu
        keyboard = [
            [InlineKeyboardButton("⚖️ Risk Settings", callback_data="config_risk")],
            [InlineKeyboardButton("📊 Symbol Settings", callback_data="config_symbol")],
            [InlineKeyboardButton("🎯 Signal Settings", callback_data="config_signal")],
            [InlineKeyboardButton("🤖 Model Settings", callback_data="config_model")],
            [InlineKeyboardButton("📈 Trading Settings", callback_data="config_trading")],
            [InlineKeyboardButton("📋 Rules Settings", callback_data="config_rules")],
            [InlineKeyboardButton("🔄 Reset All", callback_data="config_reset_all")],
            [InlineKeyboardButton("📄 View All", callback_data="config_view_all")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⚙️ **Configuration Management**\n\nSelect a configuration category to modify:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def register_mt5_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /register_mt5 command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text("❌ Subscription required to register MT5 connection.")
            return ConversationHandler.END

        await update.message.reply_text(
            """🔗 **MT5 EA Registration**

To register your MT5 Expert Advisor:

1. Install the EA file on your MT5 terminal
2. The EA will display an API key in a popup
3. Copy that API key and send it here

Please send your EA API key:""",
            parse_mode='Markdown'
        )

        return WAITING_API_KEY

    async def handle_mt5_api_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle MT5 API key input."""
        telegram_id = update.effective_user.id
        api_key = update.message.text.strip()

        if len(api_key) < 10:
            await update.message.reply_text("❌ Invalid API key format. Please try again:")
            return WAITING_API_KEY

        # Register EA connection
        success = await self.ea_bridge.register_ea_connection(
            telegram_id=telegram_id,
            api_key=api_key,
            connection_name="MT5 EA"
        )

        if success:
            await update.message.reply_text(
                """✅ **MT5 EA Registered Successfully!**

Your EA is now connected to the trading system. You can now:
- Receive trading signals
- Monitor positions via Telegram
- Configure EA settings remotely

Use /positions to view current positions or /config to adjust settings.""",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                """❌ **Registration Failed**

The API key could not be validated. Please check:
- EA is running on MT5
- API key is correct
- Server connection is active

Try again with /register_mt5"""
            )

        return ConversationHandler.END

    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /positions command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text("❌ Subscription required to view positions.")
            return

        # Get positions from EA
        positions = await self.ea_bridge.get_positions_from_ea(telegram_id)

        if positions is None:
            await update.message.reply_text("❌ Could not retrieve positions. Check your EA connection.")
            return

        if not positions:
            await update.message.reply_text("📊 **Current Positions**\n\nNo open positions.")
            return

        # Format positions message
        message = "📊 **Current Positions**\n\n"
        total_pnl = 0

        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            ticket = pos.get('ticket', 'N/A')
            type_str = pos.get('type', 'N/A')
            volume = pos.get('volume', 0)
            open_price = pos.get('open_price', 0)
            current_price = pos.get('current_price', 0)
            pnl = pos.get('pnl', 0)
            sl = pos.get('sl', 0)
            tp = pos.get('tp', 0)

            total_pnl += pnl

            message += f"""🎯 **{symbol}** (#{ticket})
📈 Type: {type_str} | Volume: {volume}
💰 Open: {open_price} | Current: {current_price}
💵 P&L: ${pnl:.2f}
🛑 SL: {sl} | 🎯 TP: {tp}

"""

        message += f"💰 **Total P&L: ${total_pnl:.2f}**"

        await update.message.reply_text(message, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        telegram_id = update.effective_user.id
        is_admin = await self.user_manager.is_admin(telegram_id)
        is_authorized = await self.user_manager.is_user_authorized(telegram_id)

        if not is_authorized:
            await update.message.reply_text("❌ Subscription required to view status.")
            return

        # Get user info
        with self.user_manager.get_session() as session:
            user = session.query(TelegramUser).filter(
                TelegramUser.telegram_id == telegram_id
            ).first()

        # Get platform connections
        connections = await self.user_manager.get_user_platform_connections(telegram_id)
        
        # Get subscriptions
        subscriptions = await self.user_manager.get_user_subscriptions(telegram_id)

        # Get account info if MT5 connected
        account_info = await self.ea_bridge.get_account_info_from_ea(telegram_id)

        status_msg = f"""📊 **Account Status**

👤 **User Information:**
Name: {user.first_name or 'N/A'} {user.last_name or ''}
Username: @{user.username or 'N/A'}
Role: {'Admin' if user.is_admin else 'User'}
Subscription: {user.subscription_status.value.title()}

🔗 **Platform Connections:**
"""

        if connections:
            for conn in connections:
                status_msg += f"- {conn['platform_type'].upper()}: {conn['connection_name']}\n"
        else:
            status_msg += "- No platforms connected\n"

        status_msg += f"\n📈 **Signal Subscriptions:**\n"
        if subscriptions:
            for sub in subscriptions:
                status_msg += f"- {sub['symbol']} (min {sub['min_confidence']}%)\n"
        else:
            status_msg += "- No symbol subscriptions\n"

        if account_info:
            balance = account_info.get('balance', 0)
            equity = account_info.get('equity', 0)
            margin = account_info.get('margin', 0)
            free_margin = account_info.get('free_margin', 0)

            status_msg += f"""
💰 **Account Info:**
Balance: ${balance:.2f}
Equity: ${equity:.2f}
Margin: ${margin:.2f}
Free Margin: ${free_margin:.2f}"""

        await update.message.reply_text(status_msg, parse_mode='Markdown')

    async def symbols_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /symbols command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text("❌ Subscription required to manage symbols.")
            return

        # Get current subscriptions
        subscriptions = await self.signal_distributor.get_user_active_symbols(telegram_id)
        
        # Available symbols
        available_symbols = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF"]

        # Create keyboard for symbol management
        keyboard = []
        for symbol in available_symbols:
            status = "✅" if symbol in subscriptions else "❌"
            keyboard.append([InlineKeyboardButton(f"{status} {symbol}", callback_data=f"symbol_{symbol}")])

        keyboard.append([InlineKeyboardButton("📊 View Settings", callback_data="symbol_settings")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = f"""📊 **Symbol Subscriptions**

Current subscriptions: {len(subscriptions)}
Active symbols: {', '.join(subscriptions) if subscriptions else 'None'}

Click symbols to toggle subscription:"""

        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    # Callback handlers for inline keyboards
    async def handle_config_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle configuration callback queries."""
        query = update.callback_query
        await query.answer()

        telegram_id = query.from_user.id
        data = query.data

        if data.startswith("config_"):
            config_type = data.replace("config_", "")
            
            if config_type == "view_all":
                configs = await self.config_manager.get_all_user_configs(telegram_id)
                message = "📄 **All Configurations:**\n\n"
                
                for cfg_type, cfg_data in configs.items():
                    message += f"**{cfg_type.title()}:**\n```json\n{str(cfg_data)[:200]}...\n```\n\n"
                
                await query.edit_message_text(message, parse_mode='Markdown')
                return

            elif config_type == "reset_all":
                # Reset all configurations
                for cfg_type in self.config_manager.DEFAULT_CONFIGS.keys():
                    await self.config_manager.reset_user_config(telegram_id, cfg_type)
                
                await query.edit_message_text("✅ All configurations reset to defaults.")
                return

            # Show specific configuration
            config_data = await self.config_manager.get_user_config(telegram_id, config_type)
            
            if config_data:
                message = f"⚙️ **{config_type.title()} Configuration:**\n\n```json\n{str(config_data)[:500]}\n```"
                
                keyboard = [
                    [InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{config_type}")],
                    [InlineKeyboardButton("🔄 Reset", callback_data=f"reset_{config_type}")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="config_back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel current conversation."""
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
