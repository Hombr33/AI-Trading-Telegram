"""
Tests for Multi-User EA Bridge Integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

from src.bridge.ea_bridge import EABridge
from src.execution.multi_user_position_manager import MultiUserPositionManager
from src.execution.multi_user_order_manager import MultiUserOrderManager
from src.services.multi_user_service import MultiUserService
from src.services.user_manager import UserManager
from src.services.config_manager import ConfigManager
from src.core.config import TradingConfig


class TestMultiUserEABridge:
    """Test multi-user EA bridge functionality."""

    @pytest.fixture
    def user_manager(self):
        """Mock user manager."""
        manager = Mock(spec=UserManager)
        manager.is_user_authorized = AsyncMock(return_value=True)
        manager.get_user_subscriptions = AsyncMock(return_value=[
            {"symbol": "EURUSD", "min_confidence": 60}
        ])
        return manager

    @pytest.fixture
    def config_manager(self):
        """Mock config manager."""
        manager = Mock(spec=ConfigManager)
        manager.get_user_config = AsyncMock(return_value={
            "max_open_positions": 5,
            "max_exposure": 10000,
            "max_daily_drawdown_pct": 5.0,
            "auto_trading_enabled": True
        })
        return manager

    @pytest.fixture
    def ea_bridge(self, user_manager, config_manager):
        """Create EA bridge instance."""
        bridge = EABridge()
        bridge.user_manager = user_manager
        bridge.config_manager = config_manager
        return bridge

    @pytest.fixture
    def position_manager(self, ea_bridge, user_manager, config_manager):
        """Create position manager instance."""
        config = TradingConfig()
        manager = MultiUserPositionManager(ea_bridge, user_manager, config)
        return manager

    @pytest.fixture
    def order_manager(self, ea_bridge, position_manager, user_manager, config_manager):
        """Create order manager instance."""
        manager = MultiUserOrderManager(ea_bridge, position_manager, user_manager, config_manager)
        return manager

    @pytest.fixture
    def multi_user_service(self, user_manager, config_manager, ea_bridge, position_manager, order_manager):
        """Create multi-user service instance."""
        service = MultiUserService("test_token")
        service.user_manager = user_manager
        service.config_manager = config_manager
        service.ea_bridge = ea_bridge
        service.position_manager = position_manager
        service.order_manager = order_manager
        return service

    @pytest.mark.asyncio
    async def test_ea_bridge_user_session_initialization(self, ea_bridge):
        """Test user session initialization in EA bridge."""
        telegram_id = 12345

        with patch.object(ea_bridge, '_establish_user_connection', new_callable=AsyncMock) as mock_establish:
            mock_establish.return_value = {"api_key": "test_key", "server_endpoint": "http://test.com"}

            result = await ea_bridge.initialize_user_session(telegram_id)

            assert result is True
            assert telegram_id in ea_bridge._user_connections
            assert telegram_id in ea_bridge._connection_health

    @pytest.mark.asyncio
    async def test_ea_bridge_user_isolation(self, ea_bridge):
        """Test user data isolation in EA bridge."""
        user1_id = 12345
        user2_id = 67890

        # Mock user connections
        ea_bridge._user_connections = {
            user1_id: {"api_key": "key1", "server_endpoint": "http://test1.com"},
            user2_id: {"api_key": "key2", "server_endpoint": "http://test2.com"}
        }

        # Test user-specific data access
        conn1 = ea_bridge._user_connections.get(user1_id)
        conn2 = ea_bridge._user_connections.get(user2_id)

        assert conn1["api_key"] == "key1"
        assert conn2["api_key"] == "key2"
        assert conn1 != conn2

    @pytest.mark.asyncio
    async def test_ea_bridge_risk_validation(self, ea_bridge):
        """Test risk validation for user orders."""
        telegram_id = 12345

        # Mock risk metrics
        ea_bridge._user_risk_metrics = {
            telegram_id: {
                "position_count": 3,
                "total_exposure": 5000,
                "daily_pnl": -200
            }
        }

        order_data = {
            "symbol": "EURUSD",
            "type": "BUY",
            "entry_zone": [1.1000, 1.1010],
            "sl": 1.0950,
            "tp": [1.1050]
        }

        with patch.object(ea_bridge.config_manager, 'get_user_config', new_callable=AsyncMock) as mock_config:
            mock_config.return_value = {
                "max_open_positions": 5,
                "max_exposure": 10000,
                "max_daily_drawdown_pct": 5.0
            }

            valid, message = await ea_bridge.validate_user_risk_limits(telegram_id, order_data)

            assert valid is True
            assert message == "Risk check passed"

    @pytest.mark.asyncio
    async def test_position_manager_user_tracking(self, position_manager):
        """Test user-specific position tracking."""
        telegram_id = 12345

        # Initialize user tracking
        result = await position_manager.initialize_user_tracking(telegram_id)
        assert result is True

        # Check user data structures
        assert telegram_id in position_manager._user_positions
        assert telegram_id in position_manager._user_position_history
        assert telegram_id in position_manager._user_risk_metrics

    @pytest.mark.asyncio
    async def test_position_manager_user_isolation(self, position_manager):
        """Test position data isolation between users."""
        user1_id = 12345
        user2_id = 67890

        # Initialize both users
        await position_manager.initialize_user_tracking(user1_id)
        await position_manager.initialize_user_tracking(user2_id)

        # Mock different positions for each user
        position_manager._user_positions[user1_id] = {"ticket1": Mock()}
        position_manager._user_positions[user2_id] = {"ticket2": Mock()}

        # Test isolation
        user1_positions = await position_manager.get_user_positions(user1_id)
        user2_positions = await position_manager.get_user_positions(user2_id)

        assert len(user1_positions) == 1
        assert len(user2_positions) == 1
        assert user1_positions != user2_positions

    @pytest.mark.asyncio
    async def test_order_manager_user_routing(self, order_manager):
        """Test user-specific order routing."""
        telegram_id = 12345
        order_data = {
            "order_id": "test_order_123",
            "symbol": "EURUSD",
            "type": "BUY",
            "entry_zone": [1.1000, 1.1010],
            "sl": 1.0950,
            "tp": [1.1050]
        }

        with patch.object(order_manager.ea_bridge, 'send_order_with_risk_check', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"success": True, "order_id": "test_order_123"}

            result = await order_manager.submit_order(telegram_id, order_data)

            assert result["success"] is True
            assert result["order_id"] == "test_order_123"

    @pytest.mark.asyncio
    async def test_order_manager_user_validation(self, order_manager):
        """Test order validation for users."""
        telegram_id = 12345
        order_data = {
            "symbol": "EURUSD",
            "type": "BUY",
            "entry_zone": [1.1000, 1.1010],
            "sl": 1.0950,
            "tp": [1.1050]
        }

        with patch.object(order_manager, '_validate_user_order_access', new_callable=AsyncMock) as mock_access:
            mock_access.return_value = True

            with patch.object(order_manager, '_validate_symbol_access', new_callable=AsyncMock) as mock_symbol:
                mock_symbol.return_value = True

                validation = await order_manager._validate_order_pre_execution(telegram_id, order_data)

                assert validation["valid"] is True

    @pytest.mark.asyncio
    async def test_multi_user_service_integration(self, multi_user_service):
        """Test complete multi-user service integration."""
        telegram_id = 12345

        # Test session initialization
        session_result = await multi_user_service.initialize_user_trading_session(telegram_id)
        assert session_result["success"] is True

        # Test order submission
        order_data = {
            "symbol": "EURUSD",
            "type": "BUY",
            "entry_zone": [1.1000, 1.1010],
            "sl": 1.0950,
            "tp": [1.1050]
        }

        with patch.object(multi_user_service.order_manager, 'submit_order', new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = {"success": True, "order_id": "test_order"}

            order_result = await multi_user_service.submit_user_order(telegram_id, order_data)
            assert order_result["success"] is True

    @pytest.mark.asyncio
    async def test_multi_user_service_status(self, multi_user_service):
        """Test multi-user service status reporting."""
        telegram_id = 12345

        with patch.object(multi_user_service.position_manager, 'get_user_positions', new_callable=AsyncMock) as mock_pos:
            mock_pos.return_value = []

            with patch.object(multi_user_service.position_manager, 'get_user_risk_metrics', new_callable=AsyncMock) as mock_risk:
                mock_risk.return_value = {"total_exposure": 0, "total_pnl": 0}

                with patch.object(multi_user_service.order_manager, 'get_user_pending_orders', new_callable=AsyncMock) as mock_orders:
                    mock_orders.return_value = []

                    with patch.object(multi_user_service.order_manager, 'get_user_order_history', new_callable=AsyncMock) as mock_history:
                        mock_history.return_value = []

                        status = await multi_user_service.get_user_trading_status(telegram_id)

                        assert "positions" in status
                        assert "risk_metrics" in status
                        assert "pending_orders" in status
                        assert "recent_orders" in status

    @pytest.mark.asyncio
    async def test_emergency_user_stop(self, multi_user_service):
        """Test emergency stop functionality for users."""
        telegram_id = 12345

        with patch.object(multi_user_service.order_manager, 'emergency_cancel_all_user_orders', new_callable=AsyncMock) as mock_cancel:
            mock_cancel.return_value = {"success": True, "cancelled": 2}

            with patch.object(multi_user_service.position_manager, 'emergency_close_all_user_positions', new_callable=AsyncMock) as mock_close:
                mock_close.return_value = {"success": True, "closed": 1}

                with patch.object(multi_user_service.ea_bridge, 'cleanup_user_session', new_callable=AsyncMock) as mock_cleanup:
                    mock_cleanup.return_value = None

                    result = await multi_user_service.emergency_user_stop(telegram_id)

                    assert result["success"] is True
                    assert result["cancelled_orders"] == 2
                    assert result["closed_positions"] == 1

    @pytest.mark.asyncio
    async def test_service_stats_enhancement(self, multi_user_service):
        """Test enhanced service statistics."""
        with patch.object(multi_user_service.position_manager, 'get_manager_stats') as mock_pos_stats:
            mock_pos_stats.return_value = {"total_positions": 5}

            with patch.object(multi_user_service.order_manager, 'get_manager_stats') as mock_order_stats:
                mock_order_stats.return_value = {"total_orders": 10}

                with patch.object(multi_user_service.ea_bridge, 'get_all_user_connections_health') as mock_ea_stats:
                    mock_ea_stats.return_value = {"total_connections": 3}

                    stats = await multi_user_service.get_enhanced_service_stats()

                    assert "position_manager" in stats
                    assert "order_manager" in stats
                    assert "ea_bridge" in stats
                    assert stats["enhanced_features"]["user_isolation"] is True

    @pytest.mark.asyncio
    async def test_concurrent_user_operations(self, multi_user_service):
        """Test concurrent operations for multiple users."""
        user1_id = 12345
        user2_id = 67890

        # Initialize both users
        await multi_user_service.initialize_user_trading_session(user1_id)
        await multi_user_service.initialize_user_trading_session(user2_id)

        # Submit orders concurrently
        order_data = {
            "symbol": "EURUSD",
            "type": "BUY",
            "entry_zone": [1.1000, 1.1010],
            "sl": 1.0950,
            "tp": [1.1050]
        }

        with patch.object(multi_user_service.order_manager, 'submit_order', new_callable=AsyncMock) as mock_submit:
            mock_submit.side_effect = [
                {"success": True, "order_id": "test_order_12345"},
                {"success": True, "order_id": "test_order_67890"}
            ]

            # Execute concurrent operations
            task1 = multi_user_service.submit_user_order(user1_id, order_data)
            task2 = multi_user_service.submit_user_order(user2_id, order_data)

            result1, result2 = await asyncio.gather(task1, task2)

            assert result1["success"] is True
            assert result2["success"] is True
            assert result1 != result2  # Different order IDs

    @pytest.mark.asyncio
    async def test_user_data_cleanup(self, ea_bridge, position_manager, order_manager):
        """Test proper cleanup of user data."""
        telegram_id = 12345

        # Initialize user data
        ea_bridge._user_connections[telegram_id] = {"api_key": "test"}
        ea_bridge._user_positions[telegram_id] = {"ticket1": Mock()}
        position_manager._user_positions[telegram_id] = {"ticket1": Mock()}
        order_manager._user_orders[telegram_id] = {"order1": Mock()}

        # Cleanup
        await ea_bridge.cleanup_user_session(telegram_id)

        # Verify EA bridge cleanup (EA bridge only cleans its own data)
        assert telegram_id not in ea_bridge._user_connections
        assert telegram_id not in ea_bridge._user_positions

        # Note: Position manager and order manager would need their own cleanup methods
        # For this test, we verify the EA bridge cleanup works correctly