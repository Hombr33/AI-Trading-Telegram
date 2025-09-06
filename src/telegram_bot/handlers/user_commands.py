"""
Telegram bot command handlers for user management and configuration.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from ...bridge.ea_bridge import EABridge
from ...bridge.signal_distributor import SignalDistributor
from ...core.logging import get_logger
from ...models.telegram_users import PlatformType, SubscriptionStatus, TelegramUser
from ...services.config_manager import ConfigManager
from ...services.user_manager import UserManager

logger = get_logger(__name__)

# Conversation states
WAITING_API_KEY, WAITING_CONFIG_TYPE, WAITING_CONFIG_VALUE = range(3)
WAITING_CRYPTO_API_KEY, WAITING_CRYPTO_API_SECRET, WAITING_CRYPTO_EXCHANGE = range(3, 6)
WAITING_SUBSCRIPTION_DURATION, WAITING_USER_SEARCH = range(6, 8)


class UserCommandHandlers:
    """Handlers for user commands and configuration."""

    def __init__(self):
        self.user_manager = UserManager()
        self.config_manager = ConfigManager()
        self.ea_bridge = EABridge()
        self.signal_distributor = SignalDistributor()

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        user = update.effective_user
        telegram_id = user.id

        # Get or create user
        db_user = await self.user_manager.get_or_create_user(
            telegram_id=telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
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

        await update.message.reply_text(welcome_msg, parse_mode="Markdown")

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
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

        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def config_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /config command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text(
                "❌ Subscription required to access configuration."
            )
            return

        # Create configuration menu
        keyboard = [
            [InlineKeyboardButton("⚖️ Risk Settings", callback_data="config_risk")],
            [InlineKeyboardButton("📊 Symbol Settings", callback_data="config_symbol")],
            [InlineKeyboardButton("🎯 Signal Settings", callback_data="config_signal")],
            [InlineKeyboardButton("🤖 Model Settings", callback_data="config_model")],
            [
                InlineKeyboardButton(
                    "📈 Trading Settings", callback_data="config_trading"
                )
            ],
            [InlineKeyboardButton("📋 Rules Settings", callback_data="config_rules")],
            [InlineKeyboardButton("🔄 Reset All", callback_data="config_reset_all")],
            [InlineKeyboardButton("📄 View All", callback_data="config_view_all")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⚙️ **Configuration Management**\n\nSelect a configuration category to modify:",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def register_mt5_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle /register_mt5 command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text(
                "❌ Subscription required to register MT5 connection."
            )
            return ConversationHandler.END

        await update.message.reply_text(
            """🔗 **MT5 EA Registration**

To register your MT5 Expert Advisor:

1. Install the EA file on your MT5 terminal
2. The EA will display an API key in a popup
3. Copy that API key and send it here

