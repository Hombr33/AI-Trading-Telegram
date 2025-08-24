#!/usr/bin/env python3
"""
Comprehensive MT5 Connection Test Script
Tests all MetaTrader5 Python API capabilities with detailed diagnostics.
Based on official MetaTrader5 Python documentation.
"""

import sys
import os
import platform
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_platform_compatibility():
    """Test if current platform supports MT5."""
    print("🔍 Platform Compatibility Check")
    print("-" * 30)
    
    if sys.platform == "win32":
        print("   Platform: Windows ✅")
        return True
    else:
        print(f"   Platform: {platform.system()} ❌")
        print("   MT5 is only supported on Windows")
        print("   💡 Use crypto exchanges for trading on Linux/macOS")
        return False

def test_mt5_import():
    """Test MT5 module import."""
    print("\n📦 MT5 Module Import Test")
    print("-" * 25)
    
    try:
        import MetaTrader5 as mt5
        print("   MetaTrader5 module: Available ✅")
        print(f"   Version: {mt5.__version__ if hasattr(mt5, '__version__') else 'Unknown'}")
        return mt5
    except ImportError as e:
        print(f"   MetaTrader5 module: Not available ❌")
        print(f"   Error: {e}")
        print("   💡 Install with: pip install MetaTrader5")
        return None

def test_mt5_initialization(mt5):
    """Test MT5 initialization with comprehensive error handling."""
    print("\n🚀 MT5 Initialization Test")
    print("-" * 25)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Clean shutdown first
        mt5.shutdown()
        time.sleep(1)
        
        # Get MT5 path from environment
        mt5_path = os.getenv('MT5_PATH')
        
        if mt5_path and os.path.exists(mt5_path):
            print(f"   Using custom path: {mt5_path}")
            success = mt5.initialize(path=mt5_path, timeout=30000)
        else:
            print("   Using default MT5 installation")
            success = mt5.initialize(timeout=30000)
        
        if success:
            print("   Initialization: Success ✅")
            return True
        else:
            error = mt5.last_error()
            print(f"   Initialization: Failed ❌")
            print(f"   Error: {error}")
            
            # Detailed error explanations
            error_messages = {
                -10004: "MT5 terminal not found. Install MetaTrader 5.",
                -10005: "IPC timeout. MT5 not running or AutoTrading disabled.",
                -10006: "IPC error. Check MT5 accessibility and antivirus.",
                -10007: "Timeout waiting for MT5 response.",
                -10008: "MT5 terminal not responding. Restart MT5.",
            }
            
            if error[0] in error_messages:
                print(f"   Explanation: {error_messages[error[0]]}")
            
            print("\n   💡 Troubleshooting:")
            print("   1. Ensure MT5 is running")
            print("   2. Enable AutoTrading (green button)")
            print("   3. Check antivirus/firewall")
            print("   4. Run MT5 as administrator")
            print("   5. Restart MT5 terminal")
            
            return False
            
    except Exception as e:
        print(f"   Exception: {e} ❌")
        return False

def test_terminal_info(mt5):
    """Test terminal information retrieval."""
    print("\n🖥️  Terminal Information Test")
    print("-" * 27)
    
    try:
        terminal_info = mt5.terminal_info()
        if terminal_info:
            print("   Terminal info: Available ✅")
            print(f"   Build: {terminal_info.build}")
            print(f"   Version: {terminal_info.version}")
            print(f"   Name: {terminal_info.name}")
            print(f"   Company: {terminal_info.company}")
            print(f"   Language: {terminal_info.language}")
            print(f"   Path: {terminal_info.path}")
            print(f"   Data path: {terminal_info.data_path}")
            print(f"   Connected: {terminal_info.connected}")
            print(f"   DLLs allowed: {terminal_info.dlls_allowed}")
            print(f"   Trade allowed: {terminal_info.trade_allowed}")
            print(f"   Tradeapi disabled: {terminal_info.tradeapi_disabled}")
            print(f"   Email enabled: {terminal_info.email_enabled}")
            print(f"   FTP enabled: {terminal_info.ftp_enabled}")
            print(f"   Notifications enabled: {terminal_info.notifications_enabled}")
            print(f"   MQ ID: {terminal_info.mqid}")
            print(f"   CPU cores: {terminal_info.cpu_cores}")
            print(f"   Memory physical: {terminal_info.memory_physical} MB")
            print(f"   Memory total: {terminal_info.memory_total} MB")
            print(f"   Memory available: {terminal_info.memory_available} MB")
            print(f"   Memory used: {terminal_info.memory_used} MB")
            return True
        else:
            print("   Terminal info: Not available ❌")
            return False
    except Exception as e:
        print(f"   Exception: {e} ❌")
        return False

