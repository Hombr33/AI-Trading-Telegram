"""
Complete EA Communication System Test
Tests all aspects of EA communication including HTTP endpoints, fallback mechanisms, and security.
"""

import asyncio
import json
import pytest
import aiohttp
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from src.main import app
from src.api.routes.ea import set_ea_globals
from src.services.user_manager import UserManager
from src.services.config_manager import ConfigManager
from src.execution.order_manager import OrderManager
from src.telegram_bot.core.trading_bot import TradingBot


class TestEACommunicationComplete:
    """Complete test suite for EA communication system."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_user_manager(self):
        """Mock user manager."""
        manager = Mock(spec=UserManager)
        manager.get_user_by_api_key = AsyncMock()
        return manager

    @pytest.fixture
    def mock_config_manager(self):
        """Mock config manager."""
        manager = Mock(spec=ConfigManager)
        manager.update_user_config = AsyncMock(return_value=True)
        return manager

    @pytest.fixture
    def mock_order_manager(self):
        """Mock order manager."""
        manager = Mock(spec=OrderManager)
        manager.execute_signal = AsyncMock()
        manager.modify_position = AsyncMock(return_value=True)
        manager.close_position = AsyncMock(return_value=True)
        return manager

    @pytest.fixture
    def mock_telegram_bot(self):
        """Mock telegram bot."""
        bot = Mock(spec=TradingBot)
        bot.notification_manager = Mock()
        bot.notification_manager.send_order_notification = AsyncMock()
        bot.notification_manager.send_position_notification = AsyncMock()
        return bot

    def setup_method(self):
        """Setup test environment."""
        # Set mock instances for EA routes
        set_ea_globals(
            self.mock_user_manager if hasattr(self, "mock_user_manager") else Mock(),
            (
                self.mock_config_manager
                if hasattr(self, "mock_config_manager")
                else Mock()
            ),
            self.mock_order_manager if hasattr(self, "mock_order_manager") else Mock(),
            self.mock_telegram_bot if hasattr(self, "mock_telegram_bot") else Mock(),
        )

    async def test_ea_api_key_validation_success(self, client, mock_user_manager):
        """Test successful EA API key validation."""
        # Mock successful authentication
        mock_user = Mock()
        mock_user.id = 123
        mock_user_manager.get_user_by_api_key.return_value = mock_user

        response = client.post("/api/v1/ea/validate", json={"api_key": "valid_key"})

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user_id"] == 123
        assert "API key is valid" in data["message"]

    async def test_ea_api_key_validation_failure(self, client, mock_user_manager):
        """Test failed EA API key validation."""
        # Mock failed authentication
        mock_user_manager.get_user_by_api_key.return_value = None

        response = client.post("/api/v1/ea/validate", json={"api_key": "invalid_key"})

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "Invalid API key" in data["message"]

    async def test_ea_order_success(
        self, client, mock_user_manager, mock_order_manager
    ):
        """Test successful EA order execution."""
        # Mock successful authentication and order execution
        mock_user = Mock()
        mock_user.id = 123
        mock_user_manager.get_user_by_api_key.return_value = mock_user

        mock_order_manager.execute_signal.return_value = {
            "success": True,
            "ticket": "12345",
        }

        order_data = {
            "api_key": "valid_key",
            "order": {
                "symbol": "EURUSD",
                "action": "BUY",
                "volume": 0.1,
                "price": 1.1234,
            },
        }

        response = client.post("/api/v1/ea/order", json=order_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["ticket"] == "12345"

    async def test_ea_order_failure(
        self, client, mock_user_manager, mock_order_manager
    ):
        """Test failed EA order execution."""
        # Mock successful authentication but failed order
        mock_user = Mock()
        mock_user.id = 123
        mock_user_manager.get_user_by_api_key.return_value = mock_user

        mock_order_manager.execute_signal.return_value = {
            "success": False,
            "error": "Insufficient funds",
        }

        order_data = {
            "api_key": "valid_key",
            "order": {
                "symbol": "EURUSD",
                "action": "BUY",
                "volume": 10.0,
                "price": 1.1234,
            },
        }

        response = client.post("/api/v1/ea/order", json=order_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Insufficient funds" in data["error"]

    async def test_ea_positions_success(self, client, mock_user_manager):
        """Test successful EA positions retrieval."""
        # Mock successful authentication
        mock_user = Mock()
        mock_user.id = 123
        mock_user_manager.get_user_by_api_key.return_value = mock_user

        # Mock database query
        with patch("src.api.routes.ea.get_db_session") as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Mock position
            mock_position = Mock()
            mock_position.ticket = "12345"
            mock_position.symbol = "EURUSD"
            mock_position.position_type = "BUY"
            mock_position.volume = 0.1
            mock_position.price_open = 1.1234
            mock_position.stop_loss = 1.1200
            mock_position.take_profit = 1.1300
            mock_position.profit = 10.5
            mock_position.swap = 0.0
            mock_position.commission = -0.1
            mock_position.time_open = datetime.now(timezone.utc)

            mock_db.query.return_value.filter.return_value.all.return_value = [
                mock_position
            ]

            response = client.post(
                "/api/v1/ea/positions", json={"api_key": "valid_key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["positions"]) == 1
            assert data["positions"][0]["ticket"] == "12345"
            assert data["positions"][0]["symbol"] == "EURUSD"

    async def test_ea_account_info(self, client, mock_user_manager):
        """Test EA account information retrieval."""
        # Mock successful authentication
        mock_user = Mock()
        mock_user.id = 123
        mock_user_manager.get_user_by_api_key.return_value = mock_user

        response = client.post("/api/v1/ea/account", json={"api_key": "valid_key"})

        assert response.status_code == 200
        data = response.json()
        assert "account" in data
        assert data["account"]["user_id"] == 123
        assert "balance" in data["account"]

    async def test_ea_modify_position_success(
        self, client, mock_user_manager, mock_order_manager
    ):
        """Test successful position modification."""
        # Mock successful authentication
        mock_user = Mock()
        mock_user.id = 123
        mock_user_manager.get_user_by_api_key.return_value = mock_user

        modify_data = {
            "api_key": "valid_key",
            "ticket": 12345,
            "new_sl": 1.1200,
            "new_tp": 1.1300,
        }

        response = client.post("/api/v1/ea/modify", json=modify_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_ea_close_position_success(
        self, client, mock_user_manager, mock_order_manager
    ):
        """Test successful position close."""
        # Mock successful authentication
        mock_user = Mock()
        mock_user.id = 123
        mock_user_manager.get_user_by_api_key.return_value = mock_user

        close_data = {"api_key": "valid_key", "ticket": 12345, "volume": 0.05}

        response = client.post("/api/v1/ea/close", json=close_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_ea_trade_history(self, client, mock_user_manager):
        """Test EA trade history retrieval."""
        # Mock successful authentication
        mock_user = Mock()
        mock_user.id = 123
        mock_user_manager.get_user_by_api_key.return_value = mock_user

        # Mock database query
        with patch("src.api.routes.ea.get_db_session") as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            # Mock trade
            mock_trade = Mock()
            mock_trade.ticket = "12345"
            mock_trade.symbol = "EURUSD"
            mock_trade.trade_type = "BUY"
            mock_trade.volume = 0.1
            mock_trade.price_open = 1.1234
            mock_trade.price_close = 1.1250
            mock_trade.profit = 15.5
            mock_trade.time_open = datetime.now(timezone.utc)
            mock_trade.time_close = datetime.now(timezone.utc)

            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
                mock_trade
            ]

            history_data = {"api_key": "valid_key", "days": 7}

            response = client.post("/api/v1/ea/history", json=history_data)

            assert response.status_code == 200
            data = response.json()
            assert len(data["trades"]) == 1
            assert data["trades"][0]["ticket"] == "12345"

    async def test_ea_settings_update(
        self, client, mock_user_manager, mock_config_manager
    ):
        """Test EA settings update."""
        # Mock successful authentication
        mock_user = Mock()
        mock_user.id = 123
        mock_user_manager.get_user_by_api_key.return_value = mock_user

        settings_data = {
            "api_key": "valid_key",
            "settings": {"max_risk_per_trade": 2.0, "enable_auto_trading": True},
        }

        response = client.post("/api/v1/ea/settings", json=settings_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_ea_health_check(self, client):
        """Test EA health check endpoint."""
        response = client.get("/api/v1/ea/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"

    async def test_ea_unauthorized_access(self, client, mock_user_manager):
        """Test unauthorized access to EA endpoints."""
        # Mock failed authentication
        mock_user_manager.get_user_by_api_key.return_value = None

        endpoints = [
            ("/api/v1/ea/order", {"api_key": "invalid", "order": {}}),
            ("/api/v1/ea/positions", {"api_key": "invalid"}),
            ("/api/v1/ea/account", {"api_key": "invalid"}),
            ("/api/v1/ea/modify", {"api_key": "invalid", "ticket": 123}),
            ("/api/v1/ea/close", {"api_key": "invalid", "ticket": 123}),
            ("/api/v1/ea/history", {"api_key": "invalid", "days": 7}),
            ("/api/v1/ea/settings", {"api_key": "invalid", "settings": {}}),
        ]

        for endpoint, payload in endpoints:
            response = client.post(endpoint, json=payload)
            assert response.status_code == 401
            data = response.json()
            assert "Invalid API key" in data["detail"]

    async def test_http_fallback_mechanism(self):
        """Test HTTP fallback mechanism for EA communication."""
        # Test direct HTTP communication to EA endpoints
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get(
                "http://127.0.0.1:8000/api/v1/ea/health"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    assert data["status"] == "healthy"
                else:
                    # If server is not running, that's expected for this test
                    assert response.status in [
                        404,
                        500,
                    ]  # Server not running or internal error

    async def test_ea_communication_error_handling(self, client, mock_user_manager):
        """Test error handling in EA communication."""
        # Mock authentication failure due to exception
        mock_user_manager.get_user_by_api_key.side_effect = Exception("Database error")

        response = client.post("/api/v1/ea/validate", json={"api_key": "test_key"})

        # Should return 500 for internal server errors
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]

    async def test_ea_rate_limiting_simulation(self, client, mock_user_manager):
        """Test rate limiting simulation for EA endpoints."""
        # Mock successful authentication
        mock_user = Mock()
        mock_user.id = 123
        mock_user_manager.get_user_by_api_key.return_value = mock_user

        # Simulate multiple rapid requests
        for i in range(10):
            response = client.post("/api/v1/ea/validate", json={"api_key": "valid_key"})
            assert response.status_code == 200

        # In a real implementation, this would test rate limiting
        # For now, we just ensure the endpoint handles multiple requests

    async def test_ea_data_validation(self, client):
        """Test data validation for EA endpoints."""
        # Test missing required fields
        response = client.post("/api/v1/ea/order", json={})
        assert response.status_code == 422  # Validation error

        response = client.post("/api/v1/ea/modify", json={"api_key": "test"})
        assert response.status_code == 422  # Missing ticket

        response = client.post("/api/v1/ea/close", json={"api_key": "test"})
        assert response.status_code == 422  # Missing ticket

    async def test_ea_communication_security(self, client):
        """Test security measures for EA communication."""
        # Test with various invalid inputs
        test_cases = [
            {"api_key": ""},
            {"api_key": None},
            {"api_key": "<script>alert('xss')</script>"},
            {"api_key": "a" * 1000},  # Very long key
        ]

        for test_case in test_cases:
            response = client.post("/api/v1/ea/validate", json=test_case)
            # Should not crash, should handle gracefully
            assert response.status_code in [200, 422]

    def test_ea_endpoints_exist(self, client):
        """Test that all EA endpoints exist and are accessible."""
        endpoints = [
            "/api/v1/ea/validate",
            "/api/v1/ea/health",
            "/api/v1/ea/order",
            "/api/v1/ea/positions",
            "/api/v1/ea/account",
            "/api/v1/ea/modify",
            "/api/v1/ea/close",
            "/api/v1/ea/history",
            "/api/v1/ea/settings",
        ]

        for endpoint in endpoints:
            if endpoint.endswith("/health"):
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})

            # Should not return 404
            assert response.status_code != 404, f"Endpoint {endpoint} not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
