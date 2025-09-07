#!/usr/bin/env python3
"""
Test script for multi-user signal distribution system.
"""

import asyncio
import os
import sys
from typing import Any, Dict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.config import TelegramConfig
from src.services.multi_user_service import MultiUserService
from src.telegram_bot.core.trading_bot import TradingBot


async def test_signal_distribution():
    """Test the enhanced signal distribution system."""
    print("🧪 Testing Multi-User Signal Distribution System")
    print("=" * 50)

    # Create service instance
    service = MultiUserService("test_token")

    # Create mock telegram bot
    config = TelegramConfig(
        token="test_token", chat_id=123456789, webhook_url="", admin_ids=[123456789]
    )

    # Mock bot for testing
    class MockBot:
        def __init__(self):
            self.notification_manager = None

        async def get_bot_stats(self):
            return {"status": "mock", "users": 0}

        async def send_message(self, chat_id, message, **kwargs):
            print(f"📤 Mock sending message to {chat_id}: {message[:100]}...")
            return True

    mock_bot = MockBot()
    service.set_telegram_bot(mock_bot)

    # Start service
    print("🚀 Starting multi-user service...")
    await service.start()

    # Test signal data
    test_signal = {
        "symbol": "EURUSD",
        "bias": "BULLISH",
        "confidence": 75,
        "setups": [
            {
                "type": "BUY",
                "entry_zone": [1.0950, 1.0970],
                "sl": 1.0920,
                "tp": [1.1020, 1.1080],
                "notes": "Strong bullish momentum detected",
            }
        ],
        "analysis_data": {
            "technical_indicators": {
                "rsi": 65,
                "macd": "bullish",
                "moving_averages": "bullish_alignment",
            },
            "market_context": {
                "trend": "uptrend",
                "support_level": 1.0920,
                "resistance_level": 1.1080,
            },
        },
    }

    print("📊 Testing signal processing...")
    print(
        f"Signal: {test_signal['symbol']} - {test_signal['bias']} ({test_signal['confidence']}%)"
    )

    # Process signal
    result = await service.process_signal(test_signal)

    print("📈 Signal Processing Result:")
    print(f"  Success: {result['success']}")
    print(f"  Distributed to: {len(result['distributed_to'])} users")
    print(f"  Skipped: {len(result['skipped'])} users")
    print(f"  Execution results: {result['execution_results']}")

    if "distribution_plan" in result:
        plan = result["distribution_plan"]
        print("📋 Distribution Plan:")
        print(f"  Total users: {plan['total_users']}")
        print(f"  Immediate: {len(plan['immediate'])}")
        print(f"  Delayed: {len(plan['delayed'])}")
        print(f"  Batch: {len(plan['batch'])}")
        print(f"  Skipped: {len(plan['skipped'])}")

    # Get service stats
    print("\n📊 Service Statistics:")
    stats = await service.get_service_stats()
    print(f"  Status: {stats['service_status']}")
    print(f"  Active tasks: {stats['active_tasks']}")

    if "signal_stats" in stats:
        signal_stats = stats["signal_stats"]
        print(f"  Signals processed: {signal_stats['total_processed']}")
        print(f"  Signals distributed: {signal_stats['total_distributed']}")

    # Get detailed signal distribution stats
    print("\n📈 Detailed Signal Distribution Stats:")
    dist_stats = await service.get_signal_distribution_stats()
    if "error" not in dist_stats:
        print(
            f"  Distribution efficiency: {dist_stats.get('distribution_efficiency', 0):.1f}%"
        )
        print(f"  Queue status: {dist_stats.get('queue_status', {})}")
    else:
        print(f"  Error: {dist_stats['error']}")

    # Test batch processing
    print("\n📦 Testing batch signal processing...")
    batch_result = await service.force_process_batch_signals()
    print(f"  Batch processing result: {batch_result}")

    # Stop service
    print("\n🛑 Stopping multi-user service...")
    await service.stop()

    print("\n✅ Test completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_signal_distribution())