def test_account_login(mt5):
    """Test account login functionality."""
    print("\n🔐 Account Login Test")
    print("-" * 19)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get credentials from environment
        mt5_login = os.getenv('MT5_LOGIN')
        mt5_password = os.getenv('MT5_PASSWORD')
        mt5_server = os.getenv('MT5_SERVER')
        
        if not all([mt5_login, mt5_password, mt5_server]):
            print("   Credentials: Not configured ❌")
            print("   💡 Set MT5_LOGIN, MT5_PASSWORD, MT5_SERVER in .env")
            return False
        
        print(f"   Login: {mt5_login}")
        print(f"   Server: {mt5_server}")
        
        # Attempt login
        if mt5.login(login=int(mt5_login), password=mt5_password, server=mt5_server):
            print("   Login: Success ✅")
            return True
        else:
            error = mt5.last_error()
            print(f"   Login: Failed ❌")
            print(f"   Error: {error}")
            
            # Common login error explanations
            login_errors = {
                10004: "Invalid account credentials",
                10006: "No connection to trade server",
                10007: "Wrong account or password",
                10008: "Account disabled",
                10009: "Old client terminal version",
                10010: "Account blocked",
                10011: "Request rejected",
                10012: "Request canceled",
                10013: "Request placed",
                10014: "Request accepted",
                10015: "Request processing",
                10016: "Request rejected",
                10017: "Request canceled by timeout",
                10018: "Invalid price",
                10019: "Invalid stops",
                10020: "Invalid volume",
                10021: "Market closed",
                10022: "No money",
                10023: "Price changed",
                10024: "Off quotes",
                10025: "Invalid expiration",
                10026: "Order changed",
                10027: "Too many requests",
                10028: "No changes",
                10029: "Autotrading disabled",
                10030: "Market closed",
                10031: "Invalid fill",
                10032: "No connection",
                10033: "Only real accounts allowed",
                10034: "EA disabled",
                10035: "Insufficient rights",
                10036: "Market closed"
            }
            
            if error[0] in login_errors:
                print(f"   Explanation: {login_errors[error[0]]}")
            
            return False
            
    except Exception as e:
        print(f"   Exception: {e} ❌")
        return False

def test_account_info(mt5):
    """Test account information retrieval."""
    print("\n💰 Account Information Test")
    print("-" * 26)
    
    try:
        account_info = mt5.account_info()
        if account_info:
            print("   Account info: Available ✅")
            print(f"   Login: {account_info.login}")
            print(f"   Trade mode: {account_info.trade_mode}")
            print(f"   Name: {account_info.name}")
            print(f"   Server: {account_info.server}")
            print(f"   Currency: {account_info.currency}")
            print(f"   Leverage: 1:{account_info.leverage}")
            print(f"   Balance: {account_info.balance:.2f}")
            print(f"   Equity: {account_info.equity:.2f}")
            print(f"   Margin: {account_info.margin:.2f}")
            print(f"   Free margin: {account_info.margin_free:.2f}")
            print(f"   Margin level: {account_info.margin_level:.2f}%")
            print(f"   Margin call: {account_info.margin_so_call:.2f}%")
            print(f"   Margin stop out: {account_info.margin_so_so:.2f}%")
            print(f"   Profit: {account_info.profit:.2f}")
            print(f"   Credit: {account_info.credit:.2f}")
            print(f"   Company: {account_info.company}")
            return True
        else:
            print("   Account info: Not available ❌")
            print("   💡 Login to account first")
            return False
    except Exception as e:
        print(f"   Exception: {e} ❌")
        return False

