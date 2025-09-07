"""
MT5 execution logic for trading operations.
"""

import glob
import os
import platform
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ....core.config import MT5Config
from ....core.logging import get_logger, log_error_with_context
from ...base_executor import BaseExecutor
from ...interfaces import PlatformType

logger = get_logger(__name__)

try:
    import MetaTrader5 as mt5

    _use_real_mt5 = True
    logger.info("Using real MetaTrader5 library")
except ImportError:
    _use_real_mt5 = False
    logger.warning("MetaTrader5 library not found, using mock implementation")

    # Create a comprehensive mock that matches the official MetaTrader5 interface
    class MockMT5:
        """Mock MetaTrader5 library that matches the official interface."""

        # Constants
        TIMEFRAME_M1 = 1
        TIMEFRAME_M5 = 5
        TIMEFRAME_M15 = 15
        TIMEFRAME_M30 = 30
        TIMEFRAME_H1 = 16385
        TIMEFRAME_H4 = 16388
        TIMEFRAME_D1 = 16408
        TIMEFRAME_W1 = 16408
        TIMEFRAME_MN1 = 16408

        # Order types
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1
        ORDER_TYPE_BUY_LIMIT = 2
        ORDER_TYPE_SELL_LIMIT = 3
        ORDER_TYPE_BUY_STOP = 4
        ORDER_TYPE_SELL_STOP = 5

        # Trade actions
        TRADE_ACTION_DEAL = 1
        TRADE_ACTION_PENDING = 5
        TRADE_ACTION_SLTP = 6
        TRADE_ACTION_MODIFY = 7
        TRADE_ACTION_REMOVE = 8

        # Order filling types
        ORDER_FILLING_FOK = 2
        ORDER_FILLING_IOC = 1
        ORDER_FILLING_RETURN = 0

        # Order time types
        ORDER_TIME_GTC = 0
        ORDER_TIME_DAY = 1
        ORDER_TIME_SPECIFIED = 2
        ORDER_TIME_SPECIFIED_DAY = 3

        # Return codes
        TRADE_RETCODE_DONE = 10009
        TRADE_RETCODE_REQUOTE = 10004
        TRADE_RETCODE_REJECT = 10018
        TRADE_RETCODE_CANCEL = 10013
        TRADE_RETCODE_PLACED = 10008
        TRADE_RETCODE_DONE_PARTIAL = 10010
        TRADE_RETCODE_ERROR = 10016

        def __init__(self):
            self._initialized = False
            self._logged_in = False
            self._last_error = 0
            self._mock_orders = {}
            self._mock_positions = {}
            self._order_counter = 1000
            self._position_counter = 2000

        def initialize(self):
            """Initialize connection to MT5 terminal."""
            self._initialized = True
            self._last_error = 0
            return True

        def login(self, login=None, password=None, server=None):
            """Login to MT5 account."""
            if not self._initialized:
                self._last_error = 10016
                return False
            self._logged_in = True
            self._last_error = 0
            return True

        def shutdown(self):
            """Shutdown connection to MT5 terminal."""
            self._initialized = False
            self._logged_in = False
            return True

        def version(self):
            """Get MT5 version (matches successful test pattern)."""
            return (5, 0, 5200)  # From successful test: Version: 5.0.5200

        def last_error(self):
            """Get last error code."""
            return self._last_error

        def account_info(self):
            """Get account information (matches successful test pattern)."""
            if not self._logged_in:
                return None
            return type(
                "MockAccountInfo",
                (),
                {
                    "login": 274056656,  # From successful test
                    "trade_mode": 0,
                    "name": "Standar",  # From successful test
                    "server": "Exness-MT5Trial6",  # From successful test
                    "currency": "USD",
                    "leverage": 2000,  # From successful test: 1:2000
                    "balance": 500.00,  # From successful test
                    "equity": 500.00,
                    "margin": 0.00,
                    "free_margin": 500.00,
                    "margin_level": 0.00,
                    "margin_call": 60.00,
                    "margin_stop_out": 0.00,
                    "profit": 0.00,
                    "credit": 0.00,
                    "company": "Exness Technologies Ltd",  # From successful test
                },
            )()

        def terminal_info(self):
            """Get terminal information (matches successful test pattern)."""
            if not self._initialized:
                return None
            return type(
                "MockTerminalInfo",
                (),
                {
                    "build": 5200,  # From successful test
                    "name": "MetaTrader 5 EXNESS",  # From successful test
                    "company": "Exness Technologies Ltd",
                    "language": "English",
                    "path": "C:\\Program Files\\MetaTrader 5 EXNES - BotX 15",
                    "data_path": "C:\\Users\\GEMBUL FOREVER\\AppData\\Roaming\\MetaQuotes\\Terminal\\E1839E56707D159F05C493AB73B62759",
                    "connected": True,
                    "dlls_allowed": False,  # From successful test
                    "trade_allowed": False,  # From successful test
                    "email_enabled": False,
                    "ftp_enabled": False,
                    "notifications_enabled": False,
                    "mqid": True,
                },
            )()

        def symbols_total(self, selected=None):
            """Get total number of symbols (matches successful test pattern)."""
            return 400  # From successful test

        def symbols_get(self, group=None, name=None, selector=None):
            """Get list of symbols (matches successful test pattern)."""
            # From successful test: USD symbols: 163, sample symbols included USDRUB, USDAED, etc.
            symbols = [
                "USDRUB",
                "USDAED",
                "USDAMD",
                "USDARS",
                "USDAZN",  # From test
                "EURUSD",
                "GBPUSD",
                "USDJPY",
                "XAUUSD",
                "USDCAD",
                "BTCUSD",
                "ETHUSD",
                "AUDUSD",
                "NZDUSD",
                "USDCHF",
            ]
            if group and "USD" in group:
                return [s for s in symbols if "USD" in s]
            return symbols

        def symbol_info(self, symbol):
            """Get symbol information (matches successful test pattern)."""
            # Set realistic values based on symbol type
            if "RUB" in symbol:
                bid, ask, digits = (
                    94.8257,
                    105.0286,
                    4,
                )  # From test: huge spread for USDRUB
            elif "JPY" in symbol:
                bid, ask, digits = 150.123, 150.125, 3
            elif "XAU" in symbol:
                bid, ask, digits = 2045.50, 2045.52, 2
            else:
                bid, ask, digits = 1.08450, 1.08452, 5

            return type(
                "MockSymbolInfo",
                (),
                {
                    "name": symbol,
                    "bid": bid,
                    "ask": ask,
                    "last": (bid + ask) / 2,
                    "volume": 1000,
                    "digits": digits,
                    "point": 10 ** (-digits),
                    "spread": int((ask - bid) * (10**digits)),
                    "trade_mode": 4,
                    "trade_stops_level": 10,
                    "trade_freeze_level": 0,
                    "volume_min": 0.01,
                    "volume_max": 100.0,
                    "volume_step": 0.01,
                    "visible": True,
                },
            )()

        def symbol_info_tick(self, symbol):
            """Get symbol tick information."""
            return type(
                "MockTick",
                (),
                {
                    "time": datetime.now(),
                    "bid": 1.2000,
                    "ask": 1.2002,
                    "last": 1.2001,
                    "volume": 1000,
                    "flags": 0,
                },
            )()

        def symbol_select(self, symbol, select):
            """Select/deselect symbol."""
            return True

        def market_book_add(self, symbol):
            """Add symbol to market book."""
            return True

        def market_book_get(self, symbol):
            """Get market book for symbol."""
            return []

        def market_book_release(self, symbol):
            """Release symbol from market book."""
            return True

        def copy_rates_from(self, symbol, timeframe, date_from, count):
            """Copy historical rates from date."""
            return []

        def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
            """Copy historical rates from position."""
            return []

        def copy_rates_range(self, symbol, timeframe, date_from, date_to):
            """Copy historical rates in range."""
            return []

        def copy_ticks_from(self, symbol, date_from, count):
            """Copy historical ticks from date."""
            return []

        def copy_ticks_range(self, symbol, date_from, date_to, flags):
            """Copy historical ticks in range."""
            return []

        def orders_total(self):
            """Get total number of orders."""
            return len(self._mock_orders)

        def orders_get(self, flags=0):
            """Get list of orders."""
            return list(self._mock_orders.values())

        def order_calc_margin(self, symbol, cmd, volume, price):
            """Calculate margin for order."""
            return type(
                "MockMarginResult",
                (),
                {"margin": 100.0, "retcode": self.TRADE_RETCODE_DONE},
            )()

        def order_calc_profit(self, symbol, cmd, volume, price, sl, tp):
            """Calculate profit for order."""
            return type(
                "MockProfitResult",
                (),
                {"profit": 50.0, "retcode": self.TRADE_RETCODE_DONE},
            )()

        def order_check(self, request):
            """Check order request."""
            return type(
                "MockCheckResult",
                (),
                {
                    "retcode": self.TRADE_RETCODE_DONE,
                    "comment": "Order check successful",
                    "balance": 10000.0,
                    "equity": 10000.0,
                    "margin": 100.0,
                    "margin_free": 9900.0,
                    "margin_level": 100.0,
                },
            )()

        def order_send(self, request):
            """Send order to MT5."""
            if not self._logged_in:
                self._last_error = 10016
                return type(
                    "MockOrderResult",
                    (),
                    {"retcode": 10016, "comment": "Not logged in"},
                )()

            # Create mock order
            order_id = self._order_counter
            self._order_counter += 1

            mock_order = type(
                "MockOrder",
                (),
                {
                    "order": order_id,
                    "retcode": self.TRADE_RETCODE_DONE,
                    "comment": "Order placed successfully",
                },
            )()

            # Store order
            self._mock_orders[order_id] = mock_order

            return mock_order

        def positions_total(self):
            """Get total number of positions."""
            return len(self._mock_positions)

        def positions_get(self, group="", strgroup=""):
            """Get list of positions."""
            return list(self._mock_positions.values())

        def history_orders_total(self, from_date=None, to_date=None):
            """Get total number of historical orders."""
            return 100

        def history_orders_get(
            self, group="last", offset=0, count=10000, extended=False
        ):
            """Get historical orders."""
            return []

        def history_deals_total(self, from_date=None, to_date=None):
            """Get total number of historical deals."""
            return 200

        def history_deals_get(self, group="last", offset=0, count=10000):
            """Get historical deals."""
            return []

    # Only use mock if real MT5 import failed
    if not _use_real_mt5:
        mt5 = MockMT5()

