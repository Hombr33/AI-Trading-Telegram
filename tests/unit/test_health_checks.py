"""
Unit tests for the multi-user service health check functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from src.services.multi_user_service import MultiUserService


class TestMultiUserServiceHealthCheck:
    """Test cases for health check functionality in MultiUserService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = MultiUserService("test_token")

    @pytest.mark.asyncio
    async def test_perform_health_check_basic(self):
        """Test basic health check execution."""
        # Mock all health check methods
        self.service._check_database_health = AsyncMock()
        self.service._check_telegram_bot_health = AsyncMock()
        self.service._check_ea_bridge_health = AsyncMock()
        self.service._check_crypto_bridge_health = AsyncMock()
        self.service._check_signal_queue_health = AsyncMock()
        self.service._check_memory_usage = AsyncMock()
        self.service._calculate_overall_health_status = Mock()
        self.service._send_health_alert = AsyncMock()

        await self.service._perform_health_check()

        # Verify all health checks were called
        self.service._check_database_health.assert_called_once()
        self.service._check_telegram_bot_health.assert_called_once()
        self.service._check_ea_bridge_health.assert_called_once()
        self.service._check_crypto_bridge_health.assert_called_once()
        self.service._check_signal_queue_health.assert_called_once()
        self.service._check_memory_usage.assert_called_once()
        self.service._calculate_overall_health_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_database_health_success(self):
        """Test successful database health check."""
        health_status = {"database": {}}

        mock_session = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = (1,)
        mock_session.execute.return_value = mock_result

        with patch("src.database.session.SessionLocal") as mock_session_local:
            mock_session_local.return_value = mock_session
            await self.service._check_database_health(health_status)

            assert health_status["database"]["status"] == "healthy"
            assert "error" not in health_status["database"]

    @pytest.mark.asyncio
    async def test_check_database_health_failure(self):
        """Test database health check failure."""
        health_status = {"database": {}}

        mock_session = Mock()
        mock_session.execute.side_effect = Exception("Database connection failed")

        with patch("src.database.session.SessionLocal") as mock_session_local:
            mock_session_local.return_value = mock_session
            await self.service._check_database_health(health_status)

            assert health_status["database"]["status"] == "critical"
            assert "error" in health_status["database"]
            assert "Database connection failed" in health_status["database"]["error"]

    @pytest.mark.asyncio
    async def test_check_telegram_bot_health_success(self):
        """Test successful Telegram bot health check."""
        health_status = {"telegram_bot": {}}

        mock_bot = Mock()
        mock_bot_info = Mock()
        mock_bot_info.username = "test_bot"
        mock_bot.bot.get_me = AsyncMock(return_value=mock_bot_info)

        self.service.telegram_bot = mock_bot

        await self.service._check_telegram_bot_health(health_status)

        assert health_status["telegram_bot"]["status"] == "healthy"
        assert health_status["telegram_bot"]["bot_username"] == "test_bot"

    @pytest.mark.asyncio
    async def test_check_telegram_bot_health_no_bot(self):
        """Test Telegram bot health check when no bot available."""
        health_status = {"telegram_bot": {}}

        self.service.telegram_bot = None

        await self.service._check_telegram_bot_health(health_status)

        assert health_status["telegram_bot"]["status"] == "critical"
        assert "error" in health_status["telegram_bot"]

    @pytest.mark.asyncio
    async def test_check_ea_bridge_health_success(self):
        """Test successful EA bridge health check."""
        health_status = {"ea_bridge": {}}

        mock_ea_bridge = Mock()
        connection_health = {"user1": {"connected": True}, "user2": {"connected": True}}
        mock_ea_bridge.get_all_user_connections_health = AsyncMock(
            return_value=connection_health
        )

        self.service.ea_bridge = mock_ea_bridge

        await self.service._check_ea_bridge_health(health_status)

        assert health_status["ea_bridge"]["status"] == "healthy"
        assert health_status["ea_bridge"]["connected_users"] == 2
        assert health_status["ea_bridge"]["total_users"] == 2

    @pytest.mark.asyncio
    async def test_check_ea_bridge_health_partial_connections(self):
        """Test EA bridge health check with partial connections."""
        health_status = {"ea_bridge": {}}

        mock_ea_bridge = Mock()
        connection_health = {
            "user1": {"connected": True},
            "user2": {"connected": False},
        }
        mock_ea_bridge.get_all_user_connections_health = AsyncMock(
            return_value=connection_health
        )

        self.service.ea_bridge = mock_ea_bridge

        await self.service._check_ea_bridge_health(health_status)

        assert health_status["ea_bridge"]["status"] == "warning"
        assert health_status["ea_bridge"]["connected_users"] == 1
        assert health_status["ea_bridge"]["total_users"] == 2

    @pytest.mark.asyncio
    async def test_check_signal_queue_health_normal(self):
        """Test signal queue health check with normal queue sizes."""
        health_status = {"signal_queues": {}}

        # Mock queue sizes
        self.service._immediate_queue = Mock()
        self.service._immediate_queue.qsize.return_value = 10
        self.service._delayed_queue = Mock()
        self.service._delayed_queue.qsize.return_value = 5
        self.service._batch_queue = [1, 2, 3]  # 3 items

        await self.service._check_signal_queue_health(health_status)

        assert health_status["signal_queues"]["status"] == "healthy"
        assert health_status["signal_queues"]["sizes"]["immediate"] == 10
        assert health_status["signal_queues"]["sizes"]["delayed"] == 5
        assert health_status["signal_queues"]["sizes"]["batch"] == 3

    @pytest.mark.asyncio
    async def test_check_signal_queue_health_overflow(self):
        """Test signal queue health check with queue overflow."""
        health_status = {"signal_queues": {}}

        # Mock large queue sizes
        self.service._immediate_queue = Mock()
        self.service._immediate_queue.qsize.return_value = 800
        self.service._delayed_queue = Mock()
        self.service._delayed_queue.qsize.return_value = 300
        self.service._batch_queue = [1] * 100  # 100 items

        await self.service._check_signal_queue_health(health_status)

        assert health_status["signal_queues"]["status"] == "warning"
        assert "High queue size" in health_status["signal_queues"]["error"]

    @pytest.mark.asyncio
    @patch("psutil.Process")
    async def test_check_memory_usage_normal(self, mock_process_class):
        """Test memory usage check with normal usage."""
        health_status = {"memory_usage": {}}

        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100 MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process

        await self.service._check_memory_usage(health_status)

        assert health_status["memory_usage"]["status"] == "healthy"
        assert health_status["memory_usage"]["usage_mb"] == 100.0

    @pytest.mark.asyncio
    @patch("psutil.Process")
    async def test_check_memory_usage_high(self, mock_process_class):
        """Test memory usage check with high usage."""
        health_status = {"memory_usage": {}}

        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 800 * 1024 * 1024  # 800 MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process

        await self.service._check_memory_usage(health_status)

        assert health_status["memory_usage"]["status"] == "warning"
        assert "Elevated memory usage" in health_status["memory_usage"]["error"]

    def test_calculate_overall_health_status_healthy(self):
        """Test overall health status calculation - healthy."""
        health_status = {
            "database": {"status": "healthy"},
            "telegram_bot": {"status": "healthy"},
            "ea_bridge": {"status": "healthy"},
            "crypto_bridge": {"status": "healthy"},
            "signal_queues": {"status": "healthy"},
            "memory_usage": {"status": "healthy"},
        }

        self.service._calculate_overall_health_status(health_status)

        assert health_status["overall_status"] == "healthy"

    def test_calculate_overall_health_status_warning(self):
        """Test overall health status calculation - warning."""
        health_status = {
            "database": {"status": "healthy"},
            "telegram_bot": {"status": "healthy"},
            "ea_bridge": {"status": "warning"},
            "crypto_bridge": {"status": "healthy"},
            "signal_queues": {"status": "healthy"},
            "memory_usage": {"status": "healthy"},
        }

        self.service._calculate_overall_health_status(health_status)

        assert health_status["overall_status"] == "warning"

    def test_calculate_overall_health_status_critical(self):
        """Test overall health status calculation - critical."""
        health_status = {
            "database": {"status": "critical"},
            "telegram_bot": {"status": "healthy"},
            "ea_bridge": {"status": "healthy"},
            "crypto_bridge": {"status": "healthy"},
            "signal_queues": {"status": "healthy"},
            "memory_usage": {"status": "healthy"},
        }

        self.service._calculate_overall_health_status(health_status)

        assert health_status["overall_status"] == "critical"

    def test_get_health_issues(self):
        """Test health issues extraction."""
        health_status = {
            "database": {"status": "critical", "error": "Connection failed"},
            "telegram_bot": {"status": "healthy"},
            "ea_bridge": {"status": "warning", "error": "Partial connections"},
            "crypto_bridge": {"status": "healthy"},
            "signal_queues": {"status": "healthy"},
            "memory_usage": {"status": "healthy"},
        }

        issues = self.service._get_health_issues(health_status)

        assert len(issues) == 2
        assert "database: Connection failed" in issues
        assert "ea_bridge: Partial connections" in issues

    @pytest.mark.asyncio
    async def test_send_health_alert(self):
        """Test sending health alerts."""
        health_status = {
            "overall_status": "critical",
            "database": {"status": "critical", "error": "Connection failed"},
        }

        mock_bot = Mock()
        mock_bot.send_admin_alert = AsyncMock()
        self.service.telegram_bot = mock_bot

        await self.service._send_health_alert(health_status)

        mock_bot.send_admin_alert.assert_called_once()
        call_args = mock_bot.send_admin_alert.call_args[0][0]
        assert "System Health Alert" in call_args
        assert "CRITICAL" in call_args


if __name__ == "__main__":
    pytest.main([__file__])