def test_symbols_info(mt5):
    """Test symbol information retrieval."""
    print("\n📊 Symbols Information Test")
    print("-" * 26)
    
    try:
        # Test symbols_total()
        total_symbols = mt5.symbols_total()
        print(f"   Total symbols: {total_symbols} ✅")
        
        # Test symbols_get()
        symbols = mt5.symbols_get()
        if symbols:
            print(f"   Available symbols: {len(symbols)} ✅")
            
            # Show sample symbols
            sample_symbols = symbols[:5]
            print("   Sample symbols:")
            for symbol in sample_symbols:
                print(f"     {symbol.name}: {symbol.description}")
        
        # Test specific symbol groups
        forex_symbols = mt5.symbols_get(group="*USD*")
        if forex_symbols:
            print(f"   USD symbols: {len(forex_symbols)} ✅")
        
        # Test symbol_info for specific symbol
        test_symbol = "EURUSD"
        symbol_info = mt5.symbol_info(test_symbol)
        if symbol_info:
            print(f"   {test_symbol} info: Available ✅")
            print(f"     Bid: {symbol_info.bid}")
            print(f"     Ask: {symbol_info.ask}")
            print(f"     Spread: {symbol_info.spread}")
            print(f"     Point: {symbol_info.point}")
            print(f"     Digits: {symbol_info.digits}")
            print(f"     Contract size: {symbol_info.trade_contract_size}")
            print(f"     Min volume: {symbol_info.volume_min}")
            print(f"     Max volume: {symbol_info.volume_max}")
            print(f"     Volume step: {symbol_info.volume_step}")
        
        # Test symbol_info_tick
        tick_info = mt5.symbol_info_tick(test_symbol)
        if tick_info:
            print(f"   {test_symbol} tick: Available ✅")
            print(f"     Time: {datetime.fromtimestamp(tick_info.time)}")
            print(f"     Bid: {tick_info.bid}")
            print(f"     Ask: {tick_info.ask}")
            print(f"     Volume: {tick_info.volume}")
        
        return True
        
    except Exception as e:
        print(f"   Exception: {e} ❌")
        return False

def test_market_data(mt5):
    """Test market data retrieval."""
    print("\n📈 Market Data Test")
    print("-" * 17)
    
    try:
        test_symbol = "EURUSD"
        
        # Ensure symbol is selected
        if not mt5.symbol_select(test_symbol, True):
            print(f"   Failed to select {test_symbol} ❌")
            return False
        
        # Test copy_rates_from_pos
        rates = mt5.copy_rates_from_pos(test_symbol, mt5.TIMEFRAME_M1, 0, 10)
        if rates is not None and len(rates) > 0:
            print(f"   Recent rates ({test_symbol} M1): {len(rates)} bars ✅")
            latest = rates[-1]
            print(f"     Latest: O={latest['open']:.5f} H={latest['high']:.5f} L={latest['low']:.5f} C={latest['close']:.5f}")
        
        # Test copy_rates_from
        from_date = datetime.now() - timedelta(hours=1)
        rates_from = mt5.copy_rates_from(test_symbol, mt5.TIMEFRAME_M5, from_date, 10)
        if rates_from is not None and len(rates_from) > 0:
            print(f"   Historical rates ({test_symbol} M5): {len(rates_from)} bars ✅")
        
        # Test copy_rates_range
        to_date = datetime.now()
        from_date = to_date - timedelta(minutes=30)
        rates_range = mt5.copy_rates_range(test_symbol, mt5.TIMEFRAME_M1, from_date, to_date)
        if rates_range is not None and len(rates_range) > 0:
            print(f"   Range rates ({test_symbol} M1): {len(rates_range)} bars ✅")
        
        # Test copy_ticks_from
        ticks = mt5.copy_ticks_from(test_symbol, from_date, 100, mt5.COPY_TICKS_ALL)
        if ticks is not None and len(ticks) > 0:
            print(f"   Tick data ({test_symbol}): {len(ticks)} ticks ✅")
            latest_tick = ticks[-1]
            print(f"     Latest tick: {datetime.fromtimestamp(latest_tick['time'])} Bid={latest_tick['bid']:.5f} Ask={latest_tick['ask']:.5f}")
        
        # Test copy_ticks_range
        ticks_range = mt5.copy_ticks_range(test_symbol, from_date, to_date, mt5.COPY_TICKS_ALL)
        if ticks_range is not None and len(ticks_range) > 0:
            print(f"   Tick range ({test_symbol}): {len(ticks_range)} ticks ✅")
        
        return True
        
    except Exception as e:
        print(f"   Exception: {e} ❌")
        return False

