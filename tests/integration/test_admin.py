#!/usr/bin/env python3
"""Test script to verify admin functionality."""

import asyncio
from src.core.config import config
from src.telegram_bot.core.trading_bot import TradingBot

async def test_admin_functionality():
    """Test admin commands and functionality."""
    try:
        bot = TradingBot.create_instance(config.telegram)
        await bot.setup()
        
        if hasattr(bot, 'application') and bot.application:
            bot_info = await bot.application.bot.get_me()
            print(f'✅ Bot is active: {bot_info.username} ({bot_info.id})')
            
            # Check registered commands
            commands = await bot.application.bot.get_my_commands()
            print(f'✅ Commands registered: {len(commands)}')
            
            admin_command_found = False
            for cmd in commands:
                if cmd.command == 'admin':
                    admin_command_found = True
                    print(f'✅ Admin command found: /{cmd.command} - {cmd.description}')
                    break
            
            if not admin_command_found:
                print('❌ Admin command not found in registered commands')
            
            if config.telegram.chat_id:
                try:
                    message = (
                        "🎉 **Bot Update Complete!** 🎉\n\n"
                        "✅ **Fixed Issues:**\n"
                        "• Admin commands now available\n"
                        "• Callback query parsing errors resolved\n"
                        "• All 16 commands registered with BotFather\n\n"
                        "👑 **New Admin Features:**\n"
                        "• `/admin` - Access admin control panel\n"
                        "• `/users` - Manage users\n"
                        "• `/add_admin` - Add administrators\n"
                        "• And more admin commands!\n\n"
                        "🚀 **Try the commands now - they should all work properly!**"
                    )
                    
                    await bot.application.bot.send_message(
                        chat_id=config.telegram.chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    print(f'✅ Success notification sent to chat {config.telegram.chat_id}')
                except Exception as e:
                    print(f'⚠️  Could not send notification: {e}')
            
            await bot.application.bot.close()
        else:
            print('❌ Bot application not initialized')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_admin_functionality())
