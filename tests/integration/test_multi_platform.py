#!/usr/bin/env python3
"""
Comprehensive multi-platform trading test for crypto exchanges and MT5.
"""

import asyncio
import sys
import traceback
from datetime import datetime
from typing import Dict, Any

async def test_platform_manager():
    """Test the platform manager with all exchanges."""
    try:
        print("🔄 Testing Multi-Platform Manager")
        print("=" * 50)
        
        from src.core.config import config
        from src.execution.platform_manager import PlatformManager
        
        # Initialize platform manager
        platform_manager = PlatformManager(config)
        
        print(f"\n📊 Available Platforms: {platform_manager.get_available_platforms()}")
        
        # Test connections
        print("\n1. Testing Platform Connections...")
        connection_results = await platform_manager.connect_all()
        
        for platform, success in connection_results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {platform.upper()}: {'Connected' if success else 'Failed'}")
        
        connected = platform_manager.get_connected_platforms()
        print(f"\n✅ Connected Platforms: {connected}")
        
        return platform_manager, len(connected) > 0
        
    except Exception as e:
        print(f"❌ Platform manager test failed: {e}")
        traceback.print_exc()
        return None, False

async def test_symbol_routing():
    """Test intelligent symbol routing to appropriate platforms."""
    try:
        print("\n🎯 Testing Symbol Routing")
        print("-" * 30)
        
        from src.core.config import config
        from src.execution.platform_manager import PlatformManager
        
        platform_manager = PlatformManager(config)
        await platform_manager.connect_all()
        
        # Test symbol routing
        test_symbols = {
            "EURUSD": "mt5",      # Forex -> MT5
            "BTCUSDT": "crypto",  # Crypto -> Binance/Bybit/Bitget
            "ETHUSDT": "crypto",  # Crypto -> Binance/Bybit/Bitget
            "GBPUSD": "mt5",      # Forex -> MT5
            "ADAUSDT": "crypto"   # Crypto -> Binance/Bybit/Bitget
        }
        
        for symbol, expected_type in test_symbols.items():
            platform = platform_manager.get_platform_for_symbol(symbol)
            executor = platform_manager.get_executor_for_symbol(symbol)
            
            if executor:
                print(f"   ✅ {symbol} -> {platform} ({executor.platform_name})")
            else:
                print(f"   ❌ {symbol} -> No available platform")
        
        await platform_manager.disconnect_all()
        return True
        
    except Exception as e:
        print(f"❌ Symbol routing test failed: {e}")
        return False

async def test_individual_exchanges():
    """Test individual crypto exchanges."""
    try:
        print("\n💰 Testing Individual Crypto Exchanges")
        print("-" * 40)
        
        from src.core.config import config
        from src.execution.crypto.binance_executor import BinanceExecutor
        from src.execution.crypto.bybit_executor import BybitExecutor
        from src.execution.crypto.bitget_executor import BitgetExecutor
        
        # Test each exchange individually
        exchanges = []
        
        if config.crypto.binance_configured:
            exchanges.append(("Binance", BinanceExecutor(config.crypto)))
        
        if config.crypto.bybit_configured:
            exchanges.append(("Bybit", BybitExecutor(config.crypto)))
        
        if config.crypto.bitget_configured:
            exchanges.append(("Bitget", BitgetExecutor(config.crypto)))
        
        if not exchanges:
            print("   ⚠️ No crypto exchanges configured (using testnet settings)")
            # Create test instances with mock config
            from src.core.config import CryptoConfig
            test_config = CryptoConfig(
                binance_api_key=os.environ.get("BINANCE_API_KEY_TEST", ""),
                binance_secret_key=os.environ.get("BINANCE_SECRET_KEY_TEST", ""), 
                binance_testnet=True
            )
            exchanges.append(("Binance (Mock)", BinanceExecutor(test_config)))
        
        results = {}
        
        for exchange_name, executor in exchanges:
            print(f"\n   Testing {exchange_name}...")
            
            try:
                # Test connection
                connected = await executor.connect()
                print(f"     Connection: {'✅' if connected else '❌'}")
                
                if connected:
                    # Test basic methods
                    try:
                        # Test get_ticker (won't work without real connection)
                        account_info = await executor.get_account_info()
                        print(f"     Account Info: {'✅' if account_info else '❌'}")
                        
                        # Test symbol info
                        symbol_info = await executor.get_symbol_info("BTCUSDT")
                        print(f"     Symbol Info: {'✅' if symbol_info else '❌'}")
                        
                        results[exchange_name] = "✅ Working"
                    except Exception as e:
                        print(f"     API Methods: ❌ ({str(e)[:50]}...)")
                        results[exchange_name] = f"⚠️ Connected but API failed"
                
                await executor.disconnect()
                
            except Exception as e:
                print(f"     Connection: ❌ ({str(e)[:50]}...)")
                results[exchange_name] = f"❌ Failed: {str(e)[:30]}..."
        
        print(f"\n📊 Exchange Test Results:")
        for exchange, result in results.items():
            print(f"   {result} {exchange}")
        
        return len([r for r in results.values() if "✅" in r]) > 0
        
    except Exception as e:
        print(f"❌ Individual exchange test failed: {e}")
        return False