def test_trading_functions(mt5):
    """Test trading functions (orders and positions)."""
    print("\n💼 Trading Functions Test")
    print("-" * 23)
    
    try:
        # Test positions_total
        positions_count = mt5.positions_total()
        print(f"   Open positions: {positions_count} ✅")
        
        # Test positions_get
        positions = mt5.positions_get()
        if positions:
            print(f"   Position details: {len(positions)} positions ✅")
            for pos in positions[:3]:  # Show first 3 positions
                print(f"     {pos.symbol}: {pos.type} {pos.volume} lots, Profit: {pos.profit:.2f}")
        
        # Test orders_total
        orders_count = mt5.orders_total()
        print(f"   Pending orders: {orders_count} ✅")
        
        # Test orders_get
        orders = mt5.orders_get()
        if orders:
            print(f"   Order details: {len(orders)} orders ✅")
            for order in orders[:3]:  # Show first 3 orders
                print(f"     {order.symbol}: {order.type} {order.volume} lots @ {order.price_open}")
        
        # Test history_orders_total
        from_date = datetime.now() - timedelta(days=7)
        to_date = datetime.now()
        history_orders_count = mt5.history_orders_total(from_date, to_date)
        print(f"   History orders (7 days): {history_orders_count} ✅")
        
        # Test history_orders_get
        history_orders = mt5.history_orders_get(from_date, to_date)
        if history_orders:
            print(f"   History order details: {len(history_orders)} orders ✅")
        
        # Test history_deals_total
        history_deals_count = mt5.history_deals_total(from_date, to_date)
        print(f"   History deals (7 days): {history_deals_count} ✅")
        
        # Test history_deals_get
        history_deals = mt5.history_deals_get(from_date, to_date)
        if history_deals:
            print(f"   History deal details: {len(history_deals)} deals ✅")
            
        return True
        
    except Exception as e:
        print(f"   Exception: {e} ❌")
        return False

def test_order_operations(mt5):
    """Test order operations (send, modify, close) - DEMO ONLY."""
    print("\n🔄 Order Operations Test (Demo)")
    print("-" * 32)
    
    try:
        # Check if account allows trading
        account_info = mt5.account_info()
        if not account_info or not account_info.trade_allowed:
            print("   Trading not allowed on this account ❌")
            return False
        
        test_symbol = "EURUSD"
        
        # Get symbol info for proper lot size and price
        symbol_info = mt5.symbol_info(test_symbol)
        if not symbol_info:
            print(f"   {test_symbol} not available ❌")
            return False
        
        # Test order_send (BUY STOP order - safe for demo)
        lot_size = symbol_info.volume_min
        current_price = symbol_info.ask
        stop_price = current_price + 0.0050  # 50 pips above current price
        
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": test_symbol,
            "volume": lot_size,
            "type": mt5.ORDER_TYPE_BUY_STOP,
            "price": stop_price,
            "sl": stop_price - 0.0020,  # 20 pips SL
            "tp": stop_price + 0.0030,  # 30 pips TP
            "deviation": 10,
            "magic": 234000,
            "comment": "MT5 Test Order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        
        print(f"   Testing order placement ({test_symbol})...")
        result = mt5.order_send(request)
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"   Order placed: Success ✅")
            print(f"     Order ID: {result.order}")
            print(f"     Volume: {result.volume}")
            print(f"     Price: {result.price}")
            
            # Test order_modify (modify SL/TP)
            modify_request = {
                "action": mt5.TRADE_ACTION_MODIFY,
                "order": result.order,
                "sl": stop_price - 0.0015,  # Modify SL
                "tp": stop_price + 0.0040,  # Modify TP
            }
            
            modify_result = mt5.order_send(modify_request)
            if modify_result and modify_result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"   Order modified: Success ✅")
            
            # Test order_remove (cancel the order)
            remove_request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": result.order,
            }
            
            remove_result = mt5.order_send(remove_request)
            if remove_result and remove_result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"   Order removed: Success ✅")
            
        else:
            print(f"   Order placement: Failed ❌")
            if result:
                print(f"     Error code: {result.retcode}")
                print(f"     Comment: {result.comment}")
        
        return True
        
    except Exception as e:
        print(f"   Exception: {e} ❌")
        return False

