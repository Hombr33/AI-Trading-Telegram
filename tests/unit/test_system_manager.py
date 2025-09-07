"""
Unit tests for the system manager module.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.core.system_manager import SystemManager, system_manager


class TestSystemManager:
    """Test cases for SystemManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SystemManager()

    def test_initialization(self):
        """Test SystemManager initialization."""
        assert self.manager._shutdown_callbacks == []
        assert self.manager._restart_requested == False

    def test_add_shutdown_callback(self):
        """Test adding shutdown callbacks."""

        def dummy_callback():
            pass

        self.manager.add_shutdown_callback(dummy_callback)
        assert dummy_callback in self.manager._shutdown_callbacks

    def test_is_restart_requested(self):
        """Test restart requested flag."""
        assert self.manager.is_restart_requested() == False

        self.manager._restart_requested = True
        assert self.manager.is_restart_requested() == True

    def test_get_system_status(self):
        """Test system status retrieval."""
        status = self.manager.get_system_status()

        assert "restart_requested" in status
        assert "shutdown_callbacks_count" in status
        assert "process_id" in status
        assert "python_version" in status
        assert "platform" in status

        assert status["restart_requested"] == False
        assert status["shutdown_callbacks_count"] == 0

    @pytest.mark.asyncio
    async def test_execute_shutdown_callbacks(self):
        """Test execution of shutdown callbacks."""
        callback_executed = False

        def sync_callback():
            nonlocal callback_executed
            callback_executed = True

        async def async_callback():
            nonlocal callback_executed
            callback_executed = True

        # Test sync callback
        self.manager.add_shutdown_callback(sync_callback)
        await self.manager._execute_shutdown_callbacks()
        assert callback_executed == True

        # Reset and test async callback
        callback_executed = False
        self.manager._shutdown_callbacks = []
        self.manager.add_shutdown_callback(async_callback)
        await self.manager._execute_shutdown_callbacks()
        assert callback_executed == True

    @pytest.mark.asyncio
    async def test_save_system_state(self):
        """Test system state saving."""
        # Should not raise exception
        await self.manager._save_system_state()

    @pytest.mark.asyncio
    async def test_stop_background_tasks(self):
        """Test stopping background tasks."""
        # Should not raise exception even with no tasks
        await self.manager._stop_background_tasks()

    def test_create_restart_script(self):
        """Test restart script creation."""
        script_path = self.manager._create_restart_script()

        if script_path:
            import os

            assert os.path.exists(script_path)

            # Clean up
            try:
                os.remove(script_path)
            except:
                pass

    @pytest.mark.asyncio
    async def test_graceful_restart_without_bot(self):
        """Test graceful restart without telegram bot."""
        result = await self.manager.graceful_restart()

        # Should handle missing bot gracefully
        assert isinstance(result, dict)
        assert "success" in result

    @pytest.mark.asyncio
    async def test_graceful_restart_with_mock_bot(self):
        """Test graceful restart with mock telegram bot."""
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()

        result = await self.manager.graceful_restart(
            telegram_bot=mock_bot, admin_telegram_id=123456
        )

        assert isinstance(result, dict)
        assert "success" in result
        assert "message" in result

    @pytest.mark.asyncio
    async def test_force_close_connections(self):
        """Test force closing connections."""
        # Should not raise exception
        await self.manager._force_close_connections()

    def test_global_system_manager_instance(self):
        """Test global system manager instance."""
        assert system_manager is not None
        assert isinstance(system_manager, SystemManager)


class TestSystemManagerErrorHandling:
    """Test error handling in SystemManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SystemManager()

    @pytest.mark.asyncio
    async def test_execute_shutdown_callbacks_with_error(self):
        """Test shutdown callback execution with errors."""

        def failing_callback():
            raise Exception("Test error")

        def working_callback():
            pass

        self.manager.add_shutdown_callback(failing_callback)
        self.manager.add_shutdown_callback(working_callback)

        # Should not raise exception even if one callback fails
        await self.manager._execute_shutdown_callbacks()

    @pytest.mark.asyncio
    async def test_graceful_restart_error_handling(self):
        """Test graceful restart error handling."""
        # Mock a failing operation
        with patch.object(
            self.manager,
            "_execute_shutdown_callbacks",
            side_effect=Exception("Test error"),
        ):
            result = await self.manager.graceful_restart()

            assert result["success"] == False
            assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__])