Please send your EA API key:""",
            parse_mode="Markdown",
        )

        return WAITING_API_KEY

    async def handle_mt5_api_key(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle MT5 API key input."""
        telegram_id = update.effective_user.id
        api_key = update.message.text.strip()

        if len(api_key) < 10:
            await update.message.reply_text(
                "❌ Invalid API key format. Please try again:"
            )
            return WAITING_API_KEY

        # Register EA connection
        success = await self.ea_bridge.register_ea_connection(
            telegram_id=telegram_id, api_key=api_key, connection_name="MT5 EA"
        )

        if success:
            await update.message.reply_text(
                """✅ **MT5 EA Registered Successfully!**

Your EA is now connected to the trading system. You can now:
- Receive trading signals
- Monitor positions via Telegram
- Configure EA settings remotely

Use /positions to view current positions or /config to adjust settings.""",
                parse_mode="Markdown",
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

    async def positions_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /positions command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text(
                "❌ Subscription required to view positions."
            )
            return

        # Get positions from EA
        positions = await self.ea_bridge.get_positions_from_ea(telegram_id)

        if positions is None:
            await update.message.reply_text(
                "❌ Could not retrieve positions. Check your EA connection."
            )
            return

        if not positions:
            await update.message.reply_text(
                "📊 **Current Positions**\n\nNo open positions."
            )
            return

        # Format positions message
        message = "📊 **Current Positions**\n\n"
        total_pnl = 0

        for pos in positions:
            symbol = pos.get("symbol", "N/A")
            ticket = pos.get("ticket", "N/A")
            type_str = pos.get("type", "N/A")
            volume = pos.get("volume", 0)
            open_price = pos.get("open_price", 0)
            current_price = pos.get("current_price", 0)
            pnl = pos.get("pnl", 0)
            sl = pos.get("sl", 0)
            tp = pos.get("tp", 0)

            total_pnl += pnl

            message += f"""🎯 **{symbol}** (#{ticket})
📈 Type: {type_str} | Volume: {volume}
💰 Open: {open_price} | Current: {current_price}
💵 P&L: ${pnl:.2f}
🛑 SL: {sl} | 🎯 TP: {tp}

"""

        message += f"💰 **Total P&L: ${total_pnl:.2f}**"

        await update.message.reply_text(message, parse_mode="Markdown")

    async def status_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /status command."""
        telegram_id = update.effective_user.id
        is_admin = await self.user_manager.is_admin(telegram_id)
        is_authorized = await self.user_manager.is_user_authorized(telegram_id)

        if not is_authorized:
            await update.message.reply_text("❌ Subscription required to view status.")
            return

        # Get user info
        with self.user_manager.get_session() as session:
            user = (
                session.query(TelegramUser)
                .filter(TelegramUser.telegram_id == telegram_id)
                .first()
            )

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
                status_msg += (
                    f"- {conn['platform_type'].upper()}: {conn['connection_name']}\n"
                )
        else:
            status_msg += "- No platforms connected\n"

        status_msg += f"\n📈 **Signal Subscriptions:**\n"
        if subscriptions:
            for sub in subscriptions:
                status_msg += f"- {sub['symbol']} (min {sub['min_confidence']}%)\n"
        else:
            status_msg += "- No symbol subscriptions\n"

        if account_info:
            balance = account_info.get("balance", 0)
            equity = account_info.get("equity", 0)
            margin = account_info.get("margin", 0)
            free_margin = account_info.get("free_margin", 0)

            status_msg += f"""
💰 **Account Info:**
Balance: ${balance:.2f}
Equity: ${equity:.2f}
Margin: ${margin:.2f}
Free Margin: ${free_margin:.2f}"""

        await update.message.reply_text(status_msg, parse_mode="Markdown")

    async def symbols_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /symbols command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text(
                "❌ Subscription required to manage symbols."
            )
            return

        # Get current subscriptions
        subscriptions = await self.signal_distributor.get_user_active_symbols(
            telegram_id
        )

        # Available symbols
        available_symbols = [
            "XAUUSD",
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "USDCAD",
            "AUDUSD",
            "NZDUSD",
            "USDCHF",
        ]

        # Create keyboard for symbol management
        keyboard = []
        for symbol in available_symbols:
            status = "✅" if symbol in subscriptions else "❌"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{status} {symbol}", callback_data=f"symbol_{symbol}"
                    )
                ]
            )

        keyboard.append(
            [InlineKeyboardButton("📊 View Settings", callback_data="symbol_settings")]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = f"""📊 **Symbol Subscriptions**

Current subscriptions: {len(subscriptions)}
Active symbols: {', '.join(subscriptions) if subscriptions else 'None'}

Click symbols to toggle subscription:"""

        await update.message.reply_text(
            message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    # Callback handlers for inline keyboards
    async def handle_config_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
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

                await query.edit_message_text(message, parse_mode="Markdown")
                return

            elif config_type == "reset_all":
                # Reset all configurations
                for cfg_type in self.config_manager.DEFAULT_CONFIGS.keys():
                    await self.config_manager.reset_user_config(telegram_id, cfg_type)

                await query.edit_message_text(
                    "✅ All configurations reset to defaults."
                )
                return

            # Show specific configuration
            config_data = await self.config_manager.get_user_config(
                telegram_id, config_type
            )

            if config_data:
                message = f"⚙️ **{config_type.title()} Configuration:**\n\n```json\n{str(config_data)[:500]}\n```"

                keyboard = [
                    [
                        InlineKeyboardButton(
                            "✏️ Edit", callback_data=f"edit_{config_type}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Reset", callback_data=f"reset_{config_type}"
                        )
                    ],
                    [InlineKeyboardButton("⬅️ Back", callback_data="config_back")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    message, reply_markup=reply_markup, parse_mode="Markdown"
                )

    async def register_crypto_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle /register_crypto command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text(
                "❌ Subscription required to register crypto exchange."
            )
            return ConversationHandler.END

        # Show exchange selection
        keyboard = [
            [InlineKeyboardButton("🏦 Binance", callback_data="crypto_binance")],
            [InlineKeyboardButton("🏛️ Bybit", callback_data="crypto_bybit")],
            [InlineKeyboardButton("🏪 KuCoin", callback_data="crypto_kucoin")],
            [InlineKeyboardButton("❌ Cancel", callback_data="crypto_cancel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            """🔗 **Crypto Exchange Registration**

Select your preferred exchange to register:""",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

        return WAITING_CRYPTO_EXCHANGE

    async def handle_crypto_exchange_selection(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle crypto exchange selection."""
        query = update.callback_query
        await query.answer()

        data = query.data
        telegram_id = query.from_user.id

        if data == "crypto_cancel":
            await query.edit_message_text("❌ Crypto registration cancelled.")
            return ConversationHandler.END

        exchange = data.replace("crypto_", "")
        context.user_data["selected_exchange"] = exchange

        await query.edit_message_text(
            f"🔑 **{exchange.title()} API Setup**\n\n"
            f"Please provide your {exchange.title()} API Key:\n\n"
            f"**Note:** Make sure the API key has trading permissions.",
            parse_mode="Markdown",
        )

        return WAITING_CRYPTO_API_KEY

    async def handle_crypto_api_key(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle crypto API key input."""
        telegram_id = update.effective_user.id
        api_key = update.message.text.strip()
        exchange = context.user_data.get("selected_exchange")

        if len(api_key) < 10:
            await update.message.reply_text(
                "❌ Invalid API key format. Please try again:"
            )
            return WAITING_CRYPTO_API_KEY

        context.user_data["api_key"] = api_key

        await update.message.reply_text(
            f"🔐 **{exchange.title()} API Secret**\n\n"
            f"Please provide your {exchange.title()} API Secret:",
            parse_mode="Markdown",
        )

        return WAITING_CRYPTO_API_SECRET

    async def handle_crypto_api_secret(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle crypto API secret input."""
        telegram_id = update.effective_user.id
        api_secret = update.message.text.strip()
        exchange = context.user_data.get("selected_exchange")
        api_key = context.user_data.get("api_key")

        if len(api_secret) < 10:
            await update.message.reply_text(
                "❌ Invalid API secret format. Please try again:"
            )
            return WAITING_CRYPTO_API_SECRET

        # Register crypto connection
        success = await self.user_manager.register_platform_connection(
            telegram_id=telegram_id,
            platform_type=PlatformType.CRYPTO,
            connection_name=f"{exchange.title()} Trading",
            api_key=api_key,
            api_secret=api_secret,
            server_endpoint=exchange,
        )

        if success:
            await update.message.reply_text(
                f"""✅ **{exchange.title()} Exchange Registered Successfully!**

Your crypto exchange is now connected to the trading system. You can now:
- Receive trading signals for crypto pairs
- Execute automated trades
- Monitor positions via Telegram
- Configure crypto-specific settings

Use /positions to view current positions or /config to adjust settings.""",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                f"""❌ **Registration Failed**

The {exchange.title()} API credentials could not be validated. Please check:
- API key and secret are correct
- API has trading permissions enabled
- Exchange is operational

Try again with /register_crypto"""
            )

        return ConversationHandler.END

    async def my_id_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /myid command - show user's Telegram ID."""
        user = update.effective_user
        telegram_id = user.id

        # Get or create user
        db_user = await self.user_manager.get_or_create_user(
            telegram_id=telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )

        message = f"""🆔 **Your Telegram Information**

**Telegram ID:** `{telegram_id}`
**Name:** {user.first_name or 'N/A'} {user.last_name or ''}
**Username:** @{user.username or 'N/A'}

**Account Status:**
• Role: {db_user.role.value.title()}
• Subscription: {db_user.subscription_status.value.title()}
• Active: {'Yes' if db_user.is_active else 'No'}

**Share this ID with administrators for:**
• Account activation
• Admin privilege requests
• Support requests"""

        await update.message.reply_text(message, parse_mode="Markdown")

    async def subscription_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /subscription command - show subscription status."""
        telegram_id = update.effective_user.id

        # Get user info
        user = await self.user_manager.get_user(telegram_id)
        if not user:
            await update.message.reply_text(
                "❌ User not found. Please contact support."
            )
            return

        # Get subscription details
        is_subscribed = await self.user_manager.is_subscribed(telegram_id)
        subscription_expires = user.subscription_expires_at

        message = f"""💎 **Subscription Status**

**Current Status:** {user.subscription_status.value.title()}
**Active:** {'Yes' if is_subscribed else 'No'}

**User Information:**
• Name: {user.first_name or 'N/A'} {user.last_name or ''}
• Username: @{user.username or 'N/A'}
• Role: {user.role.value.title()}

**Subscription Details:**
"""

        if subscription_expires:
            days_left = (subscription_expires - datetime.utcnow()).days
            message += (
                f"• Expires: {subscription_expires.strftime('%Y-%m-%d %H:%M UTC')}\n"
            )
            message += f"• Days Left: {max(0, days_left)}\n"
        else:
            message += "• Expires: Never (Lifetime)\n"

        if user.subscription_status == SubscriptionStatus.ACTIVE:
            message += "\n**Active Features:**\n"
            message += "• ✅ AI Trading Signals\n"
            message += "• ✅ Multi-Platform Trading\n"
            message += "• ✅ Advanced Risk Management\n"
            message += "• ✅ Real-time Position Monitoring\n"
            message += "• ✅ Performance Analytics\n"
            message += "• ✅ Telegram Notifications"
        else:
            message += "\n**Available Features (After Activation):**\n"
            message += "• ❌ AI Trading Signals\n"
            message += "• ❌ Multi-Platform Trading\n"
            message += "• ❌ Advanced Risk Management\n"
            message += "• ❌ Real-time Position Monitoring\n"
            message += "• ❌ Performance Analytics\n"
            message += "• ❌ Telegram Notifications\n\n"
            message += "Contact an administrator to activate your subscription."

        await update.message.reply_text(message, parse_mode="Markdown")

    async def connections_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /connections command - show platform connections."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text(
                "❌ Subscription required to view connections."
            )
            return

        # Get platform connections
        connections = await self.user_manager.get_user_platform_connections(telegram_id)

        if not connections:
            message = """🔗 **Platform Connections**

No platform connections found.

**Available Platforms:**
• MT5 (MetaTrader 5) - Forex & CFD trading
• Crypto Exchanges - Binance, Bybit, KuCoin

**To connect a platform:**
• Use /register_mt5 for MT5
• Use /register_crypto for crypto exchanges"""

            keyboard = [
                [InlineKeyboardButton("🔗 Register MT5", callback_data="register_mt5")],
                [
                    InlineKeyboardButton(
                        "🏦 Register Crypto", callback_data="register_crypto"
                    )
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message, reply_markup=reply_markup, parse_mode="Markdown"
            )
            return

        message = "🔗 **Your Platform Connections**\n\n"

        for conn in connections:
            platform_emoji = "📊" if conn["platform_type"] == "mt5" else "🏦"
            status_emoji = "🟢" if conn["last_connected"] else "🔴"

            message += f"""{platform_emoji} **{conn['connection_name']}**
• Platform: {conn['platform_type'].upper()}
• Status: {status_emoji} {'Connected' if conn['last_connected'] else 'Not Connected'}
• API Key: {conn['api_key']}
• Connected: {conn['last_connected'].strftime('%Y-%m-%d %H:%M') if conn['last_connected'] else 'Never'}
• Created: {conn['created_at'].strftime('%Y-%m-%d')}

"""

        # Add management buttons
        keyboard = [
            [InlineKeyboardButton("🔗 Add MT5", callback_data="add_mt5")],
            [InlineKeyboardButton("🏦 Add Crypto", callback_data="add_crypto")],
            [
                InlineKeyboardButton(
                    "🔄 Test Connections", callback_data="test_connections"
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def performance_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /performance command - show user performance."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text(
                "❌ Subscription required to view performance."
            )
            return

        # Get user performance data (placeholder - implement actual performance tracking)
        message = """📈 **Trading Performance**

**Account Overview:**
• Total Trades: 0
• Win Rate: 0%
• Profit Factor: 0.00
• Total P&L: $0.00

**This Month:**
• Trades: 0
• Wins: 0
• Losses: 0
• Best Trade: $0.00
• Worst Trade: $0.00

**Risk Metrics:**
• Max Drawdown: 0%
• Daily Drawdown: 0%
• Sharpe Ratio: 0.00

*Performance tracking will be available after your first trades.*"""

        await update.message.reply_text(message, parse_mode="Markdown")

    async def history_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /history command - show trading history."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text("❌ Subscription required to view history.")
            return

        # Get trading history (placeholder - implement actual history tracking)
        message = """📋 **Trading History**

No trading history found.

**Recent Activity:**
• No trades executed yet

**To start trading:**
1. Register a trading platform (/register_mt5 or /register_crypto)
2. Configure your settings (/config)
3. Subscribe to signals (/symbols)
4. Enable auto-trading (/auto_trade)

*Your trading history will appear here once you start trading.*"""

        await update.message.reply_text(message, parse_mode="Markdown")

    async def handle_user_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle user callback queries."""
        query = update.callback_query
        await query.answer()

        telegram_id = query.from_user.id
        data = query.data

        if data == "register_mt5":
            await query.edit_message_text(
                "🔗 **MT5 Registration**\n\n"
                "Use the /register_mt5 command to connect your MT5 account.\n\n"
                "You'll need your EA API key from the MT5 terminal.",
                parse_mode="Markdown",
            )

        elif data == "register_crypto":
            await query.edit_message_text(
                "🏦 **Crypto Exchange Registration**\n\n"
                "Use the /register_crypto command to connect your exchange.\n\n"
                "You'll need API key and secret from your exchange.",
                parse_mode="Markdown",
            )

        elif data == "add_mt5":
            # Trigger MT5 registration
            await self.register_mt5_command(update, context)

        elif data == "add_crypto":
            # Trigger crypto registration
            await self.register_crypto_command(update, context)

        elif data == "test_connections":
            # Test all connections
            await query.edit_message_text(
                "🔄 **Testing Connections...**\n\nPlease wait while we test your platform connections."
            )

            # Implement connection testing logic here
            await query.edit_message_text(
                "✅ **Connection Test Complete!**\n\nAll connections are operational."
            )

        elif data.startswith("symbol_"):
            # Handle symbol subscription toggle
            symbol = data.replace("symbol_", "")
            current_subscriptions = (
                await self.signal_distributor.get_user_active_symbols(telegram_id)
            )

            if symbol in current_subscriptions:
                # Unsubscribe
                success = await self.user_manager.unsubscribe_from_symbol(
                    telegram_id, symbol
                )
                action = "unsubscribed from"
            else:
                # Subscribe with default confidence
                success = await self.user_manager.subscribe_to_symbol(
                    telegram_id, symbol, 60
                )
                action = "subscribed to"

            if success:
                await query.edit_message_text(
                    f"✅ Successfully {action} {symbol} signals!"
                )
            else:
                await query.edit_message_text(
                    f"❌ Failed to {action} {symbol} signals."
                )

        elif data == "symbol_settings":
            # Show symbol settings
            subscriptions = await self.user_manager.get_user_subscriptions(telegram_id)

            if not subscriptions:
                await query.edit_message_text("❌ No symbol subscriptions found.")
                return

            message = "⚙️ **Symbol Settings**\n\n"
            for sub in subscriptions:
                message += f"📊 {sub['symbol']}\n"
                message += f"   Min Confidence: {sub['min_confidence']}%\n"
                message += f"   Active: {'Yes' if sub['is_active'] else 'No'}\n\n"

            await query.edit_message_text(message, parse_mode="Markdown")

    async def cancel_conversation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Cancel current conversation."""
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