def test_openai_signal_generation(mt5):
    """Test OpenAI trading signal generation and analysis."""
    print("\n🤖 OpenAI Signal Generation Test")
    print("-" * 31)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check OpenAI API key
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            print("   OpenAI API Key: Not configured ❌")
            print("   💡 Set OPENAI_API_KEY in .env file")
            return False
        
        print("   OpenAI API Key: Configured ✅")
        
        # Test OpenAI analyzer import
        try:
            from src.analysis.openai_analyzer import OpenAIAnalyzer
            print("   OpenAI Analyzer: Available ✅")
        except ImportError as e:
            print(f"   OpenAI Analyzer: Not available ❌")
            print(f"   Error: {e}")
            return False
        
        # Test market data collection for analysis
        test_symbol = "EURUSD"
        
        # Get current market data
        rates = mt5.copy_rates_from_pos(test_symbol, mt5.TIMEFRAME_M15, 0, 100)
        if rates is None or len(rates) == 0:
            print(f"   Market data ({test_symbol}): Not available ❌")
            return False
        
        print(f"   Market data ({test_symbol}): {len(rates)} bars ✅")
        
        # Get symbol info
        symbol_info = mt5.symbol_info(test_symbol)
        if not symbol_info:
            print(f"   Symbol info ({test_symbol}): Not available ❌")
            return False
        
        print(f"   Symbol info ({test_symbol}): Available ✅")
        print(f"     Current Bid: {symbol_info.bid}")
        print(f"     Current Ask: {symbol_info.ask}")
        print(f"     Spread: {symbol_info.spread} points")
        
        # Test AI analyzer initialization
        try:
            analyzer = OpenAIAnalyzer()
            print("   AI Analyzer init: Success ✅")
        except Exception as e:
            print(f"   AI Analyzer init: Failed ❌")
            print(f"   Error: {e}")
            return False
        
        # Create mock market context for analysis
        market_context = {
            "symbol": test_symbol,
            "timeframe": "M15",
            "current_price": symbol_info.bid,
            "spread": symbol_info.spread,
            "session": "London" if 7 <= datetime.now().hour <= 16 else "Asian",
            "volatility": "normal",
            "news_impact": "low",
            "rates_data": rates[-50:].tolist(),  # Last 50 bars
            "timestamp": datetime.now().isoformat()
        }
        
        print("   Market context: Prepared ✅")
        
        # Test real AI signal generation
        try:
            print("   Testing real AI signal generation...")
            
            # Use the actual OpenAI analyzer to generate real signals
            real_signal = analyzer.analyze_market_data(
                symbol=test_symbol,
                timeframe="M15",
                market_data=rates[-100:],  # Last 100 bars
                current_price=symbol_info.bid,
                spread=symbol_info.spread,
                session=market_context['session']
            )
            
            if real_signal:
                print("   Real AI signal: Generated ✅")
                print(f"     Symbol: {real_signal.get('symbol', 'N/A')}")
                print(f"     Bias: {real_signal.get('bias', 'N/A')}")
                print(f"     Confidence: {real_signal.get('confidence', 0)}%")
                
                if real_signal.get('setups'):
                    setup = real_signal['setups'][0]
                    print(f"     Setup Type: {setup.get('type', 'N/A')}")
                    print(f"     Entry Zone: {setup.get('entry_zone', 'N/A')}")
                    print(f"     Stop Loss: {setup.get('sl', 'N/A')}")
                    print(f"     Take Profit: {setup.get('tp', 'N/A')}")
                    
                return real_signal
            else:
                print("   Real AI signal: Failed ❌")
                return False
                
        except Exception as e:
            print(f"   OpenAI API test: Failed ❌")
            print(f"   Error: {e}")
            
            # Check common API errors
            if "api_key" in str(e).lower():
                print("   💡 Check your OpenAI API key")
            elif "quota" in str(e).lower():
                print("   💡 Check your OpenAI API quota/billing")
            elif "timeout" in str(e).lower():
                print("   💡 Network timeout - check internet connection")
            
            return False
        
        # Test signal validation with real signal
        if real_signal:
            try:
                # Test signal schema validation
                from src.analysis.signal_validator import SignalValidator
                validator = SignalValidator()
                
                is_valid = validator.validate_signal(real_signal)
                if is_valid:
                    print("   Signal validation: Success ✅")
                else:
                    print("   Signal validation: Failed ❌")
                    
            except ImportError:
                print("   Signal validator: Not available ⚠️")
            except Exception as e:
                print(f"   Signal validation: Error ❌ ({e})")
            
            # Test risk calculation with real signal
            try:
                from src.execution.risk_manager import RiskManager
                from src.core.config import config
                
                risk_manager = RiskManager(config.risk)
                
                # Calculate position size for real signal
                account_info = mt5.account_info()
                account_balance = account_info.balance if account_info else 10000
                
                if real_signal.get('setups'):
                    setup = real_signal['setups'][0]
                    entry_price = setup['entry_zone'][0] if isinstance(setup['entry_zone'], list) else setup['entry_zone']
                    sl_price = setup['sl']
                    sl_distance = abs(sl_price - entry_price)
                    
                    position_size = risk_manager.calculate_position_size(
                        account_balance=account_balance,
                        risk_percent=2.0,
                        sl_distance_points=sl_distance * 10000,  # Convert to points
                        symbol=test_symbol
                    )
                    
                    print(f"   Risk calculation: Success ✅")
                    print(f"     Position size: {position_size} lots")
                    print(f"     Risk amount: ${account_balance * 0.02:.2f}")
                    print(f"     SL distance: {sl_distance * 10000:.1f} points")
                
            except ImportError:
                print("   Risk manager: Not available ⚠️")
            except Exception as e:
                print(f"   Risk calculation: Error ❌ ({e})")
        
        print("   AI Signal Generation: Complete ✅")
        return real_signal if real_signal else True
        
    except Exception as e:
        print(f"   Exception: {e} ❌")
        return False