# Note: These imports are optional and may not be available in all setups
try:
    from ....core.config import TradingConfig
except ImportError:
    TradingConfig = None

try:
    from ....models.orders import Order
    from ....models.positions import Position
    from ....models.trades import Trade
except ImportError:
    Order = None
    Position = None
    Trade = None


class MT5Executor(BaseExecutor):
    """MT5 execution engine for automated trading."""

    def __init__(self, config: MT5Config):
        # Convert Pydantic config to dict for BaseExecutor
        config_dict = (
            config.model_dump() if hasattr(config, "model_dump") else config.__dict__
        )
        super().__init__(config_dict, PlatformType.MT5)
        self.config = config  # Keep original config object
        self.symbols_info = {}

    @property
    def platform_name(self) -> str:
        return "MetaTrader 5"

    def _get_mt5_paths_from_test(self) -> List[str]:
        """Get MT5 paths based on successful test patterns."""
        paths = []

        # Prioritize paths that worked in the test
        if platform.system() == "Windows":
            # From successful test: "C:/Program Files/MetaTrader 5 EXNES - BotX 15/terminal64.exe"
            test_paths = [
                "C:/Program Files/MetaTrader 5 EXNES - BotX 15/terminal64.exe",
                "C:\\Program Files\\MetaTrader 5 EXNES - BotX 15\\terminal64.exe",
                "C:/Program Files/MetaTrader 5 EXNESS/terminal64.exe",
                "C:\\Program Files\\MetaTrader 5 EXNESS\\terminal64.exe",
                "C:/Program Files (x86)/MetaTrader 5 EXNESS/terminal64.exe",
                "C:\\Program Files (x86)\\MetaTrader 5 EXNESS\\terminal64.exe",
                "C:/Program Files/MetaTrader 5/terminal64.exe",
                "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
                "C:/Program Files (x86)/MetaTrader 5/terminal64.exe",
                "C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe",
            ]

            # Add existing paths if they exist
            for path in test_paths:
                if os.path.exists(path):
                    paths.append(path)

            # Fallback to dynamic discovery
            paths.extend(self._find_mt5_installations())

        return list(dict.fromkeys(paths))  # Remove duplicates

    def _find_mt5_installations(self) -> List[str]:
        """Scan for MT5 installations on the system."""
        installations = []

        if platform.system() == "Windows":
            # Check Windows registry first
            try:
                import winreg

                registry_paths = [
                    r"SOFTWARE\MetaQuotes\MetaTrader 5",
                    r"SOFTWARE\WOW6432Node\MetaQuotes\MetaTrader 5",
                ]

                for path in registry_paths:
                    try:
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                        try:
                            i = 0
                            while True:
                                try:
                                    subkey_name = winreg.EnumKey(key, i)
                                    subkey = winreg.OpenKey(key, subkey_name)
                                    try:
                                        install_path = winreg.QueryValueEx(
                                            subkey, "Path"
                                        )[0]
                                        if os.path.exists(install_path):
                                            installations.append(install_path)
                                    finally:
                                        winreg.CloseKey(subkey)
                                    i += 1
                                except WindowsError:
                                    break
                        finally:
                            winreg.CloseKey(key)
                    except WindowsError:
                        pass
            except ImportError:
                pass

            # Check common installation paths
            common_paths = [
                os.path.expandvars("%ProgramFiles%\\MetaTrader 5"),
                os.path.expandvars("%ProgramFiles(x86)%\\MetaTrader 5"),
                os.path.expandvars("%LOCALAPPDATA%\\Programs\\MetaTrader 5"),
            ]

            for path in common_paths:
                if os.path.exists(path):
                    installations.append(path)

            # Check HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
            try:
                reg_keys = [
                    (
                        winreg.HKEY_LOCAL_MACHINE,
                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                    ),
                    (
                        winreg.HKEY_LOCAL_MACHINE,
                        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
                    ),
                    (
                        winreg.HKEY_CURRENT_USER,
                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                    ),
                ]

                for root_key, sub_key in reg_keys:
                    try:
                        with winreg.OpenKey(root_key, sub_key) as key:
                            for i in range(winreg.QueryInfoKey(key)[0]):
                                try:
                                    subkey_name = winreg.EnumKey(key, i)
                                    with winreg.OpenKey(key, subkey_name) as subkey:
                                        try:
                                            display_name = winreg.QueryValueEx(
                                                subkey, "DisplayName"
                                            )[0]
                                            if "MetaTrader" in display_name:
                                                install_location = winreg.QueryValueEx(
                                                    subkey, "InstallLocation"
                                                )[0]
                                                terminal_path = os.path.join(
                                                    install_location, "terminal64.exe"
                                                )
                                                if os.path.exists(terminal_path):
                                                    installations.append(terminal_path)
                                                    logger.info(
                                                        f"Found MT5 in registry: {terminal_path}"
                                                    )
                                        except FileNotFoundError:
                                            continue
                                except (OSError, FileNotFoundError):
                                    continue
                    except (OSError, FileNotFoundError):
                        continue
            except ImportError:
                logger.debug("winreg not available for registry scanning")
            except Exception as e:
                logger.debug(f"Registry scan failed: {e}")

            # File system scan as backup
            search_paths = [
                "C:\\Program Files\\MetaTrader*\\terminal64.exe",
                "C:\\Program Files (x86)\\MetaTrader*\\terminal64.exe",
                "C:\\Users\\*\\AppData\\Roaming\\MetaQuotes\\Terminal\\*\\terminal64.exe",
                "D:\\Program Files\\MetaTrader*\\terminal64.exe",
                "E:\\Program Files\\MetaTrader*\\terminal64.exe",
            ]

            for pattern in search_paths:
                try:
                    found_paths = glob.glob(pattern, recursive=True)
                    installations.extend(found_paths)
                except Exception as e:
                    logger.debug(f"Error scanning pattern {pattern}: {e}")

        elif platform.system() == "Darwin":  # macOS
            # Wine or other compatibility layers
            search_paths = [
                "/Applications/MetaTrader*.app/Contents/MacOS/terminal64",
                "~/.wine/drive_c/Program Files/MetaTrader*/terminal64.exe",
            ]
            for pattern in search_paths:
                installations.extend(glob.glob(os.path.expanduser(pattern)))

        # Remove duplicates while preserving order
        installations = list(dict.fromkeys(installations))

        logger.info(f"Found {len(installations)} MT5 installations: {installations}")
        return installations

    async def _connect_impl(self) -> bool:
        """Platform-specific connection implementation."""
        return await self._connect_internal()

    async def _connect_internal(self) -> bool:
        """Internal connection logic matching successful test patterns."""
        try:
            # Check platform compatibility first
            if platform.system() != "Windows":
                logger.warning(
                    f"Platform {platform.system()} detected. MT5 requires Windows or Wine."
                )
                # Continue anyway as we might be using mock implementation

            # Clean shutdown any existing connection
            try:
                if mt5.terminal_info() is not None:
                    logger.info("Cleaning up existing MT5 connection")
                    mt5.shutdown()
                    time.sleep(1)
            except:
                pass

            logger.info("Initializing MT5 connection...")

            # Try default initialization first (matches successful test pattern)
            if mt5.initialize():
                logger.info("MT5 initialized successfully with default settings")
                initialized = True
            else:
                error_code = mt5.last_error()
                logger.warning(f"Default MT5 initialization failed: {error_code}")

                # Try with custom paths (matches test pattern)
                paths_to_try = self._get_mt5_paths_from_test()

                initialized = False
                for path in paths_to_try:
                    logger.info(f"Trying MT5 path: {path}")
                    try:
                        if mt5.initialize(path=path):
                            logger.info(
                                f"MT5 initialized successfully with path: {path}"
                            )
                            initialized = True
                            break
                        else:
                            error = mt5.last_error()
                            logger.warning(f"Failed to initialize {path}: {error}")
                    except Exception as e:
                        logger.error(f"Error initializing {path}: {e}")
                        continue

                if not initialized:
                    logger.error("Failed to initialize MT5 with any known path")
                    return False

            # Verify MT5 version and terminal info (matches test pattern)
            try:
                version = mt5.version()
                logger.info(f"MT5 Version: {version}")

                terminal_info = mt5.terminal_info()
                if terminal_info:
                    logger.info(
                        f"Terminal: {terminal_info.name} Build: {terminal_info.build}"
                    )
                    logger.info(
                        f"Connected: {terminal_info.connected}, Trade Allowed: {terminal_info.trade_allowed}"
                    )
                else:
                    logger.warning("Could not get terminal info")
            except Exception as e:
                logger.error(f"Error getting MT5 info: {e}")

            # Handle login based on configuration (matches test pattern)
            if not self.config.is_configured:
                missing_fields = []
                if not self.config.login or self.config.login == 0:
                    missing_fields.append("login")
                if not self.config.password:
                    missing_fields.append("password")
                if not self.config.server:
                    missing_fields.append("server")

                logger.warning(
                    f"MT5 credentials not configured (missing: {', '.join(missing_fields)}). "
                    f"Using mock/demo mode. Update config/settings.yaml for live trading."
                )
                # Still try to get account info even without explicit login
                self.connected = True
                self.account_info = mt5.account_info()
                return True

            # Attempt login if credentials are provided (matches test pattern)
            if self.config.is_configured:
                logger.info(f"Attempting login with account: {self.config.login}")

                try:
                    success = mt5.login(
                        login=int(self.config.login),
                        password=self.config.password,
                        server=self.config.server,
                    )

                    if success:
                        logger.info("MT5 login successful")
                    else:
                        error_code = mt5.last_error()
                        logger.error(f"MT5 login failed: {error_code}")
                        # Don't fail completely - might be demo/mock mode

                except Exception as e:
                    logger.error(f"MT5 login error: {e}")
                    # Continue anyway for mock/demo mode

            # Verify connection with comprehensive checks
            if not self._verify_connection():
                logger.error("MT5 connection verification failed")
                mt5.shutdown()
                return False

            # Connection verified
            self.connected = True
            self.account_info = mt5.account_info()

            if self.account_info:
                logger.info(
                    f"Successfully connected to MT5. Account: {self.account_info.login}"
                )
                logger.info(
                    f"Balance: {self.account_info.balance}, Equity: {self.account_info.equity}"
                )
                logger.info(
                    f"Leverage: {self.account_info.leverage}, "
                    f"Margin Free: {self.account_info.margin_free}, "
                    f"Margin Level: {self.account_info.margin_level}%"
                )

            return True

        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            # Ensure clean shutdown on any error
            try:
                mt5.shutdown()
            except:
                pass
            return False

    def _verify_connection(self) -> bool:
        """Verify MT5 connection with comprehensive checks (matches test pattern)."""
        try:
            # 1. Check terminal info (matches test pattern)
            terminal_info = mt5.terminal_info()
            if not terminal_info:
                logger.error("Could not get terminal info")
                return False

            logger.info(
                f"Terminal: {terminal_info.name if hasattr(terminal_info, 'name') else 'Unknown'}"
            )
            logger.info(
                f"Connected: {terminal_info.connected if hasattr(terminal_info, 'connected') else 'Unknown'}"
            )

            # 2. Check account info (matches test pattern)
            account_info = mt5.account_info()
            if not account_info:
                logger.error("Could not get account info")
                return False

            logger.info(
                f"Account: {account_info.login if hasattr(account_info, 'login') else 'Unknown'}"
            )
            logger.info(
                f"Balance: {account_info.balance if hasattr(account_info, 'balance') else 'Unknown'}"
            )

            # 3. Test symbols info (matches test pattern)
            symbols_total = mt5.symbols_total()
            if symbols_total is None:
                logger.error("Could not get symbols total")
                return False
            logger.info(f"Total symbols: {symbols_total}")

            # 4. Test symbol availability (matches test pattern)
            symbols_available = mt5.symbols_total()
            if symbols_available is not None:
                logger.info(f"Available symbols: {symbols_available}")

            # 5. Test specific symbol info (use USDRUB from test)
            test_symbol = "USDRUB"  # From successful test
            symbol_info = mt5.symbol_info(test_symbol)
            if symbol_info:
                logger.info(f"Symbol {test_symbol} info available")
            else:
                logger.warning(f"Could not get {test_symbol} symbol info")
                # Try EURUSD as fallback
                symbol_info = mt5.symbol_info("EURUSD")
                if not symbol_info:
                    logger.error("Could not get any symbol info")
                    return False

            # 6. Check positions and orders (matches test pattern)
            positions = mt5.positions_total()
            orders = mt5.orders_total()
            logger.info(
                f"Open positions: {positions if positions is not None else 'Unknown'}"
            )
            logger.info(
                f"Pending orders: {orders if orders is not None else 'Unknown'}"
            )

            # 7. Check trading permissions (matches test pattern)
            if hasattr(terminal_info, "trade_allowed"):
                if not terminal_info.trade_allowed:
                    logger.warning(
                        "AutoTrading is disabled in MT5 - enable for live trading"
                    )
                    # Don't fail here as it's common in demo/test environments
                else:
                    logger.info("AutoTrading is enabled")

            logger.info("MT5 connection verification successful")
            return True

        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            return False

    async def connect(self) -> bool:
        """Connect to MT5 terminal using patterns from successful test."""
        return await self._connect_internal()

    async def disconnect(self) -> bool:
        """Disconnect from MT5 terminal."""
        try:
            if self.connected:
                mt5.shutdown()
                self.connected = False
                self.account_info = None
                logger.info("Disconnected from MT5")
                return True
            return True
        except Exception as e:
            logger.error(f"Error during MT5 disconnect: {e}")
            return False

    async def _place_order_impl(self, request) -> Dict:
        """Platform-specific order placement implementation."""
        if not self.connected:
            raise ConnectionError("Not connected to MT5")

        try:
            # Convert request to MT5 format
            mt5_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": request.symbol,
                "volume": request.amount,
                "type": (
                    mt5.ORDER_TYPE_BUY
                    if request.side.upper() == "BUY"
                    else mt5.ORDER_TYPE_SELL
                ),
                "price": request.price or 0,
                "sl": getattr(request, "stop_loss", 0) or 0,
                "tp": getattr(request, "take_profit", 0) or 0,
                "deviation": 10,
                "magic": 1001,
                "comment": f"AI_SIGNAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }

            # Send order
            result = mt5.order_send(mt5_request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = f"Order failed: {result.retcode} - {result.comment}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "retcode": result.retcode}

            logger.info(f"Order placed successfully: {result.order}")

            return {
                "success": True,
                "order_id": str(result.order),
                "symbol": request.symbol,
                "side": request.side,
                "type": request.type,
                "amount": request.amount,
                "price": request.price,
                "status": "FILLED",
                "retcode": result.retcode,
                "comment": result.comment,
            }

        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return {"success": False, "error": str(e)}

    async def place_order(self, order) -> Dict:
        """Place a new order in MT5 (legacy method)."""
        # Convert to request format and use new implementation
        request = type(
            "OrderRequest",
            (),
            {
                "symbol": (
                    order.instrument.symbol
                    if hasattr(order, "instrument")
                    else getattr(order, "symbol", "EURUSD")
                ),
                "side": order.order_type if hasattr(order, "order_type") else "BUY",
                "type": "market",
                "amount": order.volume if hasattr(order, "volume") else 0.01,
                "price": getattr(order, "price", None),
                "stop_loss": getattr(order, "stop_loss", None),
                "take_profit": getattr(order, "take_profit", None),
            },
        )()

        return await self._place_order_impl(request)

    async def modify_order(
        self, order_id: int, sl: Optional[float] = None, tp: Optional[float] = None
    ) -> Dict:
        """Modify an existing order."""
        if not self.connected:
            raise ConnectionError("Not connected to MT5")

        try:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "order": order_id,
                "symbol": self._get_order_symbol(order_id),
                "sl": sl,
                "tp": tp,
            }

            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = f"Order modification failed: {result.retcode}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "retcode": result.retcode}

            logger.info(f"Order modified successfully: {order_id}")
            return {"success": True, "retcode": result.retcode}

        except Exception as e:
            logger.error(f"Order modification error: {e}")
            return {"success": False, "error": str(e)}

    async def close_position(
        self, position_id: int, volume: Optional[float] = None
    ) -> Dict:
        """Close a position or partial close."""
        if not self.connected:
            raise ConnectionError("Not connected to MT5")

        try:
            position = mt5.positions_get(ticket=position_id)
            if not position:
                return {"success": False, "error": "Position not found"}

            pos = position[0]
            close_volume = volume if volume else pos.volume

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": position_id,
                "symbol": pos.symbol,
                "volume": close_volume,
                "type": (
                    mt5.ORDER_TYPE_SELL
                    if pos.type == mt5.POSITION_TYPE_BUY
                    else mt5.ORDER_TYPE_BUY
                ),
                "price": (
                    mt5.symbol_info_tick(pos.symbol).bid
                    if pos.type == mt5.POSITION_TYPE_BUY
                    else mt5.symbol_info_tick(pos.symbol).ask
                ),
                "deviation": self.config.execution["slippage_points"],
                "magic": self.config.execution["magic_number"],
                "comment": f"AI_CLOSE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = f"Position close failed: {result.retcode}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "retcode": result.retcode}

            logger.info(f"Position closed successfully: {position_id}")
            return {"success": True, "retcode": result.retcode}

        except Exception as e:
            logger.error(f"Position close error: {e}")
            return {"success": False, "error": str(e)}

    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open positions, optionally filtered by symbol."""
        if not self.connected:
            logger.warning("MT5 not connected")
            return []

        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()

            if positions is None:
                error_code = mt5.last_error()
                logger.error(f"Failed to get positions: {error_code}")
                return []

            result = []
            for pos in positions:
                position_data = {
                    "position_id": str(pos.ticket),
                    "symbol": pos.symbol,
                    "side": "BUY" if pos.type == 0 else "SELL",
                    "size": pos.volume,
                    "entry_price": pos.price_open,
                    "current_price": pos.price_current,
                    "unrealized_pnl": pos.profit,
                    "realized_pnl": 0.0,  # MT5 doesn't track this separately
                    "timestamp": datetime.fromtimestamp(
                        pos.time, timezone.utc
                    ).isoformat(),
                    "platform": self.platform_type.value,
                    # Legacy fields for backward compatibility
                    "type": "BUY" if pos.type == 0 else "SELL",
                    "volume": pos.volume,
                    "price_open": pos.price_open,
                    "price_current": pos.price_current,
                    "sl": pos.sl,
                    "profit": pos.profit,
                    "swap": pos.swap,
                    "time": pos.time,
                    "comment": pos.comment,
                }
                result.append(self.format_position_data(position_data))

            return result

        except Exception as e:
            log_error_with_context(e, {"operation": "get_positions", "symbol": symbol})
            return []

    async def get_orders(self) -> List[Dict]:
        """Get all pending orders from MT5."""
        if not self.connected:
            return []

        try:
            orders = mt5.orders_get()
            if orders is None:
                return []

            return [
                {
                    "ticket": order.ticket if hasattr(order, "ticket") else i,
                    "symbol": order.symbol if hasattr(order, "symbol") else "EURUSD",
                    "type": order.type if hasattr(order, "type") else "BUY",
                    "volume": order.volume if hasattr(order, "volume") else 0.01,
                    "price": order.price if hasattr(order, "price") else 1.2000,
                    "sl": order.sl if hasattr(order, "sl") else 0.0,
                    "tp": order.tp if hasattr(order, "tp") else 0.0,
                    "time": (
                        order.time
                        if hasattr(order, "time")
                        else int(datetime.now().timestamp())
                    ),
                }
                for i, order in enumerate(orders)
            ]

        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []

    def _prepare_order_request(self, order: Order) -> Dict:
        """Prepare MT5 order request from Order model."""
        symbol_info = mt5.symbol_info(order.instrument.symbol)
        if not symbol_info:
            raise ValueError(f"Symbol {order.instrument.symbol} not found")

        # Determine order type
        if order.order_type == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(order.instrument.symbol).ask
        elif order.order_type == "SELL":
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(order.instrument.symbol).bid
        elif order.order_type == "BUYLIMIT":
            order_type = mt5.ORDER_TYPE_BUY_LIMIT
            price = order.price
        elif order.order_type == "SELLLIMIT":
            order_type = mt5.ORDER_TYPE_SELL_LIMIT
            price = order.price
        elif order.order_type == "BUYSTOP":
            order_type = mt5.ORDER_TYPE_BUY_STOP
            price = order.price
        elif order.order_type == "SELLSTOP":
            order_type = mt5.ORDER_TYPE_SELL_STOP
            price = order.price
        else:
            raise ValueError(f"Unsupported order type: {order.order_type}")

        return {
            "action": (
                mt5.TRADE_ACTION_DEAL
                if order_type in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL]
                else mt5.TRADE_ACTION_PENDING
            ),
            "symbol": order.instrument.symbol,
            "volume": order.volume,
            "type": order_type,
            "price": price,
            "sl": order.stop_loss,
            "tp": order.take_profit,
            "deviation": self.config.execution["slippage_points"],
            "magic": self.config.execution["magic_number"],
            "comment": order.comment
            or f"AI_SIGNAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

    def _position_to_dict(self, position) -> Dict:
        """Convert MT5 position to dictionary."""
        return {
            "ticket": position.ticket,
            "symbol": position.symbol,
            "type": "BUY" if position.type == mt5.POSITION_TYPE_BUY else "SELL",
            "volume": position.volume,
            "price_open": position.price_open,
            "sl": position.sl,
            "tp": position.tp,
            "profit": position.profit,
            "swap": position.swap,
            "time": position.time,
        }

    def _order_to_dict(self, order) -> Dict:
        """Convert MT5 order to dictionary."""
        return {
            "ticket": order.ticket,
            "symbol": order.symbol,
            "type": order.type,
            "volume": order.volume,
            "price_open": order.price_open,
            "sl": order.sl,
            "tp": order.tp,
            "time_setup": order.time_setup,
        }

    def _get_order_symbol(self, order_id: int) -> str:
        """Get symbol for an order ID."""
        orders = mt5.orders_get(ticket=order_id)
        if orders:
            return orders[0].symbol
        return ""

    @property
    def is_connected(self) -> bool:
        """Check if connected to MT5."""
        return self.connected

    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        if not self.connected:
            return None

        try:
            account = mt5.account_info()
            if account:
                return {
                    "login": account.login,
                    "balance": account.balance,
                    "equity": account.equity,
                    "margin": account.margin,
                    "free_margin": getattr(
                        account, "margin_free", getattr(account, "free_margin", 0.0)
                    ),
                    "leverage": account.leverage,
                    "currency": account.currency,
                    "company": account.company,
                    "name": account.name,
                    "server": account.server,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    # Implement abstract methods from BaseExecutor
    async def test_connection(self) -> bool:
        """Test MT5 connection."""
        try:
            if not self.connected:
                return False
            # Try a simple operation
            terminal_info = mt5.terminal_info()
            return terminal_info is not None
        except:
            return False

    async def get_balance(self, asset: str = "USD") -> float:
        """Get account balance."""
        try:
            account_info = await self.get_account_info()
            if account_info:
                return float(account_info.get("balance", 0))
            return 0.0
        except:
            return 0.0

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        try:
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": int(order_id),
            }

            result = mt5.order_send(request)
            if result is None:
                error_code = mt5.last_error()
                return {"success": False, "error": f"MT5 error: {error_code}"}

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {"success": False, "error": f"Cancel failed: {result.retcode}"}

            return {"success": True, "order_id": order_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def modify_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Modify an order."""
        try:
            request = {
                "action": mt5.TRADE_ACTION_MODIFY,
                "order": int(order_id),
            }

            # Add modifiable fields
            if "price" in kwargs:
                request["price"] = float(kwargs["price"])
            if "sl" in kwargs:
                request["sl"] = float(kwargs["sl"])
            if "tp" in kwargs:
                request["tp"] = float(kwargs["tp"])

            result = mt5.order_send(request)
            if result is None:
                error_code = mt5.last_error()
                return {"success": False, "error": f"MT5 error: {error_code}"}

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {"success": False, "error": f"Modify failed: {result.retcode}"}

            return {"success": True, "order_id": order_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order details."""
        try:
            orders = mt5.orders_get(ticket=int(order_id))
            if orders and len(orders) > 0:
                order = orders[0]
                return self.format_order_data(
                    {
                        "id": str(order.ticket),
                        "symbol": order.symbol,
                        "side": "BUY" if order.type % 2 == 0 else "SELL",
                        "type": "LIMIT" if order.type in [2, 3, 4, 5] else "MARKET",
                        "amount": order.volume_initial,
                        "price": order.price_open,
                        "filled": order.volume_initial - order.volume_current,
                        "remaining": order.volume_current,
                        "status": "OPEN",
                        "timestamp": datetime.fromtimestamp(
                            order.time_setup, timezone.utc
                        ).isoformat(),
                    }
                )
            return None
        except Exception as e:
            log_error_with_context(e, {"operation": "get_order", "order_id": order_id})
            return None

    async def get_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all orders."""
        try:
            if symbol:
                orders = mt5.orders_get(symbol=symbol)
            else:
                orders = mt5.orders_get()

            if orders is None:
                return []

            result = []
            for order in orders:
                order_data = {
                    "id": str(order.ticket),
                    "symbol": order.symbol,
                    "side": "BUY" if order.type % 2 == 0 else "SELL",
                    "type": "LIMIT" if order.type in [2, 3, 4, 5] else "MARKET",
                    "amount": order.volume_initial,
                    "price": order.price_open,
                    "filled": order.volume_initial - order.volume_current,
                    "remaining": order.volume_current,
                    "status": "OPEN",
                    "timestamp": datetime.fromtimestamp(
                        order.time_setup, timezone.utc
                    ).isoformat(),
                }
                result.append(self.format_order_data(order_data))

            return result
        except Exception as e:
            log_error_with_context(e, {"operation": "get_orders", "symbol": symbol})
            return []

    async def close_position(
        self, position_id: str, volume: Optional[float] = None
    ) -> Dict[str, Any]:
        """Close position."""
        return await self.close_position_by_ticket(int(position_id))

    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information."""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None

            return {
                "symbol": symbol,
                "base_asset": symbol[:3],  # Approximation for forex pairs
                "quote_asset": symbol[3:],
                "status": "TRADING" if symbol_info.visible else "INACTIVE",
                "min_qty": symbol_info.volume_min,
                "max_qty": symbol_info.volume_max,
                "step_size": symbol_info.volume_step,
                "min_price": symbol_info.point,
                "tick_size": symbol_info.point,
                "platform": self.platform_type.value,
            }
        except Exception as e:
            log_error_with_context(
                e, {"operation": "get_symbol_info", "symbol": symbol}
            )
            return None

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current ticker data."""
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None

            return {
                "symbol": symbol,
                "price": tick.last,
                "bid": tick.bid,
                "ask": tick.ask,
                "volume": tick.volume,
                "change_24h": 0.0,  # Not available in MT5
                "change_percent_24h": 0.0,  # Not available in MT5
                "timestamp": int(tick.time * 1000),
                "platform": self.platform_type.value,
            }
        except Exception as e:
            log_error_with_context(e, {"operation": "get_ticker", "symbol": symbol})
            return None

    async def get_klines(
        self, symbol: str, timeframe: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical kline data."""
        try:
            # Map timeframe string to MT5 timeframe
            tf_map = {
                "1m": mt5.TIMEFRAME_M1,
                "5m": mt5.TIMEFRAME_M5,
                "15m": mt5.TIMEFRAME_M15,
                "30m": mt5.TIMEFRAME_M30,
                "1h": mt5.TIMEFRAME_H1,
                "4h": mt5.TIMEFRAME_H4,
                "1d": mt5.TIMEFRAME_D1,
            }

            mt5_timeframe = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, limit)

            if rates is None:
                return []

            result = []
            for rate in rates:
                result.append(
                    {
                        "timestamp": int(rate["time"] * 1000),
                        "open": float(rate["open"]),
                        "high": float(rate["high"]),
                        "low": float(rate["low"]),
                        "close": float(rate["close"]),
                        "volume": float(rate["tick_volume"]),
                    }
                )

            return result
        except Exception as e:
            log_error_with_context(e, {"operation": "get_klines", "symbol": symbol})
            return []
