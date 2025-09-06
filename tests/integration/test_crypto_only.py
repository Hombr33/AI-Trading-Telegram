#!/usr/bin/env python3
"""
Cross-platform crypto-only test for Linux/macOS deployment.
"""

import asyncio
import platform
import sys
from datetime import datetime


async def test_crypto_only_setup():
    """Test crypto-only functionality without MT5 dependencies."""
    print(f"🐧 Cross-Platform Crypto Test")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print("=" * 50)

    try:
        # Test core imports (should work on any platform)
        print("\n1. Testing Core Imports...")
        from src.core.config import config
        from src.execution.platform_manager import PlatformManager

        print("   ✅ Core imports successful")

        # Test crypto executor imports
        print("\n2. Testing Crypto Executors...")
        from src.execution.crypto.binance_executor import BinanceExecutor
        from src.execution.crypto.bitget_executor import BitgetExecutor
        from src.execution.crypto.bybit_executor import BybitExecutor

        print("   ✅ Crypto executors imported successfully")

        # Test platform manager initialization
        print("\n3. Testing Platform Manager...")
        platform_manager = PlatformManager(config)
        available_platforms = platform_manager.get_available_platforms()
        print(f"   Available platforms: {available_platforms}")

        if not available_platforms:
            print("   ⚠️ No platforms configured (add API keys to .env)")
        else:
            print("   ✅ Platform manager initialized")

        # Test connections (will fail without API keys, but shouldn't crash)
        print("\n4. Testing Platform Connections...")
        connection_results = await platform_manager.connect_all()

        connected = [name for name, success in connection_results.items() if success]
        failed = [name for name, success in connection_results.items() if not success]

        if connected:
            print(f"   ✅ Connected: {connected}")
        if failed:
            print(f"   ⚠️ Failed (expected without API keys): {failed}")

        await platform_manager.disconnect_all()

        # Test symbol routing for crypto
        print("\n5. Testing Crypto Symbol Routing...")
        crypto_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]

        for symbol in crypto_symbols:
            selected_platform = platform_manager.get_platform_for_symbol(symbol)
            if selected_platform:
                print(f"   ✅ {symbol} -> {selected_platform}")
            else:
                print(f"   ⚠️ {symbol} -> No platform (configure API keys)")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_mt5_availability():
    """Test MT5 availability on current platform."""
    print(f"\n🔍 MT5 Availability Check")
    print("-" * 25)

    if sys.platform == "win32":
        print("   Platform: Windows ✅")
        try:
            import MetaTrader5

            print("   MetaTrader5: Available ✅")
        except ImportError:
            print("   MetaTrader5: Not installed ❌")

        try:
            import aiomql

            print("   AioMQL: Available ✅")
        except ImportError:
            print("   AioMQL: Not installed ❌")
    else:
        print(f"   Platform: {platform.system()} (MT5 not supported)")
        print("   MetaTrader5: Not available on this platform ❌")
        print("   AioMQL: Not available on this platform ❌")
        print("   💡 Use crypto exchanges for trading on Linux/macOS")

    return True


async def test_dependencies():
    """Test all required dependencies."""
    print(f"\n📦 Dependency Check")
    print("-" * 18)

    # Map package names to their import names
    required_deps = {
        "aiohttp": "aiohttp",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "pydantic": "pydantic",
        "python-telegram-bot": "telegram",
        "python-socketio": "socketio",
        "sqlalchemy": "sqlalchemy",
    }

    missing_deps = []

    for package_name, import_name in required_deps.items():
        try:
            __import__(import_name)
            print(f"   {package_name}: ✅")
        except ImportError:
            print(f"   {package_name}: ❌")
            missing_deps.append(package_name)

    if missing_deps:
        print(f"\n   ⚠️ Install missing: pip install {' '.join(missing_deps)}")
        return False
    else:
        print(f"\n   ✅ All core dependencies available")
        return True


async def main():
    """Run cross-platform compatibility tests."""
    print(f"🚀 AI Trading Bot - Cross-Platform Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    tests = [
        ("Dependencies", test_dependencies),
        ("MT5 Availability", test_mt5_availability),
        ("Crypto-Only Setup", test_crypto_only_setup),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")

    print(f"\n{'='*55}")
    print(f"📊 Results: {passed}/{total} tests passed")

    if sys.platform != "win32":
        print(f"\n🐧 Linux/macOS Deployment:")
        print(f"✅ Pure crypto trading supported")
        print(f"✅ No MT5 dependencies required")
        print(f"✅ Deploy anywhere: VPS, cloud, Docker")
        print(f"\n🔧 Setup:")
        print(f"1. pip install -r requirements.txt")
        print(f"2. Configure crypto API keys in .env")
        print(f"3. python run.py")
    else:
        print(f"\n🪟 Windows Deployment:")
        print(f"✅ Full functionality (MT5 + Crypto)")
        print(f"✅ Install: pip install -r requirements-windows.txt")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