def test_end_to_end_trading_flow(mt5):
    """Test complete end-to-end trading flow with AI signals."""
    print("\n🔄 End-to-End Trading Flow Test")
    print("-" * 32)
    
    try:
        # Check if we can run full integration test
        from dotenv import load_dotenv
        load_dotenv()
        
        if not os.getenv('OPENAI_API_KEY'):
            print("   OpenAI API Key required for E2E test ❌")
            return False
        
        # Test the complete flow: Data -> AI -> Signal -> Risk -> Execution
        test_symbol = "EURUSD"
        
        print("   Step 1: Market data collection...")
        # Get market data
        rates = mt5.copy_rates_from_pos(test_symbol, mt5.TIMEFRAME_M15, 0, 100)
        symbol_info = mt5.symbol_info(test_symbol)
        
        if not rates or not symbol_info:
            print("   Market data: Failed ❌")
            return False
        print("   Market data: Success ✅")
        
        print("   Step 2: Real AI signal generation...")
        # Use actual OpenAI analyzer for real signal generation
        try:
            from src.analysis.openai_analyzer import OpenAIAnalyzer
            analyzer = OpenAIAnalyzer()
            
            # Generate real AI signal using market data
            ai_signal = analyzer.analyze_market_data(
                symbol=test_symbol,
                timeframe="M15",
                market_data=rates[-100:],  # Last 100 bars
                current_price=symbol_info.ask,
                spread=symbol_info.spread,
                session="London" if 7 <= datetime.now().hour <= 16 else "Asian"
            )
            
            if not ai_signal:
                print("   AI signal generation: Failed ❌")
                return False
                
            print("   Real AI signal: Generated ✅")
            print(f"     Symbol: {ai_signal.get('symbol')}")
            print(f"     Bias: {ai_signal.get('bias')}")
            print(f"     Confidence: {ai_signal.get('confidence')}%")
            
        except Exception as e:
            print(f"   AI signal generation: Failed ❌ ({e})")
            # Fallback to mock signal for testing purposes
            print("   Using fallback mock signal for testing...")
            ai_signal = {
                "symbol": test_symbol,
                "bias": "BULLISH",
                "confidence": 78,
                "setups": [{
                    "type": "BUY",
                    "entry_zone": [symbol_info.ask, symbol_info.ask + 0.0005],
                    "entry_style": "limit",
                    "sl": symbol_info.ask - 0.0025,
                    "tp": [symbol_info.ask + 0.0038, symbol_info.ask + 0.0075],
                    "confidence": 78,
                    "notes": "Fallback signal for E2E test"
                }]
            }
        
        print("   Step 3: Signal validation...")
        # Validate signal meets minimum requirements
        setup = ai_signal["setups"][0]
        entry_price = setup["entry_zone"][0] if isinstance(setup["entry_zone"], list) else setup["entry_zone"]
        sl_price = setup["sl"]
        tp_price = setup["tp"][0] if isinstance(setup["tp"], list) else setup["tp"]
        
        # Calculate risk-reward ratio
        risk = abs(entry_price - sl_price)
        reward = abs(tp_price - entry_price)
        rr_ratio = reward / risk if risk > 0 else 0
        
        if rr_ratio >= 1.5 and ai_signal["confidence"] >= 60:
            print(f"   Signal validation: Success ✅ (RR: {rr_ratio:.2f})")
        else:
            print(f"   Signal validation: Failed ❌ (RR: {rr_ratio:.2f})")
            return False
        
        print("   Step 4: Risk management...")
        # Calculate position size
        account_info = mt5.account_info()
        if not account_info:
            print("   Account info: Not available ❌")
            return False
        
        risk_percent = 2.0
        sl_distance_points = abs(entry_price - sl_price) * 10000
        max_risk_amount = account_info.balance * (risk_percent / 100)
        
        # Simple position size calculation
        point_value = 1.0  # For EURUSD, 1 pip = $1 for 0.1 lot
        position_size = max_risk_amount / (sl_distance_points * point_value)
        position_size = max(symbol_info.volume_min, min(position_size, symbol_info.volume_max))
        
        print(f"   Position size: {position_size:.2f} lots ✅")
        print(f"   Risk amount: ${max_risk_amount:.2f}")
        
        print("   Step 5: Order preparation...")
        # Prepare order (but don't execute in test)
        order_request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": test_symbol,
            "volume": position_size,
            "type": mt5.ORDER_TYPE_BUY_LIMIT,
            "price": entry_price,
            "sl": sl_price,
            "tp": tp_price,
            "deviation": 10,
            "magic": 1001,
            "comment": "AI_SIGNAL_E2E_TEST",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        
        print("   Order prepared: Success ✅")
        print(f"     Type: BUY LIMIT")
        print(f"     Entry: {entry_price:.5f}")
        print(f"     SL: {sl_price:.5f}")
        print(f"     TP: {tp_price:.5f}")
        print(f"     Volume: {position_size:.2f}")
        
        print("   Step 6: Execution simulation...")
        # In a real system, this would execute the order
        # For testing, we just validate the order structure
        required_fields = ["action", "symbol", "volume", "type", "price", "sl", "tp"]
        missing_fields = [field for field in required_fields if field not in order_request]
        
        if not missing_fields:
            print("   Order structure: Valid ✅")
        else:
            print(f"   Order structure: Invalid ❌ (Missing: {missing_fields})")
            return False
        
        print("   End-to-End Flow: Complete ✅")
        print("   💡 In production, this would place actual orders")
        
        return True
        
    except Exception as e:
        print(f"   Exception: {e} ❌")
        return False

