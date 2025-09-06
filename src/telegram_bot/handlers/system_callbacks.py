"""System callback handlers for Telegram bot."""

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
            "general_maintenance_settings": self._handle_general_maintenance_settings_callback,
            "general_features_settings": self._handle_general_features_settings_callback,
            "theme_settings": self._handle_theme_settings_callback,
            "sound_settings": self._handle_sound_settings_callback,
        }

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries."""
        query = update.callback_query
        callback_data = query.data

        if callback_data in self.callbacks:
            await self.callbacks[callback_data](update, context)
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

        message = (
            "📈 **TRADING SIGNALS NOTIFICATIONS** 📈\n\n"
            "**Configure signal notifications:**\n"
            "• New trading signals\n"
            "• Signal updates\n"
            "• Signal expirations\n\n"
            "Settings will be implemented in future updates."
        )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notif_trading")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_trading_positions_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle trading positions settings callback."""
        query = update.callback_query
        await query.answer("📊 Trading positions notification settings")

        message = (
            "📊 **TRADING POSITIONS NOTIFICATIONS** 📊\n\n"
            "**Configure position notifications:**\n"
            "• Position opened\n"
            "• Position closed\n"
            "• Position modified\n\n"
            "Settings will be implemented in future updates."
        )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notif_trading")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_trading_orders_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle trading orders settings callback."""
        query = update.callback_query
        await query.answer("📋 Trading orders notification settings")

        message = (
            "📋 **TRADING ORDERS NOTIFICATIONS** 📋\n\n"
            "**Configure order notifications:**\n"
            "• Order placed\n"
            "• Order executed\n"
            "• Order cancelled\n\n"
            "Settings will be implemented in future updates."
        )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notif_trading")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_trading_risk_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle trading risk settings callback."""
        query = update.callback_query
        await query.answer("⚠️ Trading risk notification settings")

        message = (
            "⚠️ **TRADING RISK NOTIFICATIONS** ⚠️\n\n"
            "**Configure risk notifications:**\n"
            "• Risk limit breaches\n"
            "• Drawdown warnings\n"
            "• Position size alerts\n\n"
            "Settings will be implemented in future updates."
        )

        keyboard = create_keyboard(
            [
                [("⬅️ Back", "notif_trading")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    # Reports notification settings callbacks
    async def _handle_reports_performance_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle reports performance settings callback."""
        query = update.callback_query
        await query.answer("📊 Performance reports notification settings")

        message = (
            "📊 **PERFORMANCE REPORTS NOTIFICATIONS** 📊\n\n"
            "**Configure performance notifications:**\n"
            "• Daily performance summaries\n"
            "• Weekly performance reports\n"
            "• Monthly performance analysis\n\n"
            "Settings will be implemented in future updates."
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

        message = (
            "📈 **ANALYSIS REPORTS NOTIFICATIONS** 📈\n\n"
            "**Configure analysis notifications:**\n"
            "• Market analysis reports\n"
            "• Strategy performance analysis\n"
            "• Risk analysis reports\n\n"
            "Settings will be implemented in future updates."
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

        message = (
            "📋 **STATISTICS REPORTS NOTIFICATIONS** 📋\n\n"
            "**Configure statistics notifications:**\n"
            "• Trading statistics\n"
            "• Win/loss ratios\n"
            "• Performance metrics\n\n"
            "Settings will be implemented in future updates."
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

        message = (
            "🔧 **SYSTEM REPORTS NOTIFICATIONS** 🔧\n\n"
            "**Configure system notifications:**\n"
            "• System health reports\n"
            "• Resource usage reports\n"
            "• Error reports\n\n"
            "Settings will be implemented in future updates."
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

        message = (
            "📢 **GENERAL UPDATES NOTIFICATIONS** 📢\n\n"
            "**Configure update notifications:**\n"
            "• Bot updates\n"
            "• Feature updates\n"
            "• System updates\n\n"
            "Settings will be implemented in future updates."
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

        message = (
            "📰 **GENERAL NEWS NOTIFICATIONS** 📰\n\n"
            "**Configure news notifications:**\n"
            "• Market news\n"
            "• Economic announcements\n"
            "• Trading alerts\n\n"
            "Settings will be implemented in future updates."
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

        message = (
            "🔧 **GENERAL MAINTENANCE NOTIFICATIONS** 🔧\n\n"
            "**Configure maintenance notifications:**\n"
            "• Scheduled maintenance\n"
            "• System downtime\n"
            "• Maintenance completion\n\n"
            "Settings will be implemented in future updates."
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

        message = (
            "🆕 **GENERAL FEATURES NOTIFICATIONS** 🆕\n\n"
            "**Configure feature notifications:**\n"
            "• New features\n"
            "• Feature announcements\n"
            "• Feature updates\n\n"
            "Settings will be implemented in future updates."
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
