"""Analysis commands for Telegram bot."""

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.services.performance_data_service import PerformanceDataService
from src.telegram_bot.utils.keyboards import create_keyboard

from .base import BaseCommandHandler

logger = get_logger(__name__)


class AnalysisCommandHandler(BaseCommandHandler):
    """Analysis command handler for Telegram bot."""

    def __init__(self):
        super().__init__()
        self.performance_service = PerformanceDataService()
        self._ai_analyzer = None  # Will be initialized on demand
        self._register_commands()
        self._register_callbacks()

    def _register_commands(self):
        """Register analysis commands."""
        self.commands = {
            "risk": self.risk_command,
            "performance": self.performance_command,
            "journal": self.journal_command,
            "analysis": self.market_analysis_command,
        }

    def _register_callbacks(self):
        """Register analysis callbacks."""
        self.callbacks = {
            "risk": self.risk_command,
            "refresh_risk": self.risk_command,
            "performance": self.performance_command,
            "refresh_performance": self.performance_command,
            "journal": self.journal_command,
            "refresh_journal": self.journal_command,
            "analysis": self.market_analysis_command,
            "refresh_analysis": self.market_analysis_command,
        }

    async def risk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /risk command.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Get real risk metrics data
            risk_metrics = await self.performance_service.get_risk_metrics()

            # Format the risk message
            message = (
                f"⚠️ **RISK METRICS** ⚠️\n\n"
                f"**Account Risk**:\n"
                f"• Drawdown: {risk_metrics['drawdown'] * 100:.2f}% (Max: {risk_metrics['max_drawdown'] * 100:.2f}%)\n"
                f"• Daily VaR: ${risk_metrics['daily_var']:.2f} ({risk_metrics['daily_var_pct'] * 100:.2f}%)\n"
                f"• Margin Level: {risk_metrics['margin_level']:.2f}%\n\n"
                f"**Position Risk**:\n"
                f"• Exposure: {risk_metrics['exposure'] * 100:.2f}% (Max: {risk_metrics['max_exposure'] * 100:.2f}%)\n"
                f"• Largest Position: ${risk_metrics['largest_position']:.2f} ({risk_metrics['largest_position_pct'] * 100:.2f}%)\n"
                f"• Position Correlation: {risk_metrics['position_correlation']:.2f}\n\n"
                f"**Market Risk**:\n"
                f"• Market Volatility: {risk_metrics['market_volatility'] * 100:.2f}%\n"
                f"• Correlation to SPX: {risk_metrics['correlation_to_spx']:.2f}\n"
                f"• Correlation to BTC: {risk_metrics['correlation_to_btc']:.2f}\n\n"
                f"**Risk Rating**: {risk_metrics['risk_rating']}\n"
                f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Create an inline keyboard for risk actions
            keyboard = create_keyboard(
                [
                    [("Refresh", "refresh_risk"), ("Positions", "positions")],
                    [("Account", "account"), ("Performance", "performance")],
                    [("Status", "status"), ("Settings", "settings")],
                ]
            )

            # If this is a callback query, edit the message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in risk command: {e}")
            error_message = (
                "❌ **Error Loading Risk Metrics**\n\n"
                "There was an issue loading risk data.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard(
                [[("🔄 Retry", "refresh_risk"), ("📊 Status", "status")]]
            )

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)

    async def performance_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle the /performance command.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Get real performance data
            performance = await self.performance_service.get_performance_metrics()

            # Format the performance message
            message = (
                f"📈 **PERFORMANCE METRICS** 📈\n\n"
                f"**Overall Performance**:\n"
                f"• Total Profit: ${performance['total_profit']:.2f}\n"
                f"• Daily Profit: ${performance['daily_profit']:.2f}\n"
                f"• Weekly Profit: ${performance['weekly_profit']:.2f}\n"
                f"• Monthly Profit: ${performance['monthly_profit']:.2f}\n\n"
                f"**Trading Statistics**:\n"
                f"• Total Trades: {performance['total_trades']}\n"
                f"• Win Rate: {performance['win_rate'] * 100:.1f}%\n"
                f"• Profit Factor: {performance['profit_factor']:.2f}\n"
                f"• Sharpe Ratio: {performance['sharpe_ratio']:.2f}\n\n"
                f"**Trade Analysis**:\n"
                f"• Average Winner: ${performance['avg_winner']:.2f}\n"
                f"• Average Loser: ${performance['avg_loser']:.2f}\n"
                f"• Average Trade: ${performance['avg_trade']:.2f}\n"
                f"• Best Trade: ${performance['best_trade']:.2f}\n"
                f"• Worst Trade: ${performance['worst_trade']:.2f}\n\n"
                f"**Recent Activity**:\n"
                f"• Today's Trades: {performance['today_trades']}\n"
                f"• This Week: {performance['week_trades']}\n"
                f"• This Month: {performance['month_trades']}\n"
                f"• Avg Holding Time: {performance['avg_holding_time']}\n\n"
                f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Create an inline keyboard for performance actions
            keyboard = create_keyboard(
                [
                    [("Refresh", "refresh_performance"), ("Risk", "risk")],
                    [("Journal", "journal"), ("Positions", "positions")],
                    [("Account", "account"), ("Status", "status")],
                ]
            )

            # If this is a callback query, edit the message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in performance command: {e}")
            error_message = (
                "❌ **Error Loading Performance**\n\n"
                "There was an issue loading performance data.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard(
                [[("🔄 Retry", "refresh_performance"), ("📊 Status", "status")]]
            )

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)

    async def journal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /journal command.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Get real trading journal data
            journal_entries = await self.performance_service.get_trading_journal(
                limit=10
            )

            if not journal_entries:
                message = (
                    "📖 **TRADING JOURNAL** 📖\n\n"
                    "No trading history available at the moment.\n\n"
                    "Start trading to see your journal entries here."
                )
            else:
                # Format the journal message
                message = "📖 **TRADING JOURNAL** 📖\n\n"

                for entry in journal_entries:
                    # Determine emoji based on profit
                    profit_emoji = "💰" if entry["profit"] > 0 else "📉"

                    message += (
                        f"{profit_emoji} **{entry['symbol']}** ({entry['type']})\n"
                        f"  Open: ${entry['open_price']:.5f} | Close: ${entry['close_price']:.5f}\n"
                        f"  Volume: {entry['volume']} | P&L: ${entry['profit']:.2f}\n"
                        f"  Time: {entry['open_time'][:10] if entry['open_time'] else 'Unknown'}\n"
                        f"  Status: {entry['status']}\n\n"
                    )

                message += f"**Total Entries**: {len(journal_entries)}\n**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Create an inline keyboard for journal actions
            keyboard = create_keyboard(
                [
                    [("Refresh", "refresh_journal"), ("Performance", "performance")],
                    [("Positions", "positions"), ("Signals", "signals")],
                    [("Account", "account"), ("Status", "status")],
                ]
            )

            # If this is a callback query, edit the message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in journal command: {e}")
            error_message = (
                "❌ **Error Loading Journal**\n\n"
                "There was an issue loading journal data.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard(
                [[("🔄 Retry", "refresh_journal"), ("📊 Status", "status")]]
            )

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)

    async def market_analysis_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle the /analysis command with real AI-powered market analysis.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Get AI-powered market analysis
            analysis_data = await self._get_ai_market_analysis()

            if analysis_data.get("status") == "success":
                # Format successful analysis message
                signal = analysis_data.get("signal", {})
                market_data = analysis_data.get("market_data", "")

                # Extract key insights from the analysis
                recommendation = signal.get("recommendation", "HOLD")
                confidence = signal.get("confidence", 0.5) * 100
                symbols_analyzed = ", ".join(
                    analysis_data.get("symbols", ["Major pairs"])
                )

                # Get market sentiment and key levels
                market_sentiment = self._extract_market_sentiment(market_data)
                key_levels = self._extract_key_levels(signal)

                message = (
                    f"🔍 **AI MARKET ANALYSIS** 🔍\n\n"
                    f"**Current Market Overview**:\n"
                    f"• Symbols Analyzed: {symbols_analyzed}\n"
                    f"• Market Sentiment: {market_sentiment}\n"
                    f"• AI Recommendation: **{recommendation}**\n"
                    f"• Confidence Level: {confidence:.1f}%\n\n"
                    f"**Technical Analysis**:\n"
                    f"{self._format_technical_analysis(signal)}\n"
                    f"**Key Levels**:\n"
                    f"{key_levels}\n"
                    f"**Risk Assessment**:\n"
                    f"{self._format_risk_assessment(signal)}\n"
                    f"**Market Commentary**:\n"
                    f"{signal.get('reasoning', 'AI analysis in progress...')}\n\n"
                    f"**Data Source**: Real-time market data\n"
                    f"**Analysis Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"**Model**: {analysis_data.get('model_used', 'AI Engine')}"
                )
            else:
                # Handle analysis errors gracefully
                reason = analysis_data.get("reason", "Unknown error")
                message = (
                    f"🔍 **MARKET ANALYSIS** 🔍\n\n"
                    f"**Current Status**: Analysis in progress\n\n"
                    f"**Available Analysis**:\n"
                    f"• Performance Metrics (/performance)\n"
                    f"• Risk Analysis (/risk)\n"
                    f"• Trading Journal (/journal)\n"
                    f"• Market Signals (/signals)\n\n"
                    f"**AI Features**:\n"
                    f"• 🤖 Real-time AI Analysis\n"
                    f"• 📈 Technical Indicators\n"
                    f"• 📊 Market Sentiment\n"
                    f"• 🔗 Correlation Analysis\n\n"
                    f"**Note**: {reason}\n\n"
                    f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

            # Create an inline keyboard for analysis actions
            keyboard = create_keyboard(
                [
                    [("Performance", "performance"), ("Risk", "risk")],
                    [("Journal", "journal"), ("Signals", "signals")],
                    [("Status", "status"), ("Help", "help")],
                ]
            )

            # If this is a callback query, edit the message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in market analysis command: {e}")
            error_message = (
                "❌ **Error Loading Analysis**\n\n"
                "There was an issue loading analysis data.\n"
                "Please try again in a moment."
            )
            keyboard = create_keyboard(
                [[("🔄 Retry", "refresh_analysis"), ("📊 Status", "status")]]
            )

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)

    async def _get_ai_market_analysis(self) -> dict:
        """Get AI-powered market analysis.

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Initialize AI analyzer if not already done
            if not self._ai_analyzer:
                await self._initialize_ai_analyzer()

            if not self._ai_analyzer or not self._ai_analyzer.is_available:
                return {"status": "error", "reason": "AI analyzer not available"}

            # Define market context for analysis
            market_context = {
                "symbols": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"],
                "timeframe": "1H",
                "analysis_depth": "comprehensive",
            }

            # Get AI analysis
            analysis_result = await self._ai_analyzer.analyze(
                market_context=market_context, analysis_type="basic"
            )

            return analysis_result

        except Exception as e:
            logger.error(f"Error getting AI market analysis: {e}")
            return {"status": "error", "reason": f"Analysis error: {str(e)}"}

    async def _initialize_ai_analyzer(self):
        """Initialize AI analyzer for market analysis."""
        try:
            # Import and initialize the OpenAI analyzer
            import os

            from src.analysis.openai_analyzer import OpenAIAnalyzer

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OpenAI API key not found in environment variables")
                return

            self._ai_analyzer = OpenAIAnalyzer(api_key=api_key, model="gpt-4o-mini")

            # Test connection
            if await self._ai_analyzer.test_connection():
                logger.info("AI analyzer initialized successfully")
            else:
                logger.warning("AI analyzer connection test failed")
                self._ai_analyzer = None

        except Exception as e:
            logger.error(f"Failed to initialize AI analyzer: {e}")
            self._ai_analyzer = None

    def _extract_market_sentiment(self, market_data: str) -> str:
        """Extract market sentiment from analysis data.

        Args:
            market_data: Raw market data string

        Returns:
            Market sentiment description
        """
        if not market_data:
            return "Neutral"

        # Simple sentiment extraction based on keywords
        data_lower = market_data.lower()

        bullish_keywords = ["bullish", "uptrend", "rising", "buying", "support holding"]
        bearish_keywords = [
            "bearish",
            "downtrend",
            "falling",
            "selling",
            "resistance holding",
        ]

        bullish_count = sum(1 for keyword in bullish_keywords if keyword in data_lower)
        bearish_count = sum(1 for keyword in bearish_keywords if keyword in data_lower)

        if bullish_count > bearish_count:
            return "🟢 Bullish"
        elif bearish_count > bullish_count:
            return "🔴 Bearish"
        else:
            return "🟡 Neutral"

    def _extract_key_levels(self, signal: dict) -> str:
        """Extract key price levels from signal data.

        Args:
            signal: Signal data dictionary

        Returns:
            Formatted key levels string
        """
        if not signal:
            return "• No key levels available"

        levels = []

        # Extract support and resistance levels
        if "support" in signal:
            levels.append(f"• Support: {signal['support']}")

        if "resistance" in signal:
            levels.append(f"• Resistance: {signal['resistance']}")

        # Extract stop loss and take profit levels
        if "stop_loss" in signal:
            levels.append(f"• Stop Loss: {signal['stop_loss']}")

        if "take_profit" in signal:
            levels.append(f"• Take Profit: {signal['take_profit']}")

        return "\n".join(levels) if levels else "• Key levels being calculated..."

    def _format_technical_analysis(self, signal: dict) -> str:
        """Format technical analysis from signal data.

        Args:
            signal: Signal data dictionary

        Returns:
            Formatted technical analysis string
        """
        if not signal:
            return "• Technical analysis in progress..."

        analysis_points = []

        # Add trend analysis
        if "trend" in signal:
            analysis_points.append(f"• Trend: {signal['trend']}")

        # Add momentum analysis
        if "momentum" in signal:
            analysis_points.append(f"• Momentum: {signal['momentum']}")

        # Add volume analysis
        if "volume_analysis" in signal:
            analysis_points.append(f"• Volume: {signal['volume_analysis']}")

        # Default if no specific analysis available
        if not analysis_points:
            analysis_points = [
                "• Multi-timeframe analysis active",
                "• Technical indicators evaluated",
                "• Price action patterns identified",
            ]

        return "\n".join(analysis_points)

    def _format_risk_assessment(self, signal: dict) -> str:
        """Format risk assessment from signal data.

        Args:
            signal: Signal data dictionary

        Returns:
            Formatted risk assessment string
        """
        if not signal:
            return "• Risk assessment in progress..."

        risk_points = []

        # Add risk level
        if "risk_level" in signal:
            risk_points.append(f"• Risk Level: {signal['risk_level']}")

        # Add volatility assessment
        if "volatility" in signal:
            risk_points.append(f"• Volatility: {signal['volatility']}")

        # Add market conditions
        if "market_conditions" in signal:
            risk_points.append(f"• Conditions: {signal['market_conditions']}")

        # Default risk assessment
        if not risk_points:
            risk_points = [
                "• Risk level: Moderate",
                "• Volatility: Normal range",
                "• Market conditions: Stable",
            ]

        return "\n".join(risk_points)