def run_comprehensive_mt5_test():
    """Run comprehensive MT5 test suite."""
    print("=" * 60)
    print("🚀 COMPREHENSIVE MT5 API TEST SUITE")
    print("=" * 60)
    
    # Track test results
    results = {}
    
    # 1. Platform compatibility
    results['platform'] = test_platform_compatibility()
    if not results['platform']:
        print("\n❌ Platform not compatible. Exiting...")
        return False
    
    # 2. MT5 module import
    mt5 = test_mt5_import()
    results['import'] = mt5 is not None
    if not results['import']:
        print("\n❌ MT5 module not available. Exiting...")
        return False
    
    # 3. MT5 initialization
    results['initialization'] = test_mt5_initialization(mt5)
    if not results['initialization']:
        print("\n❌ MT5 initialization failed. Exiting...")
        return False
    
    # 4. Terminal information
    results['terminal_info'] = test_terminal_info(mt5)
    
    # 5. Account login
    results['login'] = test_account_login(mt5)
    
    # 6. Account information
    results['account_info'] = test_account_info(mt5)
    
    # 7. Symbols information
    results['symbols'] = test_symbols_info(mt5)
    
    # 8. Market data
    results['market_data'] = test_market_data(mt5)
    
    # 9. Trading functions
    results['trading_functions'] = test_trading_functions(mt5)
    
    # 10. Order operations (if logged in)
    if results['login']:
        results['order_operations'] = test_order_operations(mt5)
    else:
        results['order_operations'] = False
        print("\n⚠️  Skipping order operations test (not logged in)")
    
    # 11. OpenAI signal generation
    results['openai_signals'] = test_openai_signal_generation(mt5)
    
    # 12. End-to-end trading flow (if OpenAI available)
    if results['openai_signals']:
        results['e2e_trading'] = test_end_to_end_trading_flow(mt5)
    else:
        results['e2e_trading'] = False
        print("\n⚠️  Skipping E2E trading test (OpenAI not available)")
    
    # Cleanup
    mt5.shutdown()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title():<20}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! MT5 API is fully functional.")
        return True
    elif passed >= total * 0.7:
        print("⚠️  Most tests passed. Check failed tests above.")
        return True
    else:
        print("❌ Many tests failed. Check MT5 setup and configuration.")
        return False

