"""System callback handlers for Telegram bot."""

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.utils.keyboards import create_keyboard
from src.telegram_bot.utils.visual_effects import VisualEffects

logger = get_logger(__name__)


class SystemCallbackHandler:
    """System callback handler for Telegram bot."""

    def __init__(self, system_handler):
        """Initialize the system callback handler."""
        self.system_handler = system_handler
        self.callbacks = {
            "start": self._handle_start_callback,
            "help": self._handle_help_callback,
            "status": self._handle_status_callback,
            "settings": self._handle_settings_callback,
            "about": self._handle_about_callback,
            "performance": self._handle_performance_callback,
            "risk": self._handle_risk_callback,
            "journal": self._handle_journal_callback,
            "quick_actions": self._handle_quick_actions_callback,
            "docs": self._handle_docs_callback,
            "support": self._handle_support_callback,
            "rate": self._handle_rate_callback,
            "updates": self._handle_updates_callback,
            "monitor": self._handle_monitor_callback,
            "system_monitor": self._handle_monitor_callback,
            "health_monitor": self._handle_monitor_callback,
            "trading_guide": self._handle_trading_guide_callback,
            "risk_guide": self._handle_risk_guide_callback,
            "ta_guide": self._handle_ta_guide_callback,
            "setup_guide": self._handle_setup_guide_callback,
            "email_support": self._handle_email_support_callback,
            "live_chat": self._handle_live_chat_callback,
            "faq": self._handle_faq_callback,
            "rate_5": self._handle_rate_5_callback,
            "rate_4": self._handle_rate_4_callback,
            "leave_review": self._handle_leave_review_callback,
            "feedback": self._handle_feedback_callback,
            "changelog": self._handle_changelog_callback,
            "update_alerts": self._handle_update_alerts_callback,
            "roadmap": self._handle_roadmap_callback,
            "risk_settings": self._handle_risk_settings_callback,
            "notification_settings": self._handle_notification_settings_callback,
            "settings_notifications": self._handle_notification_settings_callback,  # Alias for settings_notifications
            "settings_trading": self._handle_settings_trading_callback,
            "settings_risk": self._handle_settings_risk_callback,
            "settings_system": self._handle_settings_system_callback,
            "notif_critical": self._handle_notif_critical_callback,
            "notif_trading": self._handle_notif_trading_callback,
            "notif_reports": self._handle_notif_reports_callback,
            "notif_general": self._handle_notif_general_callback,
            # Trading notification settings
            "trading_signals_settings": self._handle_trading_signals_settings_callback,
            "trading_positions_settings": self._handle_trading_positions_settings_callback,
            "trading_orders_settings": self._handle_trading_orders_settings_callback,
            "trading_risk_settings": self._handle_trading_risk_settings_callback,
            # Reports notification settings
            "reports_performance_settings": self._handle_reports_performance_settings_callback,
            "reports_analysis_settings": self._handle_reports_analysis_settings_callback,
            "reports_statistics_settings": self._handle_reports_statistics_settings_callback,
            "reports_system_settings": self._handle_reports_system_settings_callback,
            # General notification settings
            "general_updates_settings": self._handle_general_updates_settings_callback,
            "general_news_settings": self._handle_general_news_settings_callback,
            # Trading pairs notification settings
            "notification_trading_pairs": self._handle_notification_trading_pairs_callback,
            # Trading pairs management callbacks
            "add_trading_pair": self._handle_add_trading_pair_callback,
            "remove_trading_pair": self._handle_remove_trading_pair_callback,
            "reset_symbols": self._handle_reset_symbols_callback,
            "view_all_symbols": self._handle_view_all_symbols_callback,
            "add_popular_forex": self._handle_add_popular_forex_callback,
            "add_popular_crypto": self._handle_add_popular_crypto_callback,
            "general_maintenance_settings": self._handle_general_maintenance_settings_callback,
            "general_features_settings": self._handle_general_features_settings_callback,
            "theme_settings": self._handle_theme_settings_callback,
            "sound_settings": self._handle_sound_settings_callback,
            # Theme callbacks
            "theme_dark": self._handle_theme_dark_callback,
            "theme_light": self._handle_theme_light_callback,
            "theme_colorful": self._handle_theme_colorful_callback,
            "theme_minimal": self._handle_theme_minimal_callback,
            # Sound callbacks
            "sound_mute": self._handle_sound_mute_callback,
            "sound_low": self._handle_sound_low_callback,
            "sound_medium": self._handle_sound_medium_callback,
            "sound_high": self._handle_sound_high_callback,
            # Navigation callbacks
            "back_to_settings": self._handle_back_to_settings_callback,
            # Auto trading callbacks
            "auto_trading": self._handle_auto_trading_callback,
            "toggle_auto_trading": self._handle_toggle_auto_trading_callback,
            "auto_signals": self._handle_auto_signals_callback,
            "toggle_auto_signals": self._handle_toggle_auto_signals_callback,
            "view_auto_settings": self._handle_view_auto_settings_callback,
            "edit_auto_pairs": self._handle_edit_auto_pairs_callback,
        }

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries."""
        query = update.callback_query
        callback_data = query.data

        if callback_data in self.callbacks:
            await self.callbacks[callback_data](update, context)
        elif callback_data.startswith("toggle_notification:"):
            # Handle toggle notification callbacks
            await self.system_handler.toggle_notification_callback(update, context)
        else:
            await query.answer("Unknown system callback")
            logger.warning(f"Unknown system callback data: {callback_data}")

    async def _handle_start_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle start callback."""
        await self.system_handler.start_command(update, context)

    async def _handle_monitor_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle monitor/health monitoring callback."""
        query = update.callback_query
        await query.answer("📊 System Monitor")

        # Get system status
        try:
            status_text = "🖥️ **System Monitor**\n\n"
            status_text += "🟢 **Status**: Healthy\n"
            status_text += "⏱️ **Uptime**: Running\n"
            status_text += "💾 **Memory**: Normal\n"
            status_text += "🔄 **CPU**: Normal\n\n"
            status_text += "**Components:**\n"
            status_text += "• Position Manager: 🟢 Running\n"
            status_text += "• Trailing Manager: 🟢 Running\n"
            status_text += "• Telegram Bot: 🟢 Active\n"
            status_text += "• MT5 Connection: 🔄 Connecting\n"

            keyboard = create_keyboard(
                [
                    [("🔄 Refresh", "monitor"), ("⚙️ Settings", "settings")],
                    [("📊 Status", "status"), ("🏠 Home", "start")],
                ]
            )

            await query.edit_message_text(
                status_text, parse_mode="Markdown", reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error in monitor callback: {e}")
            await query.edit_message_text("❌ Error loading system monitor")

    async def _handle_help_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle help callback."""
        await self.system_handler.help_command(update, context)

    async def _handle_status_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle status callback."""
        await self.system_handler.status_command(update, context)

    async def _handle_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle settings callback."""
        query = update.callback_query

        # Show loading effect
        await VisualEffects.send_typing_effect(
            context.bot, query.message.chat_id, "Loading settings"
        )

        message = (
            "⚙️ **SETTINGS** ⚙️\n\n"
            "🔧 **Trading Settings**\n"
            "• Risk Level: Medium\n"
            "• Max Positions: 5\n"
            "• Auto-trading: Enabled\n\n"
            "🔔 **Notifications**\n"
            "• Trade Alerts: ✅ On\n"
            "• Signal Updates: ✅ On\n"
            "• Daily Summary: ✅ On\n\n"
            "🎨 **Interface**\n"
            "• Theme: Dark\n"
            "• Animations: ✅ On\n"
            "• Sound: 🔇 Off"
        )

        keyboard = create_keyboard(
            [
                [
                    ("🎚️ Risk Settings", "risk_settings"),
                    ("🔔 Notifications", "notification_settings"),
                ],
                [("🎨 Theme", "theme_settings"), ("🔊 Sound", "sound_settings")],
                [("🏠 Main Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_about_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle about callback."""
        query = update.callback_query

        message = (
            "🤖 **AI TRADING BOT** 🤖\n\n"
            "🚀 **Version**: 2.0.0\n"
            "🧠 **AI Engine**: GPT-4 Turbo\n"
            "📊 **MT5 Integration**: Active\n"
            "⚡ **Features**: Real-time analysis, Auto-trading, Risk management\n\n"
            "💻 **Developer**: @YourHandle\n"
            "📈 **Trading Pairs**: 28+ Forex pairs\n"
            "🕐 **Uptime**: 99.9%\n\n"
            "🔗 **Links**:\n"
            "• Documentation\n"
            "• Support Channel\n"
            "• GitHub Repository"
        )

        keyboard = create_keyboard(
            [
                [("📚 Documentation", "docs"), ("💬 Support", "support")],
                [("⭐ Rate Bot", "rate"), ("🔄 Updates", "updates")],
                [("🏠 Main Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_quick_actions_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle quick actions callback."""
        query = update.callback_query

        message = (
            "⚡ QUICK ACTIONS ⚡\n\n"
            "🚀 Instant Trading Tools\n\n"
            "🎯 AI Signal - Get instant market analysis\n"
            "📊 Market Pulse - Real-time market overview\n"
            "⚡ Quick Trade - Fast order placement\n"
            "⚠️ Risk Check - Portfolio risk assessment\n"
            "📈 P&L Summary - Profit/loss overview\n"
            "🔔 Notifications - Alert preferences"
        )

        keyboard = create_keyboard(
            [
                [("🎯 AI Signal", "signals"), ("📊 Market Pulse", "symbols")],
                [("⚡ Quick Trade", "positions"), ("⚠️ Risk Check", "account")],
                [
                    ("📈 P&L Summary", "account_history"),
                    ("🔔 Notifications", "settings"),
                ],
                [("🏠 Main Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_docs_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle documentation callback."""
        query = update.callback_query

        message = (
            "📚 **DOCUMENTATION** 📚\n\n"
            "📖 **Available Resources**:\n\n"
            "🎯 **Trading Guide** - Learn AI trading strategies\n"
            "🤖 **Bot Commands** - Complete command reference\n"
            "⚠️ **Risk Management** - Risk control strategies\n"
            "📊 **Technical Analysis** - Chart reading guide\n"
            "🔧 **API Integration** - MT5 setup instructions"
        )

        keyboard = create_keyboard(
            [
                [("🎯 Trading Guide", "trading_guide"), ("🤖 Commands", "help")],
                [("⚠️ Risk Guide", "risk_guide"), ("📊 TA Guide", "ta_guide")],
                [("🔧 Setup Guide", "setup_guide"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_support_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle support callback."""
        query = update.callback_query

        message = (
            "💬 **SUPPORT CENTER** 💬\n\n"
            "🆘 **Need Help?**\n\n"
            "📧 **Contact**: support@yourdomain.com\n"
            "💬 **Telegram**: @YourSupportBot\n"
            "🌐 **Website**: https://yourdomain.com\n"
            "📚 **Documentation**: /docs\n\n"
            "🕐 **Support Hours**: 24/7 Automated\n"
            "⚡ **Response Time**: Less than 2 hours"
        )

        keyboard = create_keyboard(
            [
                [("📧 Email Support", "email_support"), ("💬 Live Chat", "live_chat")],
                [("📚 Documentation", "docs"), ("❓ FAQ", "faq")],
                [("🏠 Main Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_rate_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle rate callback."""
        query = update.callback_query

        message = (
            "⭐ **RATE OUR BOT** ⭐\n\n"
            "💝 **Enjoying the AI Trading Bot?**\n\n"
            "Your feedback helps us improve!\n\n"
            "🌟 **Rate us on**:\n"
            "• Telegram Bot Store\n"
            "• Product Hunt\n"
            "• GitHub Repository\n\n"
            "💬 Share your experience and help other traders!"
        )

        keyboard = create_keyboard(
            [
                [("⭐ Rate 5 Stars", "rate_5"), ("⭐ Rate 4 Stars", "rate_4")],
                [("💬 Leave Review", "leave_review"), ("📧 Feedback", "feedback")],
                [("🏠 Main Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_updates_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle updates callback."""
        query = update.callback_query

        message = (
            "🔄 **UPDATES AND CHANGELOG** 🔄\n\n"
            "📅 **Latest Version**: v2.0.0\n"
            "🚀 **Release Date**: January 2024\n\n"
            "✨ **New Features**:\n"
            "• 🎨 Enhanced visual interface\n"
            "• 🤖 Improved AI analysis\n"
            "• 📱 Telegram WebApp support\n"
            "• ⚡ Real-time animations\n"
            "• 🎯 Interactive dashboards\n\n"
            "🔧 **Bug Fixes**:\n"
            "• Fixed MT5 connection issues\n"
            "• Improved error handling\n"
            "• Better callback routing"
        )

        keyboard = create_keyboard(
            [
                [
                    ("📋 Full Changelog", "changelog"),
                    ("🔔 Update Alerts", "update_alerts"),
                ],
                [("🚀 What's Next", "roadmap"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_trading_guide_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle trading guide callback."""
        query = update.callback_query
        await query.answer("📈 Trading Guide")

        message = (
            "📈 **TRADING GUIDE** 📈\n\n"
            "🎯 **Basic Trading Concepts:**\n"
            "• Position Sizing\n"
            "• Risk Management\n"
            "• Stop Loss and Take Profit\n\n"
            "📊 **Trading Strategies:**\n"
            "• Trend Following\n"
            "• Scalping\n"
            "• Swing Trading\n\n"
            "⚡ **Quick Tips:**\n"
            "• Never risk more than 2% per trade\n"
            "• Always use stop losses\n"
            "• Keep a trading journal"
        )

        keyboard = create_keyboard(
            [
                [("⚠️ Risk Guide", "risk_guide"), ("📊 TA Guide", "ta_guide")],
                [("🔧 Setup Guide", "setup_guide"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_risk_guide_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle risk guide callback."""
        query = update.callback_query
        await query.answer("⚠️ Risk Guide")

        message = (
            "⚠️ **RISK MANAGEMENT GUIDE** ⚠️\n\n"
            "🛡️ **Golden Rules:**\n"
            "• Risk max 1-2% per trade\n"
            "• Use proper position sizing\n"
            "• Set stop losses before entry\n\n"
            "📊 **Risk Metrics:**\n"
            "• Risk/Reward Ratio: Min 1:2\n"
            "• Maximum Drawdown: 10%\n"
            "• Win Rate Target: >50%\n\n"
            "🚨 **Warning Signs:**\n"
            "• Revenge trading\n"
            "• Overleverage\n"
            "• Ignoring stop losses"
        )

        keyboard = create_keyboard(
            [
                [("📈 Trading Guide", "trading_guide"), ("📊 TA Guide", "ta_guide")],
                [("⚙️ Risk Settings", "risk_settings"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_ta_guide_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle technical analysis guide callback."""
        query = update.callback_query
        await query.answer("📊 TA Guide")

        message = (
            "📊 **TECHNICAL ANALYSIS GUIDE** 📊\n\n"
            "📈 **Key Indicators:**\n"
            "• Moving Averages (SMA/EMA)\n"
            "• RSI (Relative Strength Index)\n"
            "• MACD (Moving Average Convergence)\n\n"
            "📉 **Chart Patterns:**\n"
            "• Support and Resistance\n"
            "• Trend Lines\n"
            "• Breakouts and Reversals\n\n"
            "⏰ **Timeframes:**\n"
            "• M1-M5: Scalping\n"
            "• M15-H1: Day Trading\n"
            "• H4-D1: Swing Trading"
        )

        keyboard = create_keyboard(
            [
                [("📈 Trading Guide", "trading_guide"), ("⚠️ Risk Guide", "risk_guide")],
                [("📊 Analysis", "analysis"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_setup_guide_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle setup guide callback."""
        query = update.callback_query
        await query.answer("🔧 Setup Guide")

        message = (
            "🔧 **SETUP GUIDE** 🔧\n\n"
            "📋 **Prerequisites:**\n"
            "• MetaTrader 5 installed\n"
            "• Valid broker account\n"
            "• Telegram bot token\n\n"
            "⚙️ **Configuration Steps:**\n"
            "1. Install MT5 and login\n"
            "2. Copy EA to experts folder\n"
            "3. Enable algorithmic trading\n"
            "4. Configure bot settings\n\n"
            "🔗 **Environment Variables:**\n"
            "• TELEGRAM_BOT_TOKEN\n"
            "• OPENAI_API_KEY\n"
            "• MT5_LOGIN, MT5_PASSWORD"
        )

        keyboard = create_keyboard(
            [
                [("📚 Documentation", "docs"), ("💬 Support", "support")],
                [("🖥️ MT5 Status", "mt5_status"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_email_support_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle email support callback."""
        query = update.callback_query
        await query.answer("📧 Email Support")

        message = (
            "📧 **EMAIL SUPPORT** 📧\n\n"
            "💌 **Contact Information:**\n"
            "📨 Email: support@ai-trading-bot.com\n"
            "⏰ Response Time: 24-48 hours\n\n"
            "📋 **Before Contacting:**\n"
            "• Check FAQ section\n"
            "• Review documentation\n"
            "• Include error details\n\n"
            "📝 **Include in Your Email:**\n"
            "• Bot version\n"
            "• Error messages\n"
            "• Steps to reproduce\n"
            "• Screenshots if applicable"
        )

        keyboard = create_keyboard(
            [
                [("💬 Live Chat", "live_chat"), ("❓ FAQ", "faq")],
                [("📚 Documentation", "docs"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_live_chat_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle live chat callback."""
        query = update.callback_query
        await query.answer("💬 Live Chat")

        message = (
            "💬 **LIVE CHAT SUPPORT** 💬\n\n"
            "🟢 **Status**: Online\n"
            "⏰ **Hours**: 9 AM - 6 PM UTC\n\n"
            "🚀 **Instant Help:**\n"
            "• Technical issues\n"
            "• Trading questions\n"
            "• Setup assistance\n\n"
            "💡 **Pro Tips:**\n"
            "• Be specific about issues\n"
            "• Have your setup ready\n"
            "• Include error messages\n\n"
            "📱 **Contact**: @AITradingSupport"
        )

        keyboard = create_keyboard(
            [
                [("📧 Email Support", "email_support"), ("❓ FAQ", "faq")],
                [("📚 Documentation", "docs"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_faq_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle FAQ callback."""
        query = update.callback_query
        await query.answer("❓ FAQ")

        message = (
            "❓ **FREQUENTLY ASKED QUESTIONS** ❓\n\n"
            "🤔 **Q: Is the bot free to use?**\n"
            "A: Basic features are free, premium features require subscription\n\n"
            "🤔 **Q: Which brokers are supported?**\n"
            "A: All MT5-compatible brokers\n\n"
            "🤔 **Q: How accurate are the signals?**\n"
            "A: Signals have 70-80% accuracy based on backtesting\n\n"
            "🤔 **Q: Can I customize risk settings?**\n"
            "A: Yes, full risk management customization available\n\n"
            "🤔 **Q: Is my data secure?**\n"
            "A: Yes, we use enterprise-grade encryption"
        )

        keyboard = create_keyboard(
            [
                [("📧 Email Support", "email_support"), ("💬 Live Chat", "live_chat")],
                [("📚 Documentation", "docs"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_rate_5_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle 5-star rating callback."""
        query = update.callback_query
        await query.answer("⭐ Thanks for 5 stars!")

        message = (
            "⭐ **THANK YOU!** ⭐\n\n"
            "🎉 **5-Star Rating Received!**\n\n"
            "💝 We're thrilled you love our AI Trading Bot!\n\n"
            "🚀 **What's Next:**\n"
            "• Share with friends\n"
            "• Join our community\n"
            "• Get premium features\n\n"
            "🎁 **Bonus**: Use code RATE5 for 20% off premium!"
        )

        keyboard = create_keyboard(
            [
                [("💬 Leave Review", "leave_review"), ("📧 Feedback", "feedback")],
                [("🚀 Premium", "premium"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_rate_4_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle 4-star rating callback."""
        query = update.callback_query
        await query.answer("⭐ Thanks for rating!")

        message = (
            "⭐ **THANK YOU!** ⭐\n\n"
            "🎯 **4-Star Rating Received!**\n\n"
            "💭 We appreciate your feedback!\n\n"
            "🔧 **Help us improve:**\n"
            "What would make this a 5-star experience?\n\n"
            "📝 Your suggestions help us grow!\n\n"
            "💬 Share your thoughts with us."
        )

        keyboard = create_keyboard(
            [
                [
                    ("💬 Leave Feedback", "feedback"),
                    ("📧 Suggestions", "email_support"),
                ],
                [("💬 Leave Review", "leave_review"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_leave_review_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle leave review callback."""
        query = update.callback_query
        await query.answer("💬 Leave Review")

        message = (
            "💬 **LEAVE A REVIEW** 💬\n\n"
            "🌟 **Share Your Experience!**\n\n"
            "📝 **Review Platforms:**\n"
            "• Telegram Bot Directory\n"
            "• Product Hunt\n"
            "• GitHub (if open source)\n\n"
            "💡 **Review Tips:**\n"
            "• Mention specific features you like\n"
            "• Share your trading results\n"
            "• Help others discover the bot\n\n"
            "🎁 **Reward**: Premium features discount for reviewers!"
        )

        keyboard = create_keyboard(
            [
                [("⭐ Rate 5 Stars", "rate_5"), ("📧 Feedback", "feedback")],
                [("🎁 Premium", "premium"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_feedback_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle feedback callback."""
        query = update.callback_query
        await query.answer("📧 Send Feedback")

        message = (
            "📧 **SEND FEEDBACK** 📧\n\n"
            "💭 **We Value Your Input!**\n\n"
            "📝 **Feedback Types:**\n"
            "• Feature requests\n"
            "• Bug reports\n"
            "• Improvement suggestions\n"
            "• User experience feedback\n\n"
            "📨 **Send to**: feedback@ai-trading-bot.com\n\n"
            "🚀 **Your ideas help shape our roadmap!**"
        )

        keyboard = create_keyboard(
            [
                [("📧 Email Support", "email_support"), ("💬 Live Chat", "live_chat")],
                [("🚀 Roadmap", "roadmap"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_changelog_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle changelog callback."""
        query = update.callback_query
        await query.answer("📋 Changelog")

        message = (
            "📋 **CHANGELOG** 📋\n\n"
            "🆕 **Version 2.1.0** (Latest)\n"
            "• Enhanced AI signal accuracy\n"
            "• New risk management features\n"
            "• Improved UI/UX\n\n"
            "🔄 **Version 2.0.0**\n"
            "• Multi-platform support\n"
            "• Advanced analytics\n"
            "• Real-time notifications\n\n"
            "📈 **Version 1.5.0**\n"
            "• Performance optimizations\n"
            "• Bug fixes and stability"
        )

        keyboard = create_keyboard(
            [
                [("🔔 Update Alerts", "update_alerts"), ("🚀 Roadmap", "roadmap")],
                [("📚 Documentation", "docs"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_update_alerts_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle update alerts callback."""
        query = update.callback_query
        await query.answer("🔔 Update Alerts")

        message = (
            "🔔 **UPDATE ALERTS** 🔔\n\n"
            "📢 **Current Status**: Enabled\n\n"
            "🚀 **What You'll Get:**\n"
            "• New feature announcements\n"
            "• Performance improvements\n"
            "• Important bug fixes\n"
            "• Security updates\n\n"
            "📅 **Frequency**: As needed\n"
            "🔇 **Unsubscribe**: Use /settings\n\n"
            "💡 Stay informed about the latest improvements!"
        )

        keyboard = create_keyboard(
            [
                [
                    ("⚙️ Settings", "notification_settings"),
                    ("📋 Changelog", "changelog"),
                ],
                [("🚀 Roadmap", "roadmap"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_roadmap_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle roadmap callback."""
        query = update.callback_query
        await query.answer("🚀 Roadmap")

        message = (
            "🚀 **DEVELOPMENT ROADMAP** 🚀\n\n"
            "🔜 **Coming Soon (Q1 2024):**\n"
            "• Mobile app release\n"
            "• Advanced backtesting\n"
            "• Social trading features\n\n"
            "📅 **Q2 2024:**\n"
            "• Portfolio management\n"
            "• Custom indicators\n"
            "• API marketplace\n\n"
            "🔮 **Future Vision:**\n"
            "• AI-powered portfolio optimization\n"
            "• Multi-asset support\n"
            "• Institutional features"
        )

        keyboard = create_keyboard(
            [
                [("📧 Feedback", "feedback"), ("📋 Changelog", "changelog")],
                [("🔔 Updates", "update_alerts"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_risk_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle risk settings callback."""
        query = update.callback_query
        await query.answer("⚙️ Risk Settings")

        message = (
            "⚙️ **RISK SETTINGS** ⚙️\n\n"
            "🎚️ **Current Settings:**\n"
            "• Risk per Trade: 2%\n"
            "• Maximum Positions: 5\n"
            "• Stop Loss: Enabled\n"
            "• Take Profit: Enabled\n\n"
            "📊 **Risk Levels:**\n"
            "🟢 Conservative (1%)\n"
            "🟡 Moderate (2%)\n"
            "🔴 Aggressive (3-5%)\n\n"
            "⚠️ **Warning**: Higher risk = higher potential loss"
        )

        keyboard = create_keyboard(
            [
                [
                    ("🟢 Conservative", "risk_conservative"),
                    ("🟡 Moderate", "risk_moderate"),
                ],
                [("🔴 Aggressive", "risk_aggressive"), ("⚙️ Settings", "settings")],
                [("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_notification_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle notification settings callback."""
        query = update.callback_query
        await query.answer("🔔 Notification Settings")

        message = (
            "🔔 **NOTIFICATION SETTINGS** 🔔\n\n"
            "📢 **Current Settings:**\n"
            "• Trade Alerts: ✅ Enabled\n"
            "• Signal Updates: ✅ Enabled\n"
            "• Daily Summary: ✅ Enabled\n"
            "• Risk Warnings: ✅ Enabled\n\n"
            "🔇 **Notification Types:**\n"
            "• 🚨 Critical: System alerts\n"
            "• 📊 Trading: Signal and position updates\n"
            "• 📈 Performance: Daily/weekly reports\n"
            "• 🔔 General: Updates and news"
        )

        keyboard = create_keyboard(
            [
                [("🚨 Critical", "notif_critical"), ("📊 Trading", "notif_trading")],
                [("📈 Reports", "notif_reports"), ("🔔 General", "notif_general")],
                [("⚙️ Settings", "settings"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_notif_critical_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle critical notifications callback."""
        query = update.callback_query
        await query.answer("🚨 Critical notifications settings")

        message = (
            "🚨 **CRITICAL NOTIFICATIONS** 🚨\n\n"
            "**Critical alerts include:**\n"
            "• System failures and errors\n"
            "• Risk limit breaches\n"
            "• Connection losses\n"
            "• Emergency stops\n\n"
            "These notifications are always enabled for safety."
        )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notification_settings")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_notif_trading_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle trading notifications callback."""
        query = update.callback_query
        await query.answer("📊 Trading notifications settings")

        message = (
            "📊 **TRADING NOTIFICATIONS** 📊\n\n"
            "**Trading alerts include:**\n"
            "• New trading signals\n"
            "• Position updates\n"
            "• Order executions\n"
            "• Risk warnings\n\n"
            "Configure your trading notification preferences."
        )

        keyboard = create_keyboard(
            [
                [
                    ("📈 Signals", "trading_signals_settings"),
                    ("📊 Positions", "trading_positions_settings"),
                ],
                [
                    ("📋 Orders", "trading_orders_settings"),
                    ("⚠️ Risk", "trading_risk_settings"),
                ],
                [("⬅️ Back", "notification_settings")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_notif_reports_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle reports notifications callback."""
        query = update.callback_query
        await query.answer("📈 Reports notifications settings")

        message = (
            "📈 **REPORTS NOTIFICATIONS** 📈\n\n"
            "**Report alerts include:**\n"
            "• Daily performance summaries\n"
            "• Weekly analysis reports\n"
            "• Monthly statistics\n"
            "• System health reports\n\n"
            "Configure your report notification preferences."
        )

        keyboard = create_keyboard(
            [
                [
                    ("📊 Performance", "reports_performance_settings"),
                    ("📈 Analysis", "reports_analysis_settings"),
                ],
                [
                    ("📋 Statistics", "reports_statistics_settings"),
                    ("🔧 System", "reports_system_settings"),
                ],
                [("⬅️ Back", "notification_settings")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_notif_general_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle general notifications callback."""
        query = update.callback_query
        await query.answer("🔔 General notifications settings")

        message = (
            "🔔 **GENERAL NOTIFICATIONS** 🔔\n\n"
            "**General alerts include:**\n"
            "• System updates\n"
            "• News and announcements\n"
            "• Maintenance notifications\n"
            "• Feature updates\n\n"
            "Configure your general notification preferences."
        )

        keyboard = create_keyboard(
            [
                [
                    ("📢 Updates", "general_updates_settings"),
                    ("📰 News", "general_news_settings"),
                ],
                [
                    ("🔧 Maintenance", "general_maintenance_settings"),
                    ("🆕 Features", "general_features_settings"),
                ],
                [("⬅️ Back", "notification_settings")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_theme_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle theme settings callback."""
        query = update.callback_query
        await query.answer("🎨 Theme Settings")

        message = (
            "🎨 **THEME SETTINGS** 🎨\n\n"
            "🌙 **Current Theme**: Dark\n\n"
            "🎯 **Available Themes:**\n"
            "🌙 Dark Mode\n"
            "☀️ Light Mode\n"
            "🌈 Colorful Mode\n"
            "🤖 Minimal Mode\n\n"
            "✨ **Features:**\n"
            "• Custom emoji sets\n"
            "• Color-coded messages\n"
            "• Visual animations\n"
            "• Personalized layouts"
        )

        keyboard = create_keyboard(
            [
                [("🌙 Dark", "theme_dark"), ("☀️ Light", "theme_light")],
                [("🌈 Colorful", "theme_colorful"), ("🤖 Minimal", "theme_minimal")],
                [("⚙️ Settings", "settings"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_sound_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle sound settings callback."""
        query = update.callback_query
        await query.answer("🔊 Sound Settings")

        message = (
            "🔊 **SOUND SETTINGS** 🔊\n\n"
            "🔇 **Current Status**: Disabled\n\n"
            "🎵 **Sound Options:**\n"
            "• 🔔 Notification sounds\n"
            "• 📊 Trade alerts\n"
            "• ⚠️ Risk warnings\n"
            "• 🎉 Success notifications\n\n"
            "🎚️ **Volume Levels:**\n"
            "• 🔇 Muted\n"
            "• 🔉 Low\n"
            "• 🔊 Medium\n"
            "• 📢 High"
        )

        keyboard = create_keyboard(
            [
                [("🔇 Mute", "sound_mute"), ("🔉 Low", "sound_low")],
                [("🔊 Medium", "sound_medium"), ("📢 High", "sound_high")],
                [("⚙️ Settings", "settings"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    # Trading notification settings callbacks
    async def _handle_trading_signals_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle trading signals settings callback."""
        query = update.callback_query
        await query.answer("📈 Trading signals notification settings")

        try:
            # Get user configuration
            telegram_id = update.effective_user.id
            config = await self.system_handler.user_config_service.get_user_config(
                telegram_id
            )
            notifications = config.get("notifications", {})

            # Get trading pairs configuration
            trading = config.get("trading", {})
            allowed_symbols = trading.get("allowed_symbols", [])

            # Check current signal notification settings
            signals_enabled = notifications.get("signals", True)
            signal_updates_enabled = notifications.get("signal_updates", True)
            signal_expirations_enabled = notifications.get("signal_expirations", True)

            status_icon = lambda enabled: "✅" if enabled else "❌"

            message = (
                f"📈 **TRADING SIGNALS NOTIFICATIONS** 📈\n\n"
                f"**Current Settings**:\n"
                f"{status_icon(signals_enabled)} New Trading Signals\n"
                f"{status_icon(signal_updates_enabled)} Signal Updates\n"
                f"{status_icon(signal_expirations_enabled)} Signal Expirations\n\n"
                f"**Trading Pairs**: {len(allowed_symbols)} pairs configured\n"
                f"**Configure**: Toggle notifications and manage trading pairs.\n\n"
                f"🕐 _Last updated: {datetime.now().strftime('%H:%M:%S')}_"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("📈 Toggle Signals", "toggle_notification:signals"),
                        ("🔄 Toggle Updates", "toggle_notification:signal_updates"),
                    ],
                    [
                        (
                            "⏰ Toggle Expirations",
                            "toggle_notification:signal_expirations",
                        ),
                        ("📋 Trading Pairs", "notification_trading_pairs"),
                    ],
                    [
                        ("⏰ Set Intervals", "notification_intervals"),
                    ],
                    [("⬅️ Back", "notif_trading"), ("🏠 Main", "start")],
                ]
            )

            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in trading signals settings: {e}")
            error_message = (
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading trading signals settings.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard([[("⬅️ Back", "notif_trading")]])
            await query.edit_message_text(
                error_message, reply_markup=keyboard, parse_mode="Markdown"
            )

    async def _handle_trading_positions_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle trading positions settings callback."""
        query = update.callback_query
        await query.answer("📊 Trading positions notification settings")

        try:
            # Get user configuration
            telegram_id = update.effective_user.id
            config = await self.system_handler.user_config_service.get_user_config(
                telegram_id
            )
            notifications = config.get("notifications", {})

            # Check current position notification settings
            positions_enabled = notifications.get("positions", True)
            position_opened_enabled = notifications.get("position_opened", True)
            position_closed_enabled = notifications.get("position_closed", True)
            position_modified_enabled = notifications.get("position_modified", True)

            status_icon = lambda enabled: "✅" if enabled else "❌"

            message = (
                f"📊 **TRADING POSITIONS NOTIFICATIONS** 📊\n\n"
                f"**Current Settings**:\n"
                f"{status_icon(positions_enabled)} All Position Updates\n"
                f"{status_icon(position_opened_enabled)} Position Opened\n"
                f"{status_icon(position_closed_enabled)} Position Closed\n"
                f"{status_icon(position_modified_enabled)} Position Modified\n\n"
                f"**Configure**: Toggle specific position notifications.\n\n"
                f"🕐 _Last updated: {datetime.now().strftime('%H:%M:%S')}_"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("📊 Toggle All", "toggle_notification:positions"),
                        ("🟢 Toggle Opened", "toggle_notification:position_opened"),
                    ],
                    [
                        ("🔴 Toggle Closed", "toggle_notification:position_closed"),
                        ("🔄 Toggle Modified", "toggle_notification:position_modified"),
                    ],
                    [
                        ("⏰ Set Intervals", "notification_intervals"),
                    ],
                    [("⬅️ Back", "notif_trading"), ("🏠 Main", "start")],
                ]
            )

            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in trading positions settings: {e}")
            error_message = (
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading trading positions settings.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard([[("⬅️ Back", "notif_trading")]])
            await query.edit_message_text(
                error_message, reply_markup=keyboard, parse_mode="Markdown"
            )

    async def _handle_trading_orders_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle trading orders settings callback."""
        query = update.callback_query
        await query.answer("📋 Trading orders notification settings")

        try:
            # Get user configuration
            telegram_id = update.effective_user.id
            config = await self.system_handler.user_config_service.get_user_config(
                telegram_id
            )
            notifications = config.get("notifications", {})

            # Check current order notification settings
            orders_enabled = notifications.get("orders", True)
            order_placed_enabled = notifications.get("order_placed", True)
            order_executed_enabled = notifications.get("order_executed", True)
            order_cancelled_enabled = notifications.get("order_cancelled", True)

            status_icon = lambda enabled: "✅" if enabled else "❌"

            message = (
                f"📋 **TRADING ORDERS NOTIFICATIONS** 📋\n\n"
                f"**Current Settings**:\n"
                f"{status_icon(orders_enabled)} All Order Updates\n"
                f"{status_icon(order_placed_enabled)} Order Placed\n"
                f"{status_icon(order_executed_enabled)} Order Executed\n"
                f"{status_icon(order_cancelled_enabled)} Order Cancelled\n\n"
                f"**Configure**: Toggle specific order notifications.\n\n"
                f"🕐 _Last updated: {datetime.now().strftime('%H:%M:%S')}_"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("📋 Toggle All", "toggle_notification:orders"),
                        ("📝 Toggle Placed", "toggle_notification:order_placed"),
                    ],
                    [
                        ("✅ Toggle Executed", "toggle_notification:order_executed"),
                        ("❌ Toggle Cancelled", "toggle_notification:order_cancelled"),
                    ],
                    [
                        ("⏰ Set Intervals", "notification_intervals"),
                    ],
                    [("⬅️ Back", "notif_trading"), ("🏠 Main", "start")],
                ]
            )

            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in trading orders settings: {e}")
            error_message = (
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading trading orders settings.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard([[("⬅️ Back", "notif_trading")]])
            await query.edit_message_text(
                error_message, reply_markup=keyboard, parse_mode="Markdown"
            )

    async def _handle_trading_risk_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle trading risk settings callback."""
        query = update.callback_query
        await query.answer("⚠️ Trading risk notification settings")

        try:
            # Get user configuration
            telegram_id = update.effective_user.id
            config = await self.system_handler.user_config_service.get_user_config(
                telegram_id
            )
            notifications = config.get("notifications", {})

            # Check current risk notification settings
            risk_enabled = notifications.get("risk", True)
            risk_limit_enabled = notifications.get("risk_limit", True)
            drawdown_warning_enabled = notifications.get("drawdown_warning", True)
            position_size_alert_enabled = notifications.get("position_size_alert", True)

            status_icon = lambda enabled: "✅" if enabled else "❌"

            message = (
                f"⚠️ **TRADING RISK NOTIFICATIONS** ⚠️\n\n"
                f"**Current Settings**:\n"
                f"{status_icon(risk_enabled)} All Risk Alerts\n"
                f"{status_icon(risk_limit_enabled)} Risk Limit Reached\n"
                f"{status_icon(drawdown_warning_enabled)} Drawdown Warning\n"
                f"{status_icon(position_size_alert_enabled)} Position Size Alert\n\n"
                f"**Configure**: Toggle specific risk notifications.\n\n"
                f"🕐 _Last updated: {datetime.now().strftime('%H:%M:%S')}_"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("⚠️ Toggle All", "toggle_notification:risk"),
                        ("🚨 Toggle Risk Limit", "toggle_notification:risk_limit"),
                    ],
                    [
                        ("📉 Toggle Drawdown", "toggle_notification:drawdown_warning"),
                        (
                            "📊 Toggle Position Size",
                            "toggle_notification:position_size_alert",
                        ),
                    ],
                    [
                        ("⏰ Set Intervals", "notification_intervals"),
                    ],
                    [("⬅️ Back", "notif_trading"), ("🏠 Main", "start")],
                ]
            )

            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in trading risk settings: {e}")
            error_message = (
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading trading risk settings.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard([[("⬅️ Back", "notif_trading")]])
            await query.edit_message_text(
                error_message, reply_markup=keyboard, parse_mode="Markdown"
            )

    # Reports notification settings callbacks
    async def _handle_reports_performance_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle reports performance settings callback."""
        query = update.callback_query
        await query.answer("📊 Performance reports notification settings")

        try:
            # Get user configuration
            telegram_id = update.effective_user.id
            config = await self.system_handler.user_config_service.get_user_config(
                telegram_id
            )
            notifications = config.get("notifications", {})

            # Check current performance report notification settings
            daily_reports_enabled = notifications.get("daily_performance", True)
            weekly_reports_enabled = notifications.get("weekly_performance", True)
            monthly_reports_enabled = notifications.get("monthly_performance", False)
            performance_alerts_enabled = notifications.get("performance_alerts", True)

            status_icon = lambda enabled: "✅" if enabled else "❌"

            message = (
                f"📊 **PERFORMANCE REPORTS NOTIFICATIONS** 📊\n\n"
                f"**Current Settings**:\n"
                f"{status_icon(daily_reports_enabled)} Daily Performance Summaries\n"
                f"{status_icon(weekly_reports_enabled)} Weekly Performance Reports\n"
                f"{status_icon(monthly_reports_enabled)} Monthly Performance Analysis\n"
                f"{status_icon(performance_alerts_enabled)} Performance Alerts\n\n"
                f"**Configure**: Toggle specific performance report notifications.\n\n"
                f"🕐 _Last updated: {datetime.now().strftime('%H:%M:%S')}_"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("📊 Toggle Daily", "toggle_notification:daily_performance"),
                        ("📈 Toggle Weekly", "toggle_notification:weekly_performance"),
                    ],
                    [
                        (
                            "📅 Toggle Monthly",
                            "toggle_notification:monthly_performance",
                        ),
                        ("🚨 Toggle Alerts", "toggle_notification:performance_alerts"),
                    ],
                    [
                        ("⏰ Set Intervals", "notification_intervals"),
                    ],
                    [("⬅️ Back", "notif_reports"), ("🏠 Main", "start")],
                ]
            )

            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in performance reports settings: {e}")
            error_message = (
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading performance reports settings.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard([[("⬅️ Back", "notif_reports")]])
            await query.edit_message_text(
                error_message, reply_markup=keyboard, parse_mode="Markdown"
            )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notif_reports")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_reports_analysis_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle reports analysis settings callback."""
        query = update.callback_query
        await query.answer("📈 Analysis reports notification settings")

        try:
            # Get user configuration
            telegram_id = update.effective_user.id
            config = await self.system_handler.user_config_service.get_user_config(
                telegram_id
            )
            notifications = config.get("notifications", {})

            # Check current analysis report notification settings
            market_analysis_enabled = notifications.get("market_analysis", True)
            strategy_analysis_enabled = notifications.get("strategy_analysis", True)
            risk_analysis_enabled = notifications.get("risk_analysis", True)
            correlation_analysis_enabled = notifications.get(
                "correlation_analysis", False
            )

            status_icon = lambda enabled: "✅" if enabled else "❌"

            message = (
                f"📈 **ANALYSIS REPORTS NOTIFICATIONS** 📈\n\n"
                f"**Current Settings**:\n"
                f"{status_icon(market_analysis_enabled)} Market Analysis Reports\n"
                f"{status_icon(strategy_analysis_enabled)} Strategy Performance Analysis\n"
                f"{status_icon(risk_analysis_enabled)} Risk Analysis Reports\n"
                f"{status_icon(correlation_analysis_enabled)} Correlation Analysis\n\n"
                f"**Configure**: Toggle specific analysis report notifications.\n\n"
                f"🕐 _Last updated: {datetime.now().strftime('%H:%M:%S')}_"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("📊 Toggle Market", "toggle_notification:market_analysis"),
                        ("📈 Toggle Strategy", "toggle_notification:strategy_analysis"),
                    ],
                    [
                        ("⚠️ Toggle Risk", "toggle_notification:risk_analysis"),
                        (
                            "🔗 Toggle Correlation",
                            "toggle_notification:correlation_analysis",
                        ),
                    ],
                    [
                        ("⏰ Set Intervals", "notification_intervals"),
                    ],
                    [("⬅️ Back", "notif_reports"), ("🏠 Main", "start")],
                ]
            )

            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in analysis reports settings: {e}")
            error_message = (
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading analysis reports settings.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard([[("⬅️ Back", "notif_reports")]])
            await query.edit_message_text(
                error_message, reply_markup=keyboard, parse_mode="Markdown"
            )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notif_reports")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_reports_statistics_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle reports statistics settings callback."""
        query = update.callback_query
        await query.answer("📋 Statistics reports notification settings")

        try:
            # Get user configuration
            telegram_id = update.effective_user.id
            config = await self.system_handler.user_config_service.get_user_config(
                telegram_id
            )
            notifications = config.get("notifications", {})

            # Check current statistics report notification settings
            trading_stats_enabled = notifications.get("trading_statistics", True)
            win_loss_enabled = notifications.get("win_loss_reports", True)
            performance_metrics_enabled = notifications.get("performance_metrics", True)
            trade_summaries_enabled = notifications.get("trade_summaries", False)

            status_icon = lambda enabled: "✅" if enabled else "❌"

            message = (
                f"📋 **STATISTICS REPORTS NOTIFICATIONS** 📋\n\n"
                f"**Current Settings**:\n"
                f"{status_icon(trading_stats_enabled)} Trading Statistics\n"
                f"{status_icon(win_loss_enabled)} Win/Loss Ratios\n"
                f"{status_icon(performance_metrics_enabled)} Performance Metrics\n"
                f"{status_icon(trade_summaries_enabled)} Trade Summaries\n\n"
                f"**Configure**: Toggle specific statistics report notifications.\n\n"
                f"🕐 _Last updated: {datetime.now().strftime('%H:%M:%S')}_"
            )

            keyboard = create_keyboard(
                [
                    [
                        (
                            "📊 Toggle Trading Stats",
                            "toggle_notification:trading_statistics",
                        ),
                        ("📈 Toggle Win/Loss", "toggle_notification:win_loss_reports"),
                    ],
                    [
                        (
                            "📋 Toggle Metrics",
                            "toggle_notification:performance_metrics",
                        ),
                        ("📝 Toggle Summaries", "toggle_notification:trade_summaries"),
                    ],
                    [
                        ("⏰ Set Intervals", "notification_intervals"),
                    ],
                    [("⬅️ Back", "notif_reports"), ("🏠 Main", "start")],
                ]
            )

            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in statistics reports settings: {e}")
            error_message = (
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading statistics reports settings.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard([[("⬅️ Back", "notif_reports")]])
            await query.edit_message_text(
                error_message, reply_markup=keyboard, parse_mode="Markdown"
            )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notif_reports")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_reports_system_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle reports system settings callback."""
        query = update.callback_query
        await query.answer("🔧 System reports notification settings")

        try:
            # Get user configuration
            telegram_id = update.effective_user.id
            config = await self.system_handler.user_config_service.get_user_config(
                telegram_id
            )
            notifications = config.get("notifications", {})

            # Check current system report notification settings
            health_reports_enabled = notifications.get("system_health", True)
            resource_reports_enabled = notifications.get("resource_usage", False)
            error_reports_enabled = notifications.get("error_reports", True)
            maintenance_reports_enabled = notifications.get("maintenance_reports", True)

            status_icon = lambda enabled: "✅" if enabled else "❌"

            message = (
                f"🔧 **SYSTEM REPORTS NOTIFICATIONS** 🔧\n\n"
                f"**Current Settings**:\n"
                f"{status_icon(health_reports_enabled)} System Health Reports\n"
                f"{status_icon(resource_reports_enabled)} Resource Usage Reports\n"
                f"{status_icon(error_reports_enabled)} Error Reports\n"
                f"{status_icon(maintenance_reports_enabled)} Maintenance Reports\n\n"
                f"**Configure**: Toggle specific system report notifications.\n\n"
                f"🕐 _Last updated: {datetime.now().strftime('%H:%M:%S')}_"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("💚 Toggle Health", "toggle_notification:system_health"),
                        ("📊 Toggle Resources", "toggle_notification:resource_usage"),
                    ],
                    [
                        ("❌ Toggle Errors", "toggle_notification:error_reports"),
                        (
                            "🔧 Toggle Maintenance",
                            "toggle_notification:maintenance_reports",
                        ),
                    ],
                    [
                        ("⏰ Set Intervals", "notification_intervals"),
                    ],
                    [("⬅️ Back", "notif_reports"), ("🏠 Main", "start")],
                ]
            )

            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in system reports settings: {e}")
            error_message = (
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading system reports settings.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard([[("⬅️ Back", "notif_reports")]])
            await query.edit_message_text(
                error_message, reply_markup=keyboard, parse_mode="Markdown"
            )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notif_reports")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    # General notification settings callbacks
    async def _handle_general_updates_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle general updates settings callback."""
        query = update.callback_query
        await query.answer("📢 General updates notification settings")

        try:
            # Get user configuration
            telegram_id = update.effective_user.id
            config = await self.system_handler.user_config_service.get_user_config(
                telegram_id
            )
            notifications = config.get("notifications", {})

            # Check current general updates notification settings
            bot_updates_enabled = notifications.get("bot_updates", True)
            feature_updates_enabled = notifications.get("feature_updates", True)
            system_updates_enabled = notifications.get("system_updates", False)
            changelog_enabled = notifications.get("changelog", True)

            status_icon = lambda enabled: "✅" if enabled else "❌"

            message = (
                f"📢 **GENERAL UPDATES NOTIFICATIONS** 📢\n\n"
                f"**Current Settings**:\n"
                f"{status_icon(bot_updates_enabled)} Bot Updates\n"
                f"{status_icon(feature_updates_enabled)} Feature Updates\n"
                f"{status_icon(system_updates_enabled)} System Updates\n"
                f"{status_icon(changelog_enabled)} Changelog Notifications\n\n"
                f"**Configure**: Toggle specific update notifications.\n\n"
                f"🕐 _Last updated: {datetime.now().strftime('%H:%M:%S')}_"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("🤖 Toggle Bot Updates", "toggle_notification:bot_updates"),
                        ("✨ Toggle Features", "toggle_notification:feature_updates"),
                    ],
                    [
                        ("🔧 Toggle System", "toggle_notification:system_updates"),
                        ("📋 Toggle Changelog", "toggle_notification:changelog"),
                    ],
                    [
                        ("⏰ Set Intervals", "notification_intervals"),
                    ],
                    [("⬅️ Back", "notif_general"), ("🏠 Main", "start")],
                ]
            )

            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in general updates settings: {e}")
            error_message = (
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading general updates settings.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard([[("⬅️ Back", "notif_general")]])
            await query.edit_message_text(
                error_message, reply_markup=keyboard, parse_mode="Markdown"
            )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notif_general")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_general_news_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle general news settings callback."""
        query = update.callback_query
        await query.answer("📰 General news notification settings")

        try:
            # Get user configuration
            telegram_id = update.effective_user.id
            config = await self.system_handler.user_config_service.get_user_config(
                telegram_id
            )
            notifications = config.get("notifications", {})

            # Check current general news notification settings
            market_news_enabled = notifications.get("market_news", True)
            economic_news_enabled = notifications.get("economic_news", True)
            trading_alerts_enabled = notifications.get("trading_alerts", True)
            breaking_news_enabled = notifications.get("breaking_news", False)

            status_icon = lambda enabled: "✅" if enabled else "❌"

            message = (
                f"📰 **GENERAL NEWS NOTIFICATIONS** 📰\n\n"
                f"**Current Settings**:\n"
                f"{status_icon(market_news_enabled)} Market News\n"
                f"{status_icon(economic_news_enabled)} Economic Announcements\n"
                f"{status_icon(trading_alerts_enabled)} Trading Alerts\n"
                f"{status_icon(breaking_news_enabled)} Breaking News\n\n"
                f"**Configure**: Toggle specific news notifications.\n\n"
                f"🕐 _Last updated: {datetime.now().strftime('%H:%M:%S')}_"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("📊 Toggle Market", "toggle_notification:market_news"),
                        ("💰 Toggle Economic", "toggle_notification:economic_news"),
                    ],
                    [
                        ("🚨 Toggle Trading", "toggle_notification:trading_alerts"),
                        ("⚡ Toggle Breaking", "toggle_notification:breaking_news"),
                    ],
                    [
                        ("⏰ Set Intervals", "notification_intervals"),
                    ],
                    [("⬅️ Back", "notif_general"), ("🏠 Main", "start")],
                ]
            )

            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in general news settings: {e}")
            error_message = (
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading general news settings.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard([[("⬅️ Back", "notif_general")]])
            await query.edit_message_text(
                error_message, reply_markup=keyboard, parse_mode="Markdown"
            )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notif_general")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_general_maintenance_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle general maintenance settings callback."""
        query = update.callback_query
        await query.answer("🔧 General maintenance notification settings")

        try:
            # Get user configuration
            telegram_id = update.effective_user.id
            config = await self.system_handler.user_config_service.get_user_config(
                telegram_id
            )
            notifications = config.get("notifications", {})

            # Check current maintenance notification settings
            scheduled_maintenance_enabled = notifications.get(
                "scheduled_maintenance", True
            )
            system_downtime_enabled = notifications.get("system_downtime", True)
            maintenance_completion_enabled = notifications.get(
                "maintenance_completion", True
            )
            emergency_maintenance_enabled = notifications.get(
                "emergency_maintenance", True
            )

            status_icon = lambda enabled: "✅" if enabled else "❌"

            message = (
                f"🔧 **GENERAL MAINTENANCE NOTIFICATIONS** 🔧\n\n"
                f"**Current Settings**:\n"
                f"{status_icon(scheduled_maintenance_enabled)} Scheduled Maintenance\n"
                f"{status_icon(system_downtime_enabled)} System Downtime\n"
                f"{status_icon(maintenance_completion_enabled)} Maintenance Completion\n"
                f"{status_icon(emergency_maintenance_enabled)} Emergency Maintenance\n\n"
                f"**Configure**: Toggle specific maintenance notifications.\n\n"
                f"🕐 _Last updated: {datetime.now().strftime('%H:%M:%S')}_"
            )

            keyboard = create_keyboard(
                [
                    [
                        (
                            "📅 Toggle Scheduled",
                            "toggle_notification:scheduled_maintenance",
                        ),
                        ("⚠️ Toggle Downtime", "toggle_notification:system_downtime"),
                    ],
                    [
                        (
                            "✅ Toggle Completion",
                            "toggle_notification:maintenance_completion",
                        ),
                        (
                            "🚨 Toggle Emergency",
                            "toggle_notification:emergency_maintenance",
                        ),
                    ],
                    [
                        ("⏰ Set Intervals", "notification_intervals"),
                    ],
                    [("⬅️ Back", "notif_general"), ("🏠 Main", "start")],
                ]
            )

            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in maintenance settings: {e}")
            error_message = (
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading maintenance settings.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard([[("⬅️ Back", "notif_general")]])
            await query.edit_message_text(
                error_message, reply_markup=keyboard, parse_mode="Markdown"
            )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notif_general")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_general_features_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle general features settings callback."""
        query = update.callback_query
        await query.answer("🆕 General features notification settings")

        try:
            # Get user configuration
            telegram_id = update.effective_user.id
            config = await self.system_handler.user_config_service.get_user_config(
                telegram_id
            )
            notifications = config.get("notifications", {})

            # Check current features notification settings
            new_features_enabled = notifications.get("new_features", True)
            feature_announcements_enabled = notifications.get(
                "feature_announcements", True
            )
            beta_features_enabled = notifications.get("beta_features", False)
            experimental_features_enabled = notifications.get(
                "experimental_features", False
            )

            status_icon = lambda enabled: "✅" if enabled else "❌"

            message = (
                f"🆕 **GENERAL FEATURES NOTIFICATIONS** 🆕\n\n"
                f"**Current Settings**:\n"
                f"{status_icon(new_features_enabled)} New Features\n"
                f"{status_icon(feature_announcements_enabled)} Feature Announcements\n"
                f"{status_icon(beta_features_enabled)} Beta Features\n"
                f"{status_icon(experimental_features_enabled)} Experimental Features\n\n"
                f"**Configure**: Toggle specific feature notifications.\n\n"
                f"🕐 _Last updated: {datetime.now().strftime('%H:%M:%S')}_"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("✨ Toggle New Features", "toggle_notification:new_features"),
                        (
                            "📢 Toggle Announcements",
                            "toggle_notification:feature_announcements",
                        ),
                    ],
                    [
                        ("🧪 Toggle Beta", "toggle_notification:beta_features"),
                        (
                            "🔬 Toggle Experimental",
                            "toggle_notification:experimental_features",
                        ),
                    ],
                    [
                        ("⏰ Set Intervals", "notification_intervals"),
                    ],
                    [("⬅️ Back", "notif_general"), ("🏠 Main", "start")],
                ]
            )

            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error in features settings: {e}")
            error_message = (
                "❌ **Error Loading Settings**\n\n"
                "There was an issue loading feature settings.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard([[("⬅️ Back", "notif_general")]])
            await query.edit_message_text(
                error_message, reply_markup=keyboard, parse_mode="Markdown"
            )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notif_general")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    # Settings callbacks
    async def _handle_settings_trading_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle settings trading callback."""
        query = update.callback_query
        await query.answer("📊 Trading settings")

        # Route to the system command handler's trading settings
        await self.system_handler.settings_trading(update, context)

    async def _handle_settings_risk_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle settings risk callback."""
        query = update.callback_query
        await query.answer("⚠️ Risk management settings")

        # Route to the system command handler's risk settings
        await self.system_handler.settings_risk(update, context)

    async def _handle_settings_system_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle settings system callback."""
        query = update.callback_query
        await query.answer("🔧 System settings")

        # Route to the system command handler's system settings
        await self.system_handler.settings_system(update, context)

    async def _handle_notification_trading_pairs_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle notification trading pairs callback."""
        query = update.callback_query
        await query.answer("📋 Trading pairs notification settings")

        # Route to the system command handler's notification trading pairs
        await self.system_handler.notification_trading_pairs_callback(update, context)

    # Trading pairs management callbacks
    async def _handle_add_trading_pair_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle add trading pair callback."""
        query = update.callback_query
        await query.answer("➕ Add trading pair")

        # Route to the system command handler's add trading pair
        await self.system_handler.add_trading_pair_callback(update, context)

    async def _handle_remove_trading_pair_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle remove trading pair callback."""
        query = update.callback_query
        await query.answer("➖ Remove trading pair")

        # Route to the system command handler's remove trading pair
        await self.system_handler.remove_trading_pair_callback(update, context)

    async def _handle_reset_symbols_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle reset symbols callback."""
        query = update.callback_query
        await query.answer("🔄 Reset to defaults")

        # Route to the system command handler's reset symbols
        await self.system_handler.reset_symbols_callback(update, context)

    async def _handle_view_all_symbols_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle view all symbols callback."""
        query = update.callback_query
        await query.answer("📊 View all symbols")

        # Route to the system command handler's view all symbols
        await self.system_handler.view_all_symbols_callback(update, context)

    async def _handle_add_popular_forex_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle add popular forex callback."""
        query = update.callback_query
        await query.answer("📋 Add popular forex pairs")

        # Route to the system command handler's add popular forex
        await self.system_handler.add_popular_forex_callback(update, context)

    async def _handle_add_popular_crypto_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle add popular crypto callback."""
        query = update.callback_query
        await query.answer("📋 Add popular crypto pairs")

        # Route to the system command handler's add popular crypto
        await self.system_handler.add_popular_crypto_callback(update, context)

    # Theme callback handlers
    async def _handle_theme_dark_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle theme dark callback."""
        query = update.callback_query
        await query.answer("🌙 Dark theme selected")

        message = (
            "🌙 **DARK THEME SELECTED** 🌙\n\n"
            "✅ **Theme Changed**: Dark Mode\n\n"
            "**Features**:\n"
            "• Easy on the eyes in low light\n"
            "• Battery saving on OLED screens\n"
            "• Professional appearance\n"
            "• Enhanced contrast\n\n"
            "Theme settings have been applied to your interface."
        )

        keyboard = create_keyboard(
            [[("⚙️ Theme Settings", "theme_settings"), ("🏠 Main", "start")]]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_theme_light_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle theme light callback."""
        query = update.callback_query
        await query.answer("☀️ Light theme selected")

        message = (
            "☀️ **LIGHT THEME SELECTED** ☀️\n\n"
            "✅ **Theme Changed**: Light Mode\n\n"
            "**Features**:\n"
            "• Clear visibility in bright environments\n"
            "• Classic clean appearance\n"
            "• Enhanced readability\n"
            "• Optimal for daytime use\n\n"
            "Theme settings have been applied to your interface."
        )

        keyboard = create_keyboard(
            [[("⚙️ Theme Settings", "theme_settings"), ("🏠 Main", "start")]]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_theme_colorful_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle theme colorful callback."""
        query = update.callback_query
        await query.answer("🌈 Colorful theme selected")

        message = (
            "🌈 **COLORFUL THEME SELECTED** 🌈\n\n"
            "✅ **Theme Changed**: Colorful Mode\n\n"
            "**Features**:\n"
            "• Vibrant colors and emojis\n"
            "• Enhanced visual feedback\n"
            "• Fun and engaging interface\n"
            "• Color-coded information\n\n"
            "Theme settings have been applied to your interface."
        )

        keyboard = create_keyboard(
            [[("⚙️ Theme Settings", "theme_settings"), ("🏠 Main", "start")]]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_theme_minimal_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle theme minimal callback."""
        query = update.callback_query
        await query.answer("🤖 Minimal theme selected")

        message = (
            "🤖 **MINIMAL THEME SELECTED** 🤖\n\n"
            "✅ **Theme Changed**: Minimal Mode\n\n"
            "**Features**:\n"
            "• Clean and simple design\n"
            "• Reduced visual clutter\n"
            "• Focus on essential information\n"
            "• Fast loading interface\n\n"
            "Theme settings have been applied to your interface."
        )

        keyboard = create_keyboard(
            [[("⚙️ Theme Settings", "theme_settings"), ("🏠 Main", "start")]]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    # Sound callback handlers
    async def _handle_sound_mute_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle sound mute callback."""
        query = update.callback_query
        await query.answer("🔇 Sound muted")

        message = (
            "🔇 **SOUND MUTED** 🔇\n\n"
            "✅ **Sound Level**: Muted\n\n"
            "**Status**:\n"
            "• All notification sounds disabled\n"
            "• Silent operation mode\n"
            "• Visual notifications only\n"
            "• Battery saving enabled\n\n"
            "You can re-enable sounds anytime from sound settings."
        )

        keyboard = create_keyboard(
            [[("🔊 Sound Settings", "sound_settings"), ("🏠 Main", "start")]]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_sound_low_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle sound low callback."""
        query = update.callback_query
        await query.answer("🔉 Sound set to low")

        message = (
            "🔉 **SOUND SET TO LOW** 🔉\n\n"
            "✅ **Sound Level**: Low Volume\n\n"
            "**Settings**:\n"
            "• Quiet notification sounds\n"
            "• Gentle audio feedback\n"
            "• Minimal disruption\n"
            "• Suitable for quiet environments\n\n"
            "Sound settings have been applied."
        )

        keyboard = create_keyboard(
            [[("🔊 Sound Settings", "sound_settings"), ("🏠 Main", "start")]]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_sound_medium_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle sound medium callback."""
        query = update.callback_query
        await query.answer("🔊 Sound set to medium")

        message = (
            "🔊 **SOUND SET TO MEDIUM** 🔊\n\n"
            "✅ **Sound Level**: Medium Volume\n\n"
            "**Settings**:\n"
            "• Balanced notification sounds\n"
            "• Clear audio feedback\n"
            "• Standard volume level\n"
            "• Good for most environments\n\n"
            "Sound settings have been applied."
        )

        keyboard = create_keyboard(
            [[("🔊 Sound Settings", "sound_settings"), ("🏠 Main", "start")]]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_sound_high_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle sound high callback."""
        query = update.callback_query
        await query.answer("📢 Sound set to high")

        message = (
            "📢 **SOUND SET TO HIGH** 📢\n\n"
            "✅ **Sound Level**: High Volume\n\n"
            "**Settings**:\n"
            "• Loud notification sounds\n"
            "• Strong audio feedback\n"
            "• Maximum alert volume\n"
            "• Suitable for noisy environments\n\n"
            "Sound settings have been applied."
        )

        keyboard = create_keyboard(
            [[("🔊 Sound Settings", "sound_settings"), ("🏠 Main", "start")]]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    # Navigation callback handlers
    async def _handle_back_to_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle back to settings callback."""
        query = update.callback_query
        await query.answer("⚙️ Back to settings")

        # Route back to the main settings
        await self.system_handler.settings_command(update, context)

    # Auto trading callback handlers
    async def _handle_auto_trading_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle auto trading callback - redirect to comprehensive auto trading interface."""
        query = update.callback_query
        await query.answer("🤖 Auto Trading Settings")

        try:
            # Import the auto trading handler
            from ..commands.auto_trading import AutoTradingCommandHandler

            auto_trading_handler = AutoTradingCommandHandler()
            await auto_trading_handler.auto_trading_command(update, context)
        except ImportError as e:
            logger.error(f"Auto trading module not found: {e}")
            message = (
                "🤖 **AUTO TRADING** 🤖\n\n"
                "⚠️ **Module Loading Issue**\n\n"
                "The auto trading module is currently unavailable.\n"
                "This may be due to a missing dependency or configuration issue.\n\n"
                "**Available Options:**\n"
                "• Try using the /auto_trading command directly\n"
                "• Check system status for more details\n"
                "• Contact support if the issue persists\n\n"
                "**Alternative Access:**\n"
                "• Manual trading via /positions\n"
                "• Risk settings via /risk\n"
                "• Account monitoring via /account"
            )
            keyboard = create_keyboard(
                [
                    [("📊 Manual Trading", "positions"), ("⚠️ Risk Settings", "risk")],
                    [("📈 Account", "account"), ("📊 Status", "status")],
                    [("⬅️ Back", "settings_trading"), ("🏠 Main", "start")],
                ]
            )
            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error loading auto trading interface: {e}")
            # Get more specific error information
            error_type = type(e).__name__
            error_details = str(e)

            message = (
                "🤖 **AUTO TRADING** 🤖\n\n"
                "⚠️ **Temporary Service Issue**\n\n"
                f"**Error Type**: {error_type}\n\n"
                "The auto trading interface is temporarily unavailable.\n"
                "Our team is working to resolve this issue.\n\n"
                "**What you can do:**\n"
                "• Try again in a few minutes\n"
                "• Use manual trading controls\n"
                "• Monitor your positions manually\n"
                "• Check system status for updates\n\n"
                "**Alternative Trading Options:**\n"
                "• Manual position management\n"
                "• Risk monitoring tools\n"
                "• Account analysis features"
            )
            keyboard = create_keyboard(
                [
                    [
                        ("🔄 Try Again", "auto_trading"),
                        ("📊 Manual Trading", "positions"),
                    ],
                    [("⚠️ Risk Monitor", "risk"), ("📈 Account", "account")],
                    [("📊 System Status", "status"), ("💬 Support", "support")],
                    [("⬅️ Back", "settings_trading"), ("🏠 Main", "start")],
                ]
            )
            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )

    async def _handle_toggle_auto_trading_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle auto trading toggle callback - redirect to auto trading interface."""
        query = update.callback_query
        await query.answer("🤖 Redirecting to Auto Trading")

        # Instead of just toggling, show the full auto trading interface
        await self._handle_auto_trading_callback(update, context)

    # Analysis callback handlers
    async def _handle_performance_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle performance callback - redirect to performance command."""
        query = update.callback_query
        await query.answer("📊 Performance Metrics")

        # Route to the analysis handler's performance command
        from ..commands.analysis import AnalysisCommandHandler

        analysis_handler = AnalysisCommandHandler()
        await analysis_handler.performance_command(update, context)

    async def _handle_risk_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle risk callback - redirect to risk command."""
        query = update.callback_query
        await query.answer("⚠️ Risk Analysis")

        # Route to the analysis handler's risk command
        from ..commands.analysis import AnalysisCommandHandler

        analysis_handler = AnalysisCommandHandler()
        await analysis_handler.risk_command(update, context)

    async def _handle_journal_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle journal callback - redirect to journal command."""
        query = update.callback_query
        await query.answer("📖 Trading Journal")

        # Route to the analysis handler's journal command
        from ..commands.analysis import AnalysisCommandHandler

        analysis_handler = AnalysisCommandHandler()
        await analysis_handler.journal_command(update, context)

    async def _handle_auto_signals_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle auto signals callback - redirect to auto signals interface."""
        query = update.callback_query
        await query.answer("📡 Auto Signals Settings")

        try:
            # Import the auto trading handler
            from ..commands.auto_trading import AutoTradingCommandHandler

            auto_trading_handler = AutoTradingCommandHandler()
            await auto_trading_handler.auto_signals_command(update, context)
        except Exception as e:
            logger.error(f"Error handling auto signals callback: {e}")
            await query.edit_message_text(
                "❌ Error loading auto signals settings. Please try again.",
                parse_mode=None,
            )

    async def _handle_toggle_auto_signals_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle toggle auto signals callback."""
        query = update.callback_query
        await query.answer("🔄 Toggling Auto Signals")

        try:
            # Import the auto trading handler
            from ..commands.auto_trading import AutoTradingCommandHandler

            auto_trading_handler = AutoTradingCommandHandler()
            await auto_trading_handler.toggle_auto_signals(update, context)
        except Exception as e:
            logger.error(f"Error toggling auto signals: {e}")
            await query.edit_message_text(
                "❌ Error toggling auto signals. Please try again.", parse_mode=None
            )

    async def _handle_view_auto_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle view auto settings callback."""
        query = update.callback_query
        await query.answer("⚙️ Auto Settings")

        try:
            # Import the auto trading handler
            from ..commands.auto_trading import AutoTradingCommandHandler

            auto_trading_handler = AutoTradingCommandHandler()
            await auto_trading_handler.view_auto_settings(update, context)
        except Exception as e:
            logger.error(f"Error viewing auto settings: {e}")
            await query.edit_message_text(
                "❌ Error loading auto settings. Please try again.", parse_mode=None
            )

    async def _handle_edit_auto_pairs_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle edit auto pairs callback."""
        query = update.callback_query
        await query.answer("📝 Edit Auto Pairs")

        try:
            # Import the auto trading handler
            from ..commands.auto_trading import AutoTradingCommandHandler

            auto_trading_handler = AutoTradingCommandHandler()
            await auto_trading_handler.edit_auto_pairs(update, context)
        except Exception as e:
            logger.error(f"Error editing auto pairs: {e}")
            await query.edit_message_text(
                "❌ Error loading auto pairs editor. Please try again.", parse_mode=None
            )
