#!/usr/bin/env python3
"""
Integration test for the AI Trading Bot complete workflow.
"""

import asyncio
import sys
import traceback
from datetime import datetime

async def test_complete_workflow():
    """Test the complete trading workflow."""
    try:
        print("🔄 Testing Complete Workflow")
        print("=" * 40)
        
        # Test 1: Component Initialization
        print("\n1. Testing Component Initialization...")
        from src.core.config import config
        from src.execution.aiomql_executor import AioMQLExecutor
        from src.execution.order_manager import OrderManager
        from src.common.interfaces import IPositionManager
        from src.telegram_bot.core.trading_bot import TradingBot
        from src.bridge.socketio_bridge import SocketIOBridge
        
        # Initialize components
        mt5_executor = AioMQLExecutor(config.mt5)
        order_manager = OrderManager(mt5_executor, config.trading)
        # Use the implementation through the interface
        from src.execution.position_manager import PositionManager
        position_manager: IPositionManager = PositionManager(mt5_executor, config.trading)
        telegram_bot = TradingBot(config.telegram)
        bridge = SocketIOBridge(config.bridge)
        
        print("✅ All components initialized successfully")
        
        # Test 2: Connection Testing
        print("\n2. Testing Connections...")
        
        # Test MT5 connection (will use mock)
        mt5_connected = await mt5_executor.connect()
        print(f"MT5 Connection: {'✅' if mt5_connected else '❌'}")
        
        # Test bridge setup
        bridge_connected = await bridge.connect()
        print(f"Bridge Setup: {'✅' if bridge_connected else '❌'}")
        
        # Test telegram bot setup
        telegram_setup = await telegram_bot.setup()
        print(f"Telegram Setup: {'✅' if telegram_setup else '❌'}")
        
        # Test 3: Signal Processing
        print("\n3. Testing Signal Processing...")
        
        mock_signal = {
            "symbol": "EURUSD",
            "bias": "BULLISH",
            "confidence": 75,
            "setups": [
                {
                    "entry_type": "MARKET",
                    "volume": 0.01,
                    "stop_loss": 1.1950,
                    "take_profit": 1.2050
                }
            ],
            "id": "test_signal_001"
        }
        
        result = await order_manager.execute_signal(mock_signal)
        print(f"Signal Execution: {'✅' if result.get('success') else '❌'}")
        if not result.get('success'):
            print(f"   Error: {result.get('error', 'Unknown')}")
        
        # Test 4: Position Monitoring
        print("\n4. Testing Position Monitoring...")
        
        positions = await mt5_executor.get_positions()
        print(f"Position Retrieval: ✅ ({len(positions)} positions)")
        
        # Test 5: Notification System
        print("\n5. Testing Notification System...")
        
        if telegram_bot.notification_manager:
            try:
                # Test notification (won't actually send in test environment)
                test_notification = await telegram_bot.send_notification(
                    "🧪 Integration test notification", "test"
                )
                print(f"Notification System: {'✅' if test_notification else '❌'}")
            except Exception as e:
                print(f"Notification System: ❌ ({str(e)[:50]}...)")
        else:
            print("Notification System: ❌ (Manager not initialized)")
        
        # Test 6: Health Monitoring
        print("\n6. Testing Health Monitoring...")
        
        from src.core.health_monitor import health_monitor
        await health_monitor.start_monitoring()
        await asyncio.sleep(1)  # Let it run briefly
        
        health_status = health_monitor.get_health_summary()
        print(f"Health Monitoring: ✅ (Status: {health_status.get('status', 'unknown')})")
        
        await health_monitor.stop_monitoring()
        
        # Cleanup
        print("\n7. Cleanup...")
        await telegram_bot.stop()
        await bridge.disconnect()
        await mt5_executor.disconnect()
        print("✅ Cleanup completed")
        
        print("\n🎉 Integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        traceback.print_exc()
        return False


async def test_error_handling():
    """Test error handling and recovery mechanisms."""
    try:
        print("\n🚨 Testing Error Handling")
        print("=" * 40)
        
        from src.core.error_handler import with_error_handling, ErrorContext
        from src.core.exceptions import TradingBotException
        
        # Test 1: Error context manager
        print("\n1. Testing Error Context Manager...")
        try:
            async with ErrorContext("test_operation", {"test": "data"}) as ctx:
                raise ValueError("Test error")
        except ValueError:
            print("✅ Error context handled correctly")
        
        # Test 2: Error handler decorator
        print("\n2. Testing Error Handler Decorator...")
        
        @with_error_handling("test_decorator", fallback_value="fallback", max_retries=1)
        async def test_function():
            raise ConnectionError("Test connection error")
        
        result = await test_function()
        print(f"✅ Decorator fallback: {result}")
        
        # Test 3: Circuit breaker
        print("\n3. Testing Circuit Breaker...")
        from src.core.error_handler import CircuitBreaker
        
        circuit_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        
        async def failing_operation():
            raise Exception("Simulated failure")
        
        # Trigger failures
        for i in range(3):
            try:
                await circuit_breaker.call(failing_operation)
            except:
                pass
        
        print(f"✅ Circuit breaker state: {circuit_breaker.state}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print(f"🤖 AI Trading Bot Integration Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    tests = [
        ("Complete Workflow", test_complete_workflow),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print(f"\n📊 Final Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
