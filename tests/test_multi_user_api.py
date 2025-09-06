"""
Tests for Multi-User API endpoints.

This module contains comprehensive tests for all multi-user API endpoints
including user management, configuration, signal processing, and admin operations.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes.multi_user import router, set_multi_user_service
from src.services.config_manager import ConfigManager
from src.services.multi_user_service import MultiUserService
from src.services.user_manager import UserManager


@pytest.fixture
def app():
    """Create FastAPI test application."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_multi_user_service():
    """Create mock multi-user service."""
    service = Mock(spec=MultiUserService)

    # Mock user manager
    user_manager = Mock(spec=UserManager)
    service.user_manager = user_manager

    # Mock config manager
    config_manager = Mock(spec=ConfigManager)
    service.config_manager = config_manager

    return service


@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        "telegram_id": 123456789,
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "role": "user",
        "subscription_status": "active",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00",
        "last_activity": "2024-01-01T12:00:00",
        "subscription_expires_at": None,
    }


@pytest.fixture
def sample_configuration():
    """Sample configuration data for testing."""
    return {
        "risk_per_trade_pct": 2.0,
        "max_daily_drawdown_pct": 6.0,
        "max_daily_loss_usd": 25.0,
        "max_open_positions": 10,
        "max_daily_trades": 50,
    }


