"""
Telegram bot command handlers for crypto trading operations.
"""

import logging
from typing import Any, Dict, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from ...models.telegram_users import PlatformType
from ...services.crypto_bridge import CryptoBridge
from ...services.user_manager import UserManager

logger = logging.getLogger(__name__)

# Conversation states
WAITING_EXCHANGE, WAITING_CRYPTO_API_KEY, WAITING_CRYPTO_SECRET = range(3)


class CryptoCommandHandlers:
    """Handlers for crypto trading commands."""

    def __init__(self):
        self.user_manager = UserManager()
        self.crypto_bridge = CryptoBridge()

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

        keyboard = [
            [InlineKeyboardButton("🟡 Binance", callback_data="exchange_binance")],
            [InlineKeyboardButton("🟠 Bybit", callback_data="exchange_bybit")],
            [InlineKeyboardButton("❌ Cancel", callback_data="exchange_cancel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            """🔗 **Crypto Exchange Registration**

Select your crypto exchange:

**Supported Exchanges:**
- Binance (Spot and Futures)
- Bybit (Spot and Derivatives)

Choose an exchange to continue:""",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

        return WAITING_EXCHANGE

    async def handle_exchange_selection(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle exchange selection."""
        query = update.callback_query
        await query.answer()

        if query.data == "exchange_cancel":
            await query.edit_message_text("❌ Crypto registration cancelled.")
            return ConversationHandler.END

        exchange = query.data.replace("exchange_", "")
        context.user_data["selected_exchange"] = exchange

        await query.edit_message_text(
            f"""🔑 **{exchange.title()} API Configuration**

To register your {exchange.title()} account:

1. Go to your {exchange.title()} account settings
2. Create a new API key with trading permissions
3. Copy your API key and send it here

⚠️ **Security Notes:**
- Only use API keys with trading permissions
- Never share your API keys with others
- You can revoke access anytime from your exchange

Please send your API key:""",
            parse_mode="Markdown",
        )

        return WAITING_CRYPTO_API_KEY

    async def handle_crypto_api_key(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle crypto API key input."""
        api_key = update.message.text.strip()

        if len(api_key) < 10:
            await update.message.reply_text(
                "❌ Invalid API key format. Please try again:"
            )
            return WAITING_CRYPTO_API_KEY

        context.user_data["api_key"] = api_key
        exchange = context.user_data.get("selected_exchange", "binance")

        await update.message.reply_text(
            f"""🔐 **{exchange.title()} Secret Key**

Now please send your API secret key:

⚠️ **Important:** This message will be deleted for security after processing."""
        )

        return WAITING_CRYPTO_SECRET

    async def handle_crypto_secret(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle crypto API secret input."""
        telegram_id = update.effective_user.id
        api_secret = update.message.text.strip()

        if len(api_secret) < 10:
            await update.message.reply_text(
                "❌ Invalid secret key format. Please try again:"
            )
            return WAITING_CRYPTO_SECRET

        # Delete the message containing the secret
        try:
            await update.message.delete()
        except:
            pass

        exchange = context.user_data.get("selected_exchange", "binance")
        api_key = context.user_data.get("api_key")

        # Register crypto connection
        success = await self.crypto_bridge.register_crypto_connection(
            telegram_id=telegram_id,
            exchange=exchange,
            api_key=api_key,
            api_secret=api_secret,
            connection_name=f"{exchange.title()} Exchange",
            testnet=True,  # Default to testnet for safety
        )

        if success:
            await context.bot.send_message(
                chat_id=telegram_id,
                text=f"""✅ **{exchange.title()} Exchange Registered!**

Your crypto exchange is now connected to the trading system.

**Features Available:**
- Receive crypto trading signals
- Monitor positions via Telegram
- Execute trades remotely
- View account balance and history

**Next Steps:**
- Use /crypto_status to view account info
- Use /crypto_positions to see open positions
- Configure symbol subscriptions with /symbols

⚠️ **Note:** Currently using testnet for safety. Contact admin to enable live trading.""",
                parse_mode="Markdown",
            )
        else:
            await context.bot.send_message(
                chat_id=telegram_id,
                text=f"""❌ **{exchange.title()} Registration Failed**

Could not validate your API credentials. Please check:
- API key is correct and active
- Secret key matches the API key
- API has trading permissions enabled
- Exchange servers are accessible

Try again with /register_crypto""",
                parse_mode="Markdown",
            )

        # Clear sensitive data
        context.user_data.clear()
        return ConversationHandler.END

    async def crypto_status_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /crypto_status command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text(
                "❌ Subscription required to view crypto status."
            )
            return

        # Get crypto account info
        account_info = await self.crypto_bridge.get_crypto_account_info(telegram_id)

        if not account_info:
            await update.message.reply_text(
                """❌ **No Crypto Exchange Connected**

Please register your crypto exchange first:
/register_crypto - Register Binance or Bybit"""
            )
            return

        exchange = account_info.get("exchange", "Unknown")
        total_balance = account_info.get("total_balance_usdt", 0)
        balances = account_info.get("balances", [])

        message = f"""💰 **{exchange.title()} Account Status**

💵 **Total Balance:** ${total_balance:.2f} USDT

📊 **Asset Balances:**
"""

        # Show top 5 balances
        for balance in balances[:5]:
            asset = balance.get("asset", "N/A")
            total = balance.get("total", 0)
            if total > 0.01:  # Only show significant balances
                message += f"• {asset}: {total:.4f}\n"

        if len(balances) > 5:
            message += f"• ... and {len(balances) - 5} more assets\n"

        # Add trading permissions if available
        if "can_trade" in account_info:
            trade_status = "✅ Enabled" if account_info["can_trade"] else "❌ Disabled"
            message += f"\n🔄 **Trading:** {trade_status}"

        await update.message.reply_text(message, parse_mode="Markdown")

    async def crypto_positions_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /crypto_positions command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_user_authorized(telegram_id):
            await update.message.reply_text(
                "❌ Subscription required to view crypto positions."
            )
            return

        # Get crypto positions/orders
        positions = await self.crypto_bridge.get_crypto_positions(telegram_id)

        if positions is None:
            await update.message.reply_text(
                "❌ Could not retrieve positions. Check your exchange connection."
            )
            return

        if not positions:
            await update.message.reply_text(
                "📊 **Crypto Positions**\n\nNo open orders or positions."
            )
            return

        message = "📊 **Crypto Positions and Orders**\n\n"

        for pos in positions:
            symbol = pos.get("symbol", "N/A")
            order_id = pos.get("order_id", "N/A")
            side = pos.get("side", "N/A")
            order_type = pos.get("type", "N/A")
            quantity = pos.get("quantity", 0)
            price = pos.get("price", 0)
            status = pos.get("status", "N/A")

            message += f"""🎯 **{symbol}**
ID: {order_id}
📈 {side} {order_type}
📊 Qty: {quantity} | Price: {price}
Status: {status}

"""

        await update.message.reply_text(message, parse_mode="Markdown")

    async def crypto_balance_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /crypto_balance command."""
        await self.crypto_status_command(update, context)

    async def cancel_conversation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Cancel current conversation."""
        await update.message.reply_text("❌ Operation cancelled.")
        context.user_data.clear()
        return ConversationHandler.END