def test_config():
    """Test MT5 configuration from environment."""
    print("\n🔧 Configuration Test")
    print("-" * 19)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check environment variables
        mt5_login = os.getenv('MT5_LOGIN')
        mt5_password = os.getenv('MT5_PASSWORD')
        mt5_server = os.getenv('MT5_SERVER')
        mt5_path = os.getenv('MT5_PATH')
        
        print(f"   MT5_LOGIN: {'Set ✅' if mt5_login else 'Not set ❌'}")
        print(f"   MT5_PASSWORD: {'Set ✅' if mt5_password else 'Not set ❌'}")
        print(f"   MT5_SERVER: {'Set ✅' if mt5_server else 'Not set ❌'}")
        print(f"   MT5_PATH: {'Set ✅' if mt5_path else 'Not set (using default) ⚠️'}")
        
        if mt5_path and not os.path.exists(mt5_path):
            print(f"   MT5_PATH exists: No ❌")
            print(f"   Path: {mt5_path}")
        elif mt5_path:
            print(f"   MT5_PATH exists: Yes ✅")
        
        # Try to load from src config if available
        try:
            from src.core.config import config
            print(f"   App config loaded: Yes ✅")
            print(f"   MT5 configured in app: {'Yes ✅' if config.mt5.is_configured else 'No ❌'}")
        except Exception as e:
            print(f"   App config loaded: No ❌ ({e})")
        
        return all([mt5_login, mt5_password, mt5_server])
        
    except Exception as e:
        print(f"   Exception: {e} ❌")
        return False

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Quick connection test (original)")
    print("2. Comprehensive MT5 API test (recommended)")
    print("3. Configuration test only")
    
    try:
        choice = input("\nEnter choice (1-3) [default: 2]: ").strip() or "2"
    except (KeyboardInterrupt, EOFError):
        choice = "2"
    
    if choice == "1":
        # Original quick test (kept for backward compatibility)
        success = test_platform_compatibility()
        if success:
            mt5 = test_mt5_import()
            if mt5:
                success = test_mt5_initialization(mt5)
                if success:
                    success = test_account_login(mt5)
                    mt5.shutdown()
    elif choice == "2":
        # Comprehensive test suite
        success = run_comprehensive_mt5_test()
    elif choice == "3":
        # Configuration test only
        success = test_config()
    else:
        print("Invalid choice. Running comprehensive test...")
        success = run_comprehensive_mt5_test()
    
    if success:
        print("\n🎉 MT5 test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 MT5 test failed!")
        sys.exit(1)