class TestUserManagement:
    """Test user management endpoints."""

    def test_create_user_success(self, client, mock_multi_user_service, sample_user):
        """Test successful user creation."""
        # Setup mock
        mock_multi_user_service.user_manager.create_user = AsyncMock(return_value=True)

        # Mock get_user to return the created user
        mock_user = Mock()
        mock_user.telegram_id = sample_user["telegram_id"]
        mock_user.username = sample_user["username"]
        mock_user.first_name = sample_user["first_name"]
        mock_user.last_name = sample_user["last_name"]
        mock_user.role.value = sample_user["role"]
        mock_user.subscription_status.value = sample_user["subscription_status"]
        mock_user.is_active = sample_user["is_active"]
        mock_user.created_at = datetime.fromisoformat(sample_user["created_at"])
        mock_user.last_activity = datetime.fromisoformat(sample_user["last_activity"])
        mock_user.subscription_expires_at = None

        mock_multi_user_service.user_manager.get_user = AsyncMock(
            return_value=mock_user
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Test data
        user_data = {
            "telegram_id": 123456789,
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "role": "user",
        }

        # Make request
        response = client.post("/multi-user/users", json=user_data)

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == user_data["telegram_id"]
        assert data["username"] == user_data["username"]
        assert data["role"] == user_data["role"]

    def test_create_user_failure(self, client, mock_multi_user_service):
        """Test user creation failure."""
        # Setup mock
        mock_multi_user_service.user_manager.create_user = AsyncMock(return_value=False)

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Test data
        user_data = {
            "telegram_id": 123456789,
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "role": "user",
        }

        # Make request
        response = client.post("/multi-user/users", json=user_data)

        # Assert response
        assert response.status_code == 400
        assert "Failed to create user" in response.json()["detail"]

    def test_get_all_users_admin_success(
        self, client, mock_multi_user_service, sample_user
    ):
        """Test getting all users as admin."""
        # Setup mock
        mock_multi_user_service.user_manager.get_all_users = AsyncMock(
            return_value=[sample_user]
        )
        mock_multi_user_service.user_manager.is_admin = AsyncMock(return_value=True)

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Make request
        response = client.get("/multi-user/users?admin_telegram_id=123456789")

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["users"]) == 1
        assert data["users"][0]["telegram_id"] == sample_user["telegram_id"]

    def test_get_all_users_unauthorized(self, client, mock_multi_user_service):
        """Test getting all users without admin privileges."""
        # Setup mock
        mock_multi_user_service.user_manager.get_all_users = AsyncMock(
            return_value=None
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Make request
        response = client.get("/multi-user/users?admin_telegram_id=123456789")

        # Assert response
        assert response.status_code == 403
        assert "Admin privileges required" in response.json()["detail"]

    def test_get_user_success(self, client, mock_multi_user_service, sample_user):
        """Test getting a specific user."""
        # Setup mock
        mock_user = Mock()
        mock_user.telegram_id = sample_user["telegram_id"]
        mock_user.username = sample_user["username"]
        mock_user.first_name = sample_user["first_name"]
        mock_user.last_name = sample_user["last_name"]
        mock_user.role.value = sample_user["role"]
        mock_user.subscription_status.value = sample_user["subscription_status"]
        mock_user.is_active = sample_user["is_active"]
        mock_user.created_at = datetime.fromisoformat(sample_user["created_at"])
        mock_user.last_activity = datetime.fromisoformat(sample_user["last_activity"])
        mock_user.subscription_expires_at = None

        mock_multi_user_service.user_manager.get_user = AsyncMock(
            return_value=mock_user
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Make request
        response = client.get("/multi-user/users/123456789")

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == sample_user["telegram_id"]
        assert data["username"] == sample_user["username"]

    def test_get_user_not_found(self, client, mock_multi_user_service):
        """Test getting a non-existent user."""
        # Setup mock
        mock_multi_user_service.user_manager.get_user = AsyncMock(return_value=None)

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Make request
        response = client.get("/multi-user/users/999999999")

        # Assert response
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestSubscriptionManagement:
    """Test subscription management endpoints."""

    def test_set_user_subscription_success(self, client, mock_multi_user_service):
        """Test setting user subscription successfully."""
        # Setup mock
        mock_multi_user_service.user_manager.set_subscription = AsyncMock(
            return_value=True
        )
        mock_multi_user_service.user_manager.is_admin = AsyncMock(return_value=True)

        # Mock get_user for response
        mock_user = Mock()
        mock_user.telegram_id = 123456789
        mock_user.subscription_status.value = "active"
        mock_user.subscription_expires_at = None

        mock_multi_user_service.user_manager.get_user = AsyncMock(
            return_value=mock_user
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Test data
        subscription_data = {
            "telegram_id": 123456789,
            "status": "active",
            "expires_at": "2024-12-31T23:59:59",
            "plan_type": "premium",
            "auto_renew": True,
        }

        # Make request
        response = client.post(
            "/multi-user/users/subscription?admin_telegram_id=123456789",
            json=subscription_data,
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == subscription_data["telegram_id"]
        assert data["status"] == subscription_data["status"]

    def test_set_user_subscription_unauthorized(self, client, mock_multi_user_service):
        """Test setting user subscription without admin privileges."""
        # Setup mock
        mock_multi_user_service.user_manager.set_subscription = AsyncMock(
            return_value=False
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Test data
        subscription_data = {"telegram_id": 123456789, "status": "active"}

        # Make request
        response = client.post(
            "/multi-user/users/subscription?admin_telegram_id=123456789",
            json=subscription_data,
        )

        # Assert response
        assert response.status_code == 403


class TestPlatformConnectionManagement:
    """Test platform connection management endpoints."""

    def test_register_platform_connection_success(
        self, client, mock_multi_user_service
    ):
        """Test registering platform connection successfully."""
        # Setup mock
        mock_multi_user_service.user_manager.register_platform_connection = AsyncMock(
            return_value=True
        )

        # Mock get_user_platform_connections for response
        connection_data = {
            "id": 1,
            "platform_type": "mt5",
            "connection_name": "Test MT5",
            "api_key": "test_key_123",
            "server_endpoint": "mt5.server.com",
            "last_connected": "2024-01-01T12:00:00",
            "created_at": "2024-01-01T10:00:00",
        }

        mock_multi_user_service.user_manager.get_user_platform_connections = AsyncMock(
            return_value=[connection_data]
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Test data
        connection_request = {
            "telegram_id": 123456789,
            "platform_type": "mt5",
            "connection_name": "Test MT5",
            "api_key": "test_key_123",
            "api_secret": "test_secret_123",
            "server_endpoint": "mt5.server.com",
            "test_connection": True,
        }

        # Make request
        response = client.post(
            "/multi-user/users/platform-connection", json=connection_request
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["platform_type"] == connection_request["platform_type"]
        assert data["connection_name"] == connection_request["connection_name"]
        assert "api_key_masked" in data

    def test_get_user_connections_success(self, client, mock_multi_user_service):
        """Test getting user platform connections."""
        # Setup mock
        connections = [
            {
                "id": 1,
                "platform_type": "mt5",
                "connection_name": "Test MT5",
                "api_key": "test_key_123",
                "server_endpoint": "mt5.server.com",
                "last_connected": "2024-01-01T12:00:00",
                "created_at": "2024-01-01T10:00:00",
            }
        ]

        mock_multi_user_service.user_manager.get_user_platform_connections = AsyncMock(
            return_value=connections
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Make request
        response = client.get("/multi-user/users/123456789/connections")

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["connections"]) == 1
        assert data["connections"][0]["platform_type"] == "mt5"


class TestConfigurationManagement:
    """Test configuration management endpoints."""

    def test_set_user_configuration_success(
        self, client, mock_multi_user_service, sample_configuration
    ):
        """Test setting user configuration successfully."""
        # Setup mock
        mock_multi_user_service.config_manager.validate_config = AsyncMock(
            return_value=(True, "Valid")
        )
        mock_multi_user_service.config_manager.set_user_config = AsyncMock(
            return_value=True
        )
        mock_multi_user_service.config_manager.get_user_config = AsyncMock(
            return_value=sample_configuration
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Test data
        config_data = {
            "telegram_id": 123456789,
            "config_type": "risk",
            "config_data": sample_configuration,
            "validate": True,
        }

        # Make request
        response = client.post("/multi-user/users/configuration", json=config_data)

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["config_type"] == config_data["config_type"]
        assert (
            data["config_data"]["risk_per_trade_pct"]
            == sample_configuration["risk_per_trade_pct"]
        )

    def test_get_user_configuration_success(
        self, client, mock_multi_user_service, sample_configuration
    ):
        """Test getting user configuration."""
        # Setup mock
        mock_multi_user_service.config_manager.get_user_config = AsyncMock(
            return_value=sample_configuration
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Make request
        response = client.get(
            "/multi-user/users/123456789/configuration?config_type=risk"
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert "configurations" in data
        assert "risk" in data["configurations"]
        assert data["configurations"]["risk"]["config_type"] == "risk"
        assert (
            data["configurations"]["risk"]["config_data"]["risk_per_trade_pct"]
            == sample_configuration["risk_per_trade_pct"]
        )


class TestSignalManagement:
    """Test signal management endpoints."""

    def test_process_signal_success(self, client, mock_multi_user_service):
        """Test processing signal successfully."""
        # Setup mock
        signal_result = {
            "success": True,
            "distributed_to": [123456789],
            "skipped": [],
            "execution_results": {"successful": [], "failed": []},
            "distribution_plan": {
                "total_users": 1,
                "immediate": [123456789],
                "delayed": [],
                "batch": [],
            },
        }

        mock_multi_user_service.process_signal = AsyncMock(return_value=signal_result)

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Test data
        signal_data = {
            "symbol": "XAUUSD",
            "bias": "BULLISH",
            "setups": [
                {
                    "type": "BUY",
                    "entry_zone": [1950.00, 1960.00],
                    "sl": 1940.00,
                    "tp": [1970.00, 1980.00],
                    "confidence": 75,
                }
            ],
            "confidence": 75,
        }

        # Make request
        response = client.post("/multi-user/signal/process", json=signal_data)

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["distributed_to"]) == 1
        assert data["distributed_to"][0] == 123456789

    def test_subscribe_to_symbol_success(self, client, mock_multi_user_service):
        """Test subscribing to symbol successfully."""
        # Setup mock
        mock_multi_user_service.user_manager.subscribe_to_symbol = AsyncMock(
            return_value=True
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Test data
        subscription_data = {
            "telegram_id": 123456789,
            "symbol": "EURUSD",
            "min_confidence": 70,
        }

        # Make request
        response = client.post(
            "/multi-user/users/123456789/signal-subscription", json=subscription_data
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == subscription_data["symbol"]
        assert data["min_confidence"] == subscription_data["min_confidence"]
        assert data["is_active"] == True


class TestTradingManagement:
    """Test trading management endpoints."""

    def test_submit_user_order_success(self, client, mock_multi_user_service):
        """Test submitting user order successfully."""
        # Setup mock
        order_result = {
            "success": True,
            "order_id": "order_123",
            "details": {"status": "submitted"},
        }

        mock_multi_user_service.submit_user_order = AsyncMock(return_value=order_result)

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Test data
        order_data = {
            "telegram_id": 123456789,
            "symbol": "XAUUSD",
            "order_type": "BUY",
            "volume": 0.1,
            "price": 1950.00,
            "sl": 1940.00,
            "tp": 1970.00,
            "platform": "mt5",
        }

        # Make request
        response = client.post("/multi-user/users/123456789/orders", json=order_data)

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["order_id"] == order_result["order_id"]

    def test_get_user_trading_status_success(self, client, mock_multi_user_service):
        """Test getting user trading status."""
        # Setup mock
        trading_status = {
            "telegram_id": 123456789,
            "positions": [
                {
                    "ticket": 12345,
                    "symbol": "XAUUSD",
                    "type": "BUY",
                    "volume": 0.1,
                    "open_price": 1950.00,
                    "current_price": 1955.00,
                    "stop_loss": 1940.00,
                    "take_profit": 1970.00,
                    "pnl": 50.00,
                    "open_time": "2024-01-01T10:00:00",
                }
            ],
            "pending_orders": [],
            "risk_metrics": {
                "total_risk": 20.00,
                "daily_pnl": 50.00,
                "open_positions": 1,
            },
            "platform_connections": ["mt5"],
            "timestamp": "2024-01-01T12:00:00",
        }

        mock_multi_user_service.get_user_trading_status = AsyncMock(
            return_value=trading_status
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Make request
        response = client.get("/multi-user/users/123456789/trading-status")

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == 123456789
        assert len(data["positions"]) == 1
        assert data["positions"][0]["symbol"] == "XAUUSD"


class TestAdminOperations:
    """Test admin operation endpoints."""

    def test_get_admin_stats_success(
        self, client, mock_multi_user_service, sample_user
    ):
        """Test getting admin statistics successfully."""
        # Setup mock
        mock_multi_user_service.user_manager.get_all_users = AsyncMock(
            return_value=[sample_user]
        )
        mock_multi_user_service.user_manager.is_admin = AsyncMock(return_value=True)

        service_stats = {
            "system_health": {"status": "running", "uptime": 123456},
            "signal_stats": {"total_processed": 100, "auto_trades_executed": 50},
        }

        mock_multi_user_service.get_enhanced_service_stats = AsyncMock(
            return_value=service_stats
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Make request
        response = client.get("/multi-user/admin/stats?admin_telegram_id=123456789")

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == 1
        assert data["active_users"] == 1
        assert data["total_signals_processed"] == 100

    def test_promote_user_success(self, client, mock_multi_user_service):
        """Test promoting user to admin successfully."""
        # Setup mock
        mock_multi_user_service.user_manager.add_admin = AsyncMock(return_value=True)
        mock_multi_user_service.user_manager.is_admin = AsyncMock(return_value=True)

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Make request
        response = client.post(
            "/multi-user/admin/users/123456789/promote?admin_telegram_id=123456789"
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert "promoted to admin" in data["message"]


class TestMonitoring:
    """Test monitoring endpoints."""

    def test_get_service_stats_success(self, client, mock_multi_user_service):
        """Test getting service statistics."""
        # Setup mock
        stats = {
            "service_status": "running",
            "bot_stats": {"active_users": 10},
            "signal_stats": {"total_processed": 100, "auto_trades_executed": 50},
            "queue_stats": {
                "immediate_queue_size": 0,
                "delayed_queue_size": 0,
                "batch_queue_size": 0,
            },
            "active_tasks": 5,
        }

        mock_multi_user_service.get_service_stats = AsyncMock(return_value=stats)

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Make request
        response = client.get("/multi-user/stats")

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["active_users"] == 10
        assert data["signals_processed_today"] == 100

    def test_get_system_health_success(self, client, mock_multi_user_service):
        """Test getting system health."""
        # Setup mock
        stats = {
            "service_status": "running",
            "bot_stats": {"status": "active"},
            "uptime": "2 days, 3 hours",
        }

        mock_multi_user_service.get_service_stats = AsyncMock(return_value=stats)

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Make request
        response = client.get("/multi-user/health")

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "healthy"
        assert data["services"]["multi_user_service"] == "running"


class TestSecurity:
    """Test security endpoints."""

    def test_check_authentication_success(
        self, client, mock_multi_user_service, sample_user
    ):
        """Test authentication check successfully."""
        # Setup mock
        mock_user = Mock()
        mock_user.telegram_id = sample_user["telegram_id"]
        mock_user.username = sample_user["username"]
        mock_user.first_name = sample_user["first_name"]
        mock_user.last_name = sample_user["last_name"]
        mock_user.role.value = sample_user["role"]
        mock_user.subscription_status.value = sample_user["subscription_status"]
        mock_user.is_active = sample_user["is_active"]
        mock_user.created_at = datetime.fromisoformat(sample_user["created_at"])
        mock_user.last_activity = datetime.fromisoformat(sample_user["last_activity"])
        mock_user.subscription_expires_at = None

        mock_multi_user_service.user_manager.get_user = AsyncMock(
            return_value=mock_user
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Test data
        auth_data = {"telegram_id": 123456789, "token": "test_token"}

        # Make request
        response = client.post("/multi-user/auth/check", json=auth_data)

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] == True
        assert data["user"]["telegram_id"] == sample_user["telegram_id"]

    def test_check_permissions_success(
        self, client, mock_multi_user_service, sample_user
    ):
        """Test permission check successfully."""
        # Setup mock
        mock_user = Mock()
        mock_user.telegram_id = sample_user["telegram_id"]
        mock_user.is_active = sample_user["is_active"]
        mock_user.is_admin = False

        mock_multi_user_service.user_manager.get_user = AsyncMock(
            return_value=mock_user
        )
        mock_multi_user_service.user_manager.is_subscribed = AsyncMock(
            return_value=True
        )

        # Set service
        set_multi_user_service(mock_multi_user_service)

        # Test data
        permission_data = {
            "telegram_id": 123456789,
            "resource": "trading",
            "action": "execute",
        }

        # Make request
        response = client.post("/multi-user/auth/permissions", json=permission_data)

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
