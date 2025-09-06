"""Comprehensive test for Telegram bot functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import CallbackQuery, Chat, Message, Update, User
from telegram.ext import ContextTypes

from src.telegram_bot.commands.admin_global_settings import AdminGlobalSettingsHandler
from src.telegram_bot.commands.system import SystemCommandHandler
from src.telegram_bot.handlers.callback_handler import CallbackRouter
from src.telegram_bot.handlers.user_commands import UserCommandHandlers


class TestTelegramBotComplete:
    """Test complete Telegram bot functionality."""

    @pytest.fixture
    def mock_update(self):
        """Create a mock update object."""
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345
        update.effective_user.first_name = "Test"
        update.effective_user.last_name = "User"
        update.effective_user.username = "testuser"

        update.callback_query = MagicMock(spec=CallbackQuery)
        update.callback_query.data = "test_callback"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()

        update.message = MagicMock(spec=Message)
        update.message.reply_text = AsyncMock()
        update.message.text = "test message"

        return update

    @pytest.fixture
    def mock_context(self):
        """Create a mock context object."""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        context.user_data = {}
        return context

    @pytest.fixture
    def system_handler(self):
        """Create system command handler."""
        with patch("src.telegram_bot.commands.system.UserConfigService"):
            return SystemCommandHandler()

    @pytest.fixture
    def admin_global_handler(self):
        """Create admin global settings handler."""
        with patch("src.telegram_bot.commands.admin_global_settings.UserConfigService"):
            return AdminGlobalSettingsHandler()

    @pytest.fixture
    def callback_router(self):
        """Create callback router."""
        return CallbackRouter()

    @pytest.fixture
    def user_handlers(self):
        """Create user command handlers."""
        with patch("src.telegram_bot.handlers.user_commands.UserManager"), patch(
            "src.telegram_bot.handlers.user_commands.ConfigManager"
        ), patch("src.telegram_bot.handlers.user_commands.EABridge"), patch(
            "src.telegram_bot.handlers.user_commands.SignalDistributor"
        ):
            return UserCommandHandlers()

    @pytest.mark.asyncio
    async def test_system_settings_menu(
        self, system_handler, mock_update, mock_context
    ):
        """Test system settings menu functionality."""
        # Mock user config service
        with patch.object(
            system_handler.user_config_service, "get_user_config"
        ) as mock_get_config:
            mock_get_config.return_value = {
                "trading": {
                    "auto_trading": False,
                    "risk_per_trade_pct": 2.0,
                    "max_open_positions": 5,
                    "allowed_symbols": ["EURUSD", "GBPUSD"],
                },
                "notifications": {
                    "signals": True,
                    "positions": True,
                    "orders": True,
                    "risk": True,
                    "performance": True,
                    "system": True,
                },
            }

            # Test settings command
            await system_handler.settings_command(mock_update, mock_context)

            # Verify the message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]

            # Check that the message contains expected content
            assert "USER SETTINGS" in message_text
            assert "Auto Trading" in message_text
            assert "Risk per Trade" in message_text
            assert "Max Positions" in message_text
            assert "Active Notifications" in message_text

    @pytest.mark.asyncio
    async def test_notification_settings(
        self, system_handler, mock_update, mock_context
    ):
        """Test notification settings functionality."""
        with patch.object(
            system_handler.user_config_service, "get_user_config"
        ) as mock_get_config:
            mock_get_config.return_value = {
                "notifications": {
                    "signals": True,
                    "positions": True,
                    "orders": False,
                    "risk": True,
                    "performance": False,
                    "system": True,
                }
            }

            # Test notification settings
            await system_handler.settings_notifications(mock_update, mock_context)

            # Verify the message was edited
            mock_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_update.callback_query.edit_message_text.call_args
            message_text = call_args[0][0]

            # Check that the message contains expected content
            assert "NOTIFICATION SETTINGS" in message_text
            assert "Trading Signals" in message_text
            assert "Position Updates" in message_text
            assert "Order Updates" in message_text

    @pytest.mark.asyncio
    async def test_trading_pairs_settings(
        self, system_handler, mock_update, mock_context
    ):
        """Test trading pairs settings functionality."""
        with patch.object(
            system_handler.user_config_service, "get_user_config"
        ) as mock_get_config:
            mock_get_config.return_value = {
                "trading": {"allowed_symbols": ["EURUSD", "GBPUSD", "USDJPY"]}
            }

            # Test trading pairs callback
            await system_handler.trading_pairs_callback(mock_update, mock_context)

            # Verify the message was edited
            mock_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_update.callback_query.edit_message_text.call_args
            message_text = call_args[0][0]

            # Check that the message contains expected content
            assert "TRADING PAIRS SETTINGS" in message_text
            assert "EURUSD" in message_text
            assert "GBPUSD" in message_text
            assert "USDJPY" in message_text
            assert "Total: 3 pairs" in message_text

    @pytest.mark.asyncio
    async def test_notification_intervals(
        self, system_handler, mock_update, mock_context
    ):
        """Test notification intervals functionality."""
        with patch.object(
            system_handler.user_config_service, "get_user_config"
        ) as mock_get_config:
            mock_get_config.return_value = {
                "notification_intervals": {
                    "signals_minutes": 5,
                    "positions_minutes": 1,
                    "risk_minutes": 15,
                    "performance_hours": 4,
                    "system_minutes": 30,
                }
            }

            # Test notification intervals callback
            await system_handler.notification_intervals_callback(
                mock_update, mock_context
            )

            # Verify the message was edited
            mock_update.callback_query.edit_message_text.assert_called_once()
            call_args = mock_update.callback_query.edit_message_text.call_args
            message_text = call_args[0][0]

            # Check that the message contains expected content
            assert "NOTIFICATION INTERVALS" in message_text
            assert "Signals: 5 minutes" in message_text
            assert "Positions: 1 minutes" in message_text
            assert "Risk: 15 minutes" in message_text
            assert "Performance: 4 hours" in message_text
            assert "System: 30 minutes" in message_text
            assert "Token Saving" in message_text

    @pytest.mark.asyncio
    async def test_admin_global_settings(
        self, admin_global_handler, mock_update, mock_context
    ):
        """Test admin global settings functionality."""
        # Mock admin check
        with patch.object(admin_global_handler, "_is_admin", return_value=True):
            # Test admin global command
            await admin_global_handler.admin_global_command(mock_update, mock_context)

            # Verify the message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]

            # Check that the message contains expected content
            assert "ADMIN GLOBAL SETTINGS" in message_text
            assert "Global Trading Pairs" in message_text
            assert "Global Notification Intervals" in message_text
            assert "System Configuration" in message_text

    @pytest.mark.asyncio
    async def test_admin_global_pairs(
        self, admin_global_handler, mock_update, mock_context
    ):
        """Test admin global trading pairs functionality."""
        with patch.object(
            admin_global_handler, "_is_admin", return_value=True
        ), patch.object(
            admin_global_handler,
            "_get_global_trading_pairs",
            return_value=["EURUSD", "GBPUSD", "USDJPY"],
        ):

            # Test global pairs command
            await admin_global_handler.global_pairs_command(mock_update, mock_context)

            # Verify the message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]

            # Check that the message contains expected content
            assert "GLOBAL TRADING PAIRS" in message_text
            assert "EURUSD" in message_text
            assert "GBPUSD" in message_text
            assert "USDJPY" in message_text
            assert "Total: 3 pairs" in message_text

    @pytest.mark.asyncio
    async def test_admin_global_intervals(
        self, admin_global_handler, mock_update, mock_context
    ):
        """Test admin global notification intervals functionality."""
        with patch.object(
            admin_global_handler, "_is_admin", return_value=True
        ), patch.object(
            admin_global_handler,
            "_get_global_notification_intervals",
            return_value={
                "signals_minutes": 5,
                "positions_minutes": 1,
                "risk_minutes": 15,
                "performance_hours": 4,
                "system_minutes": 30,
            },
        ):

            # Test global intervals command
            await admin_global_handler.global_intervals_command(
                mock_update, mock_context
            )

            # Verify the message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]

            # Check that the message contains expected content
            assert "GLOBAL NOTIFICATION INTERVALS" in message_text
            assert "Signals: 5 minutes" in message_text
            assert "Positions: 1 minutes" in message_text
            assert "Risk: 15 minutes" in message_text
            assert "Performance: 4 hours" in message_text
            assert "System: 30 minutes" in message_text

    @pytest.mark.asyncio
    async def test_callback_routing(self, callback_router, mock_update, mock_context):
        """Test callback routing functionality."""
        # Test system callback routing
        mock_update.callback_query.data = "status"
        await callback_router.route_callback(mock_update, mock_context)

        # Test admin callback routing
        mock_update.callback_query.data = "global_pairs"
        await callback_router.route_callback(mock_update, mock_context)

        # Test user callback routing
        mock_update.callback_query.data = "set_risk:2.0"
        await callback_router.route_callback(mock_update, mock_context)

        # Test unknown callback
        mock_update.callback_query.data = "unknown_callback"
        await callback_router.route_callback(mock_update, mock_context)

        # Verify unknown callback was handled
        mock_update.callback_query.edit_message_text.assert_called()
        call_args = mock_update.callback_query.edit_message_text.call_args
        message_text = call_args[0][0]
        assert "Unknown Command" in message_text

    @pytest.mark.asyncio
    async def test_user_callback_handlers(
        self, user_handlers, mock_update, mock_context
    ):
        """Test user callback handlers functionality."""
        # Test risk setting callback
        mock_update.callback_query.data = "set_risk:2.5"
        with patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Risk per trade set to 2.5%"
            )

        # Test max positions callback
        mock_update.callback_query.data = "set_max_pos:10"
        with patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Max positions set to 10"
            )

        # Test add pair callback
        mock_update.callback_query.data = "add_pair:EURUSD"
        with patch.object(
            user_handlers.config_manager,
            "get_user_config",
            return_value={"allowed_symbols": []},
        ), patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Added EURUSD to trading pairs"
            )

        # Test remove pair callback
        mock_update.callback_query.data = "remove_pair:GBPUSD"
        with patch.object(
            user_handlers.config_manager,
            "get_user_config",
            return_value={"allowed_symbols": ["GBPUSD"]},
        ), patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Removed GBPUSD from trading pairs"
            )

    @pytest.mark.asyncio
    async def test_interval_setting_callbacks(
        self, user_handlers, mock_update, mock_context
    ):
        """Test notification interval setting callbacks."""
        # Test signal interval callback
        mock_update.callback_query.data = "update_interval:signals:5"
        with patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Signals interval set to 5 minutes"
            )

        # Test performance interval callback
        mock_update.callback_query.data = "update_interval:performance:4"
        with patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Performance interval set to 4 hours"
            )

    @pytest.mark.asyncio
    async def test_risk_settings_callbacks(
        self, user_handlers, mock_update, mock_context
    ):
        """Test risk settings callbacks."""
        # Test drawdown callback
        mock_update.callback_query.data = "set_drawdown:15"
        with patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Max drawdown set to 15%"
            )

        # Test daily loss percentage callback
        mock_update.callback_query.data = "set_daily_loss_pct:5"
        with patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Daily loss % set to 5%"
            )

        # Test position size callback
        mock_update.callback_query.data = "set_position_size:10"
        with patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Position size set to 10%"
            )

    @pytest.mark.asyncio
    async def test_system_settings_callbacks(
        self, user_handlers, mock_update, mock_context
    ):
        """Test system settings callbacks."""
        # Test timezone callback
        mock_update.callback_query.data = "set_timezone:UTC"
        with patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Timezone set to UTC"
            )

        # Test update frequency callback
        mock_update.callback_query.data = "set_update_freq:60"
        with patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Update frequency set to 60s"
            )

        # Test log level callback
        mock_update.callback_query.data = "set_log_level:INFO"
        with patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Log level set to INFO"
            )

        # Test timeframe callback
        mock_update.callback_query.data = "set_timeframe:H1"
        with patch.object(
            user_handlers.config_manager, "update_user_config", return_value=True
        ):
            await user_handlers.handle_user_callback(mock_update, mock_context)
            mock_update.callback_query.answer.assert_called_with(
                "✅ Timeframe set to H1"
            )

    def test_callback_key_coverage(self, callback_router):
        """Test that all callback keys are properly registered."""
        # Check system callback keys
        assert "settings" in callback_router.system_callback_keys
        assert "settings_notifications" in callback_router.system_callback_keys
        assert "settings_trading" in callback_router.system_callback_keys
        assert "settings_risk" in callback_router.system_callback_keys
        assert "settings_system" in callback_router.system_callback_keys
        assert "notification_intervals" in callback_router.system_callback_keys
        assert "trading_pairs" in callback_router.system_callback_keys

        # Check admin callback keys
        assert "admin_global" in callback_router.admin_callback_keys
        assert "global_pairs" in callback_router.admin_callback_keys
        assert "global_intervals" in callback_router.admin_callback_keys
        assert "add_global_pair" in callback_router.admin_callback_keys
        assert "remove_global_pair" in callback_router.admin_callback_keys

        # Check user callback keys
        assert "manage_symbols" in callback_router.user_callback_keys
        assert "edit_risk_percent" in callback_router.user_callback_keys
        assert "edit_max_positions" in callback_router.user_callback_keys
        assert "edit_daily_loss" in callback_router.user_callback_keys
        assert "set_risk" in callback_router.user_callback_keys
        assert "set_max_pos" in callback_router.user_callback_keys
        assert "set_daily_loss" in callback_router.user_callback_keys
        assert "update_interval" in callback_router.user_callback_keys
        assert "add_pair" in callback_router.user_callback_keys
        assert "remove_pair" in callback_router.user_callback_keys

    def test_keyboard_creation(self, system_handler):
        """Test keyboard creation functionality."""
        from src.telegram_bot.utils.keyboards import create_keyboard

        # Test basic keyboard creation
        buttons = [
            [("Button 1", "callback1"), ("Button 2", "callback2")],
            [("Button 3", "callback3")],
        ]

        keyboard = create_keyboard(buttons)
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 2
        assert len(keyboard.inline_keyboard[0]) == 2
        assert len(keyboard.inline_keyboard[1]) == 1

    @pytest.mark.asyncio
    async def test_error_handling(self, system_handler, mock_update, mock_context):
        """Test error handling in system commands."""
        # Test error in settings command
        with patch.object(
            system_handler.user_config_service,
            "get_user_config",
            side_effect=Exception("Database error"),
        ):
            await system_handler.settings_command(mock_update, mock_context)

            # Verify error message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]
            assert "Error Loading Settings" in message_text

    @pytest.mark.asyncio
    async def test_admin_access_control(
        self, admin_global_handler, mock_update, mock_context
    ):
        """Test admin access control."""
        # Test non-admin access
        with patch.object(admin_global_handler, "_is_admin", return_value=False):
            await admin_global_handler.admin_global_command(mock_update, mock_context)

            # Verify access denied message
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            message_text = call_args[0][0]
            assert "Access Denied" in message_text

    def test_comprehensive_feature_coverage(self):
        """Test that all required features are implemented."""
        # Test that all required callback handlers exist
        system_handler = SystemCommandHandler()
        assert hasattr(system_handler, "settings_notifications")
        assert hasattr(system_handler, "settings_trading")
        assert hasattr(system_handler, "settings_risk")
        assert hasattr(system_handler, "settings_system")
        assert hasattr(system_handler, "notification_intervals_callback")
        assert hasattr(system_handler, "trading_pairs_callback")
        assert hasattr(system_handler, "add_trading_pair_callback")
        assert hasattr(system_handler, "remove_trading_pair_callback")

        # Test that all required admin handlers exist
        admin_handler = AdminGlobalSettingsHandler()
        assert hasattr(admin_handler, "admin_global_command")
        assert hasattr(admin_handler, "global_pairs_command")
        assert hasattr(admin_handler, "global_intervals_command")
        assert hasattr(admin_handler, "add_global_pair_callback")
        assert hasattr(admin_handler, "remove_global_pair_callback")

        # Test that all required user handlers exist
        user_handlers = UserCommandHandlers()
        assert hasattr(user_handlers, "handle_user_callback")

        # Test callback router
        callback_router = CallbackRouter()
        assert hasattr(callback_router, "route_callback")
        assert hasattr(callback_router, "system_callback_keys")
        assert hasattr(callback_router, "admin_callback_keys")
        assert hasattr(callback_router, "user_callback_keys")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
