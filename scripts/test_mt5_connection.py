#!/usr/bin/env python3
"""
MT5 Connection Test Script
Tests MT5 connection with proper error handling and diagnostics.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_mt5_connection():
    """Test MT5 connection with detailed error reporting."""
    print("Testing MT5 Connection...")
    
    try:
        # Check if we're on Windows (MT5 only works on Windows)
        if sys.platform != "win32":
            print("❌ MT5 is only supported on Windows platform")
            print(f"Current platform: {sys.platform}")
            return False
            
        # Try to import MT5
        try:
            import MetaTrader5 as mt5
            print("✅ MetaTrader5 module imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import MetaTrader5 module: {e}")
            print("Install with: pip install MetaTrader5")
            return False
        
        # Initialize MT5
        print("Initializing MT5...")
        if not mt5.initialize():
            error_code = mt5.last_error()
            print(f"❌ MT5 initialization failed: {error_code}")
            
            # Provide specific error explanations
            error_messages = {
                -10004: "MT5 terminal not found. Please install MetaTrader 5.",
                -10005: "IPC timeout. MT5 terminal may not be running or is busy.",
                -10006: "IPC error. Check if MT5 terminal is accessible.",
                -10007: "Timeout waiting for MT5 terminal response.",
                -10008: "MT5 terminal is not responding.",
            }
            
            if error_code[0] in error_messages:
                print(f"Explanation: {error_messages[error_code[0]]}")
            
            if error_code[0] == -10005:
                print("\n🔧 Troubleshooting steps for IPC timeout:")
                print("1. Make sure MetaTrader 5 terminal is installed and running")
                print("2. Enable 'Allow automated trading' in MT5 Tools > Options > Expert Advisors")
                print("3. Close and restart MT5 terminal")
                print("4. Run MT5 as administrator if needed")
                print("5. Check if antivirus is blocking MT5 communication")
                
            return False
            
        print("✅ MT5 initialized successfully")
        
        # Get terminal info
        terminal_info = mt5.terminal_info()
        if terminal_info:
            print(f"✅ Terminal info retrieved:")
            print(f"   Version: {terminal_info.version}")
            print(f"   Build: {terminal_info.build}")
            print(f"   Path: {terminal_info.path}")
            print(f"   Data path: {terminal_info.data_path}")
            print(f"   Experts enabled: {terminal_info.dlls_allowed}")
            print(f"   Trade allowed: {terminal_info.trade_allowed}")
        
        # Check account info (if logged in)
        account_info = mt5.account_info()
        if account_info:
            print(f"✅ Account connected:")
            print(f"   Login: {account_info.login}")
            print(f"   Server: {account_info.server}")
            print(f"   Balance: {account_info.balance}")
            print(f"   Currency: {account_info.currency}")
        else:
            print("⚠️  No account connected (demo/live account login required for trading)")
        
        # Test symbol access
        symbols = mt5.symbols_get()
        if symbols:
            print(f"✅ Symbols available: {len(symbols)} symbols")
            print(f"   Sample symbols: {[s.name for s in symbols[:5]]}")
        else:
            print("⚠️  No symbols available")
        
        # Shutdown MT5
        mt5.shutdown()
        print("✅ MT5 connection test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during MT5 test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test MT5 configuration from environment."""
    print("\n" + "="*50)
    print("Testing MT5 Configuration...")
    
    try:
        from src.core.config import config
        
        print(f"MT5 Login: {'***' if config.mt5.login else 'Not set'}")
        print(f"MT5 Server: {config.mt5.server or 'Not set'}")
        print(f"MT5 Password: {'***' if config.mt5.password else 'Not set'}")
        print(f"MT5 Configured: {config.mt5.is_configured}")
        
        if not config.mt5.is_configured:
            print("\n⚠️  MT5 not configured. Set these environment variables:")
            print("   MT5_LOGIN=your_login")
            print("   MT5_PASSWORD=your_password") 
            print("   MT5_SERVER=your_server")
            
    except Exception as e:
        print(f"❌ Error reading MT5 config: {e}")

if __name__ == "__main__":
    success = test_mt5_connection()
    test_config()
    
    if success:
        print("\n🎉 MT5 connection test passed!")
        sys.exit(0)
    else:
        print("\n💥 MT5 connection test failed!")
        sys.exit(1)
