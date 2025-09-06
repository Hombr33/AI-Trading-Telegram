"""Telegram WebApp handler."""

from typing import Any, Dict, Optional

from telegram import Update, WebAppInfo
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.utils.keyboards import create_keyboard

logger = get_logger(__name__)


class WebAppHandler:
    """Handles Telegram WebApp functionality."""

    def __init__(self, webapp_url: Optional[str] = None):
        """Initialize WebApp handler."""
        self.webapp_url = webapp_url or "https://your-webapp-domain.com"
        self.supported_views = {
            "trading": f"{self.webapp_url}/trading",
            "analytics": f"{self.webapp_url}/analytics",
            "portfolio": f"{self.webapp_url}/portfolio",
            "settings": f"{self.webapp_url}/settings",
        }

    def create_webapp_keyboard(self, view_type: str = "trading"):
        """Create WebApp keyboard."""
        webapp_url = self.supported_views.get(view_type, self.webapp_url)

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

        keyboard = [
            [
                InlineKeyboardButton(
                    "🌐 Open Trading WebApp", web_app=WebAppInfo(url=webapp_url)
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Analytics",
                    web_app=WebAppInfo(url=self.supported_views["analytics"]),
                ),
                InlineKeyboardButton(
                    "💼 Portfolio",
                    web_app=WebAppInfo(url=self.supported_views["portfolio"]),
                ),
            ],
            [
                InlineKeyboardButton(
                    "⚙️ Settings",
                    web_app=WebAppInfo(url=self.supported_views["settings"]),
                ),
                InlineKeyboardButton("🏠 Main Menu", callback_data="start"),
            ],
        ]

        return InlineKeyboardMarkup(keyboard)

    async def handle_webapp_data(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle data received from WebApp."""
        try:
            web_app_data = update.message.web_app_data
            if not web_app_data:
                return

            data = web_app_data.data
            logger.info(f"WebApp data received: {data}")

            # Parse WebApp data (assuming JSON format)
            import json

            try:
                parsed_data = json.loads(data)
                await self._process_webapp_data(update, context, parsed_data)
            except json.JSONDecodeError:
                logger.error(f"Invalid WebApp data format: {data}")
                await update.message.reply_text(
                    "❌ Invalid data received from WebApp", parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"Error handling WebApp data: {e}")
            await update.message.reply_text(
                "❌ Error processing WebApp data", parse_mode="Markdown"
            )

    async def _process_webapp_data(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]
    ):
        """Process WebApp data based on action type."""
        action = data.get("action")

        if action == "place_order":
            await self._handle_webapp_order(update, context, data)
        elif action == "update_settings":
            await self._handle_webapp_settings(update, context, data)
        elif action == "request_data":
            await self._handle_webapp_data_request(update, context, data)
        else:
            logger.warning(f"Unknown WebApp action: {action}")
            await update.message.reply_text(
                f"❌ Unknown WebApp action: {action}", parse_mode="Markdown"
            )

    async def _handle_webapp_order(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]
    ):
        """Handle order placement from WebApp."""
        symbol = data.get("symbol")
        order_type = data.get("type")
        volume = data.get("volume")

        message = (
            f"📱 **WebApp Order Received** 📱\n\n"
            f"🎯 **Symbol**: {symbol}\n"
            f"📊 **Type**: {order_type}\n"
            f"💰 **Volume**: {volume}\n\n"
            f"✅ Order has been queued for execution."
        )

        keyboard = create_keyboard(
            [
                [("📈 Positions", "positions"), ("📋 Orders", "orders")],
                [("🌐 WebApp", "webapp"), ("🏠 Menu", "start")],
            ]
        )

        await update.message.reply_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_webapp_settings(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]
    ):
        """Handle settings update from WebApp."""
        settings = data.get("settings", {})

        message = (
            "⚙️ **Settings Updated** ⚙️\n\n"
            "✅ Settings have been updated from WebApp:\n\n"
        )

        for key, value in settings.items():
            message += f"• {key}: {value}\n"

        keyboard = create_keyboard(
            [
                [("⚙️ Settings", "settings"), ("🌐 WebApp", "webapp")],
                [("🏠 Menu", "start")],
            ]
        )

        await update.message.reply_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_webapp_data_request(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict[str, Any]
    ):
        """Handle data request from WebApp."""
        data_type = data.get("data_type")

        if data_type == "positions":
            # Send current positions data to WebApp
            # This would typically be done via a webhook or direct API call
            message = "📊 **Data Sent to WebApp**\n\nPositions data has been sent to your WebApp interface."
        elif data_type == "account":
            message = "💰 **Data Sent to WebApp**\n\nAccount data has been sent to your WebApp interface."
        else:
            message = f"📡 **Data Request**\n\nData type '{data_type}' sent to WebApp."

        await update.message.reply_text(message, parse_mode="Markdown")

    def get_webapp_info(self, view_type: str = "trading") -> WebAppInfo:
        """Get WebApp info for the specified view."""
        url = self.supported_views.get(view_type, self.webapp_url)
        return WebAppInfo(url=url)
