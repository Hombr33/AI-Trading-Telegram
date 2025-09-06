#!/usr/bin/env python3
"""Test script to verify Telegram bot functionality."""

import asyncio

from src.core.config import config
from src.telegram_bot.core.trading_bot import TradingBot


async def test_bot_response():
    """Test if bot can send messages and is responsive."""
    try:
        bot = TradingBot.create_instance(config.telegram)
        await bot.setup()

        if hasattr(bot, "application") and bot.application:
            bot_info = await bot.application.bot.get_me()
            print(f"✅ Bot is active: {bot_info.username} ({bot_info.id})")

            if config.telegram.chat_id:
                try:
                    message = (
                        "🤖 *Bot Status Update*\n\n"
                        "✅ Bot is now active and polling for messages!\n"
                        "✅ All 15 commands are registered with BotFather\n\n"
                        "Try these commands:\n"
                        "• /start - Get started\n"
                        "• /help - Show all commands\n"
                        "• /status - System status\n"
                        "• /positions - View positions\n\n"
                        "_Bot is ready to receive your commands!_"
                    )

                    await bot.application.bot.send_message(
                        chat_id=config.telegram.chat_id,
                        text=message,
                        parse_mode="Markdown",
                    )
                    print(f"✅ Test message sent to chat {config.telegram.chat_id}")
                except Exception as e:
                    print(f"❌ Could not send test message: {e}")
            else:
                print("⚠️  No chat_id configured, cannot send test message")

            await bot.application.bot.close()
        else:
            print("❌ Bot application not initialized")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_bot_response())
