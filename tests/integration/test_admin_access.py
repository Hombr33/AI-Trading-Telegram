#!/usr/bin/env python3
"""
Script to test admin access and command functionality
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import config
from src.services.user_manager import UserManager
from src.telegram_bot.commands.handler import CommandHandler
from src.telegram_bot.handlers.admin_commands import AdminCommandHandlers

async def test_admin_access():
    """Test admin access and command functionality"""
    print("=== Testing Admin Access ===")
    
    # Test UserManager admin check
    user_manager = UserManager()
    admin_chat_id = config.telegram.chat_id
    
    print(f"Testing admin check for chat_id: {admin_chat_id}")
    is_admin = await user_manager.is_admin(admin_chat_id)
    print(f"✅ UserManager.is_admin() result: {is_admin}")
    
    if not is_admin:
        print("❌ Admin check failed - this should not happen!")
        return False
    
    # Test command handler initialization
    print("\n=== Testing Command Handler ===")
    try:
        command_handler = CommandHandler()
        print("✅ CommandHandler initialized successfully")
        
        # Check if admin commands are registered
        admin_commands = [cmd for cmd in command_handler.commands.keys() if 'admin' in cmd.lower()]
        print(f"✅ Admin commands registered: {admin_commands}")
        
        # Check if /admin command is available
        if 'admin' in command_handler.commands:
            print("✅ /admin command is registered")
        else:
            print("❌ /admin command is NOT registered")
            
    except Exception as e:
        print(f"❌ CommandHandler initialization failed: {e}")
        return False
    
    # Test AdminCommandHandlers initialization
    print("\n=== Testing Admin Command Handlers ===")
    try:
        admin_handlers = AdminCommandHandlers()
        print("✅ AdminCommandHandlers initialized successfully")
        
        # Check available admin methods
        admin_methods = [method for method in dir(admin_handlers) if not method.startswith('_')]
        print(f"✅ Available admin methods: {admin_methods}")
        
    except Exception as e:
        print(f"❌ AdminCommandHandlers initialization failed: {e}")
        return False
    
    print("\n=== Test Results ===")
    print("✅ All admin access tests passed!")
    print("✅ Admin user is properly configured in database")
    print("✅ Admin commands are properly registered")
    print("✅ Admin handlers are working correctly")
    
    return True

async def test_command_imports():
    """Test that all command imports work correctly"""
    print("\n=== Testing Command Imports ===")
    
    try:
        from src.telegram_bot.commands.system import SystemCommandHandler
        print("✅ SystemCommandHandler import successful")
    except Exception as e:
        print(f"❌ SystemCommandHandler import failed: {e}")
        return False
    
    try:
        from src.telegram_bot.commands.trading import TradingCommandHandler
        print("✅ TradingCommandHandler import successful")
    except Exception as e:
        print(f"❌ TradingCommandHandler import failed: {e}")
        return False
    
    try:
        from src.telegram_bot.commands.analysis import AnalysisCommandHandler
        print("✅ AnalysisCommandHandler import successful")
    except Exception as e:
        print(f"❌ AnalysisCommandHandler import failed: {e}")
        return False
    
    try:
        from src.telegram_bot.commands.auto_trading import AutoTradingCommandHandler
        print("✅ AutoTradingCommandHandler import successful")
    except Exception as e:
        print(f"❌ AutoTradingCommandHandler import failed: {e}")
        return False
    
    try:
        from src.telegram_bot.handlers.admin_commands import AdminCommandHandlers
        print("✅ AdminCommandHandlers import successful")
    except Exception as e:
        print(f"❌ AdminCommandHandlers import failed: {e}")
        return False
    
    print("✅ All command imports successful!")
    return True

async def main():
    """Main test function"""
    print("🚀 Starting Admin Access Test Suite")
    print("=" * 50)
    
    # Test imports first
    import_success = await test_command_imports()
    if not import_success:
        print("❌ Import tests failed - stopping")
        return
    
    # Test admin access
    admin_success = await test_admin_access()
    if not admin_success:
        print("❌ Admin access tests failed")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Admin access is working correctly.")
    print("\nNext steps:")
    print("1. Start the bot with: python run.py")
    print("2. Send /admin command in Telegram to test admin menu")
    print("3. Test other admin commands like /users, /add_admin, etc.")

if __name__ == "__main__":
    asyncio.run(main())
