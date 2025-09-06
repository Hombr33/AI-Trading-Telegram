"""
Test EA API routes directly.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.routes.ea import router as ea_router, set_ea_globals

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_user_manager():
    """Mock user manager."""
    manager = Mock()
    manager.get_user_by_api_key = AsyncMock()
    return manager


@pytest.fixture
def mock_config_manager():
    """Mock config manager."""
    manager = Mock()
    manager.update_user_config = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def mock_order_manager():
    """Mock order manager."""
    manager = Mock()
    manager.execute_signal = AsyncMock()
    manager.modify_position = AsyncMock(return_value=True)
    manager.close_position = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def mock_telegram_bot():
    """Mock telegram bot."""
    bot = Mock()
    bot.notification_manager = Mock()
    bot.notification_manager.send_order_notification = AsyncMock()
    bot.notification_manager.send_position_notification = AsyncMock()
    return bot


@pytest.fixture
def app(mock_user_manager, mock_config_manager, mock_order_manager, mock_telegram_bot):
    """Create test app with EA routes."""
    # Set mock instances for EA routes
    set_ea_globals(
        mock_user_manager, mock_config_manager, mock_order_manager, mock_telegram_bot
    )

    app = FastAPI()
    app.include_router(ea_router, prefix="/api/v1/ea")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestEARoutes:
    """Test EA API routes."""

    def test_ea_health_check(self, client):
        """Test EA health check endpoint."""
        response = client.get("/api/v1/ea/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"

    def test_ea_api_key_validation_success(self, client, mock_user_manager):
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

    def test_ea_api_key_validation_failure(self, client, mock_user_manager):
        """Test failed EA API key validation."""
        # Mock failed authentication
        mock_user_manager.get_user_by_api_key.return_value = None

        response = client.post("/api/v1/ea/validate", json={"api_key": "invalid_key"})

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "Invalid API key" in data["message"]

    def test_ea_unauthorized_access(self, client, mock_user_manager):
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

    def test_ea_data_validation(self, client):
        """Test data validation for EA endpoints."""
        # Test missing required fields
        response = client.post("/api/v1/ea/order", json={})
        assert response.status_code == 422  # Validation error

        response = client.post("/api/v1/ea/modify", json={"api_key": "test"})
        assert response.status_code == 422  # Missing ticket

        response = client.post("/api/v1/ea/close", json={"api_key": "test"})
        assert response.status_code == 422  # Missing ticket

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
