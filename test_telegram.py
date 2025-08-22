#!/usr/bin/env python3
"""
Test script for Telegram bot functionality.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config import config
from src.core.logging import get_logger
from src.telegram_bot.bot import TelegramBot

logger = get_logger(__name__)


async def test_telegram_bot():
    """Test the Telegram bot functionality."""
    try:
        logger.info("Testing Telegram bot...")
        logger.info(f"Bot token: {config.telegram.bot_token[:10]}...")
        logger.info(f"Chat ID: {config.telegram.chat_id}")
        
        # Create bot instance
        bot = TelegramBot(config.telegram)
        
        # Test bot startup
        logger.info("Starting bot...")
        await bot.start()
        
        # Wait a bit
        await asyncio.sleep(5)
        
        # Test sending a message
        if config.telegram.chat_id:
            logger.info("Testing message sending...")
            success = await bot.send_message(
                config.telegram.chat_id,
                "🤖 **AI Trading Bot Test**\n\nThis is a test message to verify the bot is working correctly.\n\n✅ Bot is operational and ready for trading signals!"
            )
            
            if success:
                logger.info("✅ Test message sent successfully!")
            else:
                logger.error("❌ Failed to send test message")
        else:
            logger.warning("No chat ID configured, skipping message test")
        
        # Wait a bit more
        await asyncio.sleep(5)
        
        # Test bot shutdown
        logger.info("Stopping bot...")
        await bot.stop()
        
        logger.info("✅ Telegram bot test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Telegram bot test failed: {e}")
        raise


async def test_notifications():
    """Test notification functionality."""
    try:
        logger.info("Testing notification system...")
        
        from src.telegram_bot.notifications import NotificationManager
        
        # Create notification manager
        notif_manager = NotificationManager(config.telegram)
        
        # Start notification manager
        await notif_manager.start()
        
        # Test different notification types
        logger.info("Testing signal notification...")
        await notif_manager.send_signal_notification({
            "symbol": "XAUUSD",
            "bias": "BULLISH",
            "confidence": 85
        })
        
        logger.info("Testing position notification...")
        await notif_manager.send_position_notification({
            "symbol": "EURUSD",
            "type": "BUY",
            "volume": 0.1,
            "price_open": 1.0850,
            "profit": 25.50
        }, "opened")
        
        logger.info("Testing risk alert...")
        await notif_manager.send_risk_alert(
            "drawdown",
            "Daily drawdown approaching limit",
            {"current_dd": 4.2, "limit": 6.0}
        )
        
        logger.info("Testing performance notification...")
        await notif_manager.send_performance_notification({
            "total_trades": 45,
            "win_rate": 62.2,
            "total_pnl": 1250.75,
            "drawdown": 3.2
        })
        
        # Wait for notifications to process
        await asyncio.sleep(3)
        
        # Stop notification manager
        await notif_manager.stop()
        
        logger.info("✅ Notification system test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Notification system test failed: {e}")
        raise


async def main():
    """Main test function."""
    try:
        logger.info("🚀 Starting Telegram bot tests...")
        
        # Test notifications first
        await test_notifications()
        
        # Test bot functionality
        await test_telegram_bot()
        
        logger.info("🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
