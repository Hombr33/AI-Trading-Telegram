#!/usr/bin/env python3
"""
Test script to verify the AI Trading Bot setup.
"""

import sys
import traceback


def test_imports():
    """Test critical imports."""
    try:
        print("Testing core imports...")
        from src.core.config import config
        from src.core.logging import get_logger

        print("✅ Core imports successful")

        print("Testing execution modules...")
        from src.execution.mt5_executor import MT5Executor
        from src.execution.aiomql_executor import AioMQLExecutor

        print("✅ Execution modules successful")

        print("Testing telegram bot...")
        from src.telegram_bot.core.trading_bot import TradingBot

        print("✅ Telegram bot imports successful")

        print("Testing handlers...")
        from src.telegram_bot.handlers.command_handler import setup_command_handlers
        from src.telegram_bot.handlers.callback_handler import setup_callback_handler
        from src.telegram_bot.handlers.message_handler import setup_message_handler
        from src.telegram_bot.handlers.error_handler import setup_error_handler

        print("✅ Handler setup functions successful")

        return True

    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration loading."""
    try:
        from src.core.config import config

        print(f"Environment: {config.environment}")
        print(f"Debug mode: {config.debug}")
        print(f"MT5 configured: {config.mt5.is_configured}")
        print(f"Telegram token configured: {bool(config.telegram.bot_token)}")
        print("✅ Configuration test successful")

        return True

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        traceback.print_exc()
        return False


def test_executor_creation():
    """Test executor creation."""
    try:
        from src.execution.aiomql_executor import AioMQLExecutor
        from src.core.config import config

        executor = AioMQLExecutor(config.mt5)
        print(f"Executor created: {type(executor).__name__}")
        print(f"Connection status: {executor.is_connected}")
        print("✅ Executor creation successful")

        return True

    except Exception as e:
        print(f"❌ Executor creation error: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🤖 AI Trading Bot Setup Test")
    print("=" * 40)

    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Executor Creation Test", test_executor_creation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The setup looks good.")
        return 0
    else:
        print("⚠️ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