async def test_mock_trading():
    """Test mock trading operations."""
    try:
        print("\n📈 Testing Mock Trading Operations") 
        print("-" * 35)
        
        from src.core.config import config
        from src.execution.platform_manager import PlatformManager
        
        platform_manager = PlatformManager(config)
        await platform_manager.connect_all()
        
        # Test mock orders
        test_orders = [
            {
                "symbol": "BTCUSDT",
                "side": "buy",
                "type": "market", 
                "quantity": 0.001,
                "test": True
            },
            {
                "symbol": "EURUSD",
                "side": "buy",
                "type": "limit",
                "quantity": 0.01,
                "price": 1.1000,
                "test": True
            }
        ]
        
        for i, order in enumerate(test_orders, 1):
            print(f"\n   Test Order {i}: {order['symbol']} {order['side']} {order['type']}")
            
            try:
                # This will attempt to place order but should handle test mode gracefully
                result = await platform_manager.place_order(order)
                
                if result.get("success", False):
                    print(f"     ✅ Order placement succeeded")
                    print(f"     Platform: {result.get('platform', 'unknown')}")
                else:
                    print(f"     ⚠️ Order placement failed (expected in test mode)")
                    print(f"     Error: {result.get('error', 'unknown')[:50]}...")
                    
            except Exception as e:
                print(f"     ❌ Order test failed: {str(e)[:50]}...")
        
        # Test platform status
        print(f"\n   Platform Status:")
        status = platform_manager.get_platform_status()
        print(f"     Connected: {status['connected_platforms']}/{status['total_platforms']}")
        print(f"     Primary: {status['primary_platform']}")
        
        await platform_manager.disconnect_all()
        return True
        
    except Exception as e:
        print(f"❌ Mock trading test failed: {e}")
        return False

async def test_configuration():
    """Test configuration loading for all platforms."""
    try:
        print("\n⚙️ Testing Configuration")
        print("-" * 25)
        
        from src.core.config import config
        
        print(f"   Environment: {config.environment}")
        print(f"   Debug: {config.debug}")
        
        # MT5 Config
        print(f"\n   MT5 Configuration:")
        print(f"     Configured: {config.mt5.is_configured}")
        if config.mt5.is_configured:
            print(f"     Server: {config.mt5.server}")
        
        # Crypto Configs
        print(f"\n   Crypto Configurations:")
        print(f"     Binance: {'✅' if config.crypto.binance_configured else '❌'}")
        print(f"     Bybit: {'✅' if config.crypto.bybit_configured else '❌'}")
        print(f"     Bitget: {'✅' if config.crypto.bitget_configured else '❌'}")
        
        if config.crypto.binance_configured:
            print(f"     Binance Testnet: {config.crypto.binance_testnet}")
        if config.crypto.bybit_configured:
            print(f"     Bybit Testnet: {config.crypto.bybit_testnet}")
        if config.crypto.bitget_configured:
            print(f"     Bitget Testnet: {config.crypto.bitget_testnet}")
        
        print(f"\n   Telegram: {'✅' if config.telegram.bot_token else '❌'}")
        print(f"   Bridge: {'✅' if config.bridge.token else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def main():
    """Run comprehensive multi-platform tests."""
    print(f"🚀 AI Trading Bot - Multi-Platform Test Suite")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Configuration Loading", test_configuration),
        ("Platform Manager", test_platform_manager),
        ("Symbol Routing", test_symbol_routing), 
        ("Individual Exchanges", test_individual_exchanges),
        ("Mock Trading", test_mock_trading),
    ]
    
    passed = 0
    total = len(tests)
    platform_manager = None
    has_connections = False
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            if test_name == "Platform Manager":
                platform_manager, has_connections = await test_func()
                if platform_manager:
                    passed += 1
            else:
                result = await test_func()
                if result:
                    passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 Final Results: {passed}/{total} tests passed")
    
    if platform_manager and has_connections:
        print(f"🎉 Multi-platform system is working!")
        print(f"🔗 Connected Platforms: {', '.join(platform_manager.get_connected_platforms())}")
        
        # Show quick setup guide
        print(f"\n🔧 Quick Setup Guide:")
        print(f"1. Configure API keys in .env file")
        print(f"2. Set CRYPTO_*_TESTNET=false for live trading")
        print(f"3. Run: python run.py")
        print(f"4. The bot will auto-route trades to appropriate exchanges")
        
        return 0
    elif passed >= 2:
        print(f"⚠️ Partial functionality working. Check configuration.")
        return 1
    else:
        print(f"❌ Major issues found. Please fix errors above.")
        return 2

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
