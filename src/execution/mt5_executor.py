"""
MT5 execution logic for trading operations.
"""

import time
import asyncio
import os
import glob
import platform
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from ..core.logging import (
    get_logger,
    log_error_with_context,
    log_system_event,
    log_trade_event,
    log_operation_timing
)
from ..core.error_handler import with_error_handling, ErrorContext
from ..core.exceptions import MT5ConnectionError, MT5ExecutionError
from ..core.config import MT5Config

logger = get_logger(__name__)

try:
    import MetaTrader5 as mt5

    logger.info("Using real MetaTrader5 library")
except ImportError:
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
            """Get MT5 version."""
            return "5.0.45"

        def last_error(self):
            """Get last error code."""
            return self._last_error

        def account_info(self):
            """Get account information."""
            if not self._logged_in:
                return None
            return type(
                "MockAccountInfo",
                (),
                {
                    "login": 12345,
                    "balance": 10000.0,
                    "equity": 10000.0,
                    "margin": 0.0,
                    "free_margin": 10000.0,
                    "leverage": 100,
                    "currency": "USD",
                    "company": "Mock Broker",
                    "name": "Mock Account",
                    "server": "Mock Server",
                },
            )()

        def terminal_info(self):
            """Get terminal information."""
            if not self._initialized:
                return None
            return type(
                "MockTerminalInfo",
                (),
                {
                    "name": "MetaTrader 5",
                    "version": "5.0.45",
                    "build": 1234,
                    "trade_mode": 4,
                    "connected": True,
                    "trade_allowed": True,
                    "expert_allowed": True,
                    "dlls_allowed": True,
                    "trade_timeout": 30000,
                },
            )()

        def symbols_total(self, selected=None):
            """Get total number of symbols."""
            return 1000

        def symbols_get(self, group=None, name=None, selector=None):
            """Get list of symbols."""
            return ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "USDCAD"]

        def symbol_info(self, symbol):
            """Get symbol information."""
            return type(
                "MockSymbolInfo",
                (),
                {
                    "name": symbol,
                    "bid": 1.2000,
                    "ask": 1.2002,
                    "last": 1.2001,
                    "volume": 1000,
                    "digits": 5,
                    "point": 0.00001,
                    "spread": 2,
                    "trade_mode": 4,
                    "trade_stops_level": 10,
                    "trade_freeze_level": 0,
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

    mt5 = MockMT5()

from ..core.config import TradingConfig
from ..models.orders import Order
from ..models.positions import Position
from ..models.trades import Trade


class MT5Executor:
    """MT5 execution engine for automated trading."""

    def __init__(self, config: MT5Config):
        self.config = config
        self.connected = False
        self.account_info = None
        self.symbols_info = {}

    def _find_mt5_installations(self) -> List[str]:
        """Scan for MT5 installations on the system."""
        installations = []
        
        if platform.system() == "Windows":
            # Check Windows registry first
            try:
                import winreg
                registry_paths = []
                
                # Check HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
                reg_keys = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
                ]
                
                for root_key, sub_key in reg_keys:
                    try:
                        with winreg.OpenKey(root_key, sub_key) as key:
                            for i in range(winreg.QueryInfoKey(key)[0]):
                                try:
                                    subkey_name = winreg.EnumKey(key, i)
                                    with winreg.OpenKey(key, subkey_name) as subkey:
                                        try:
                                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                            if "MetaTrader" in display_name:
                                                install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                                terminal_path = os.path.join(install_location, "terminal64.exe")
                                                if os.path.exists(terminal_path):
                                                    registry_paths.append(terminal_path)
                                                    logger.info(f"Found MT5 in registry: {terminal_path}")
                                        except FileNotFoundError:
                                            continue
                                except (OSError, FileNotFoundError):
                                    continue
                    except (OSError, FileNotFoundError):
                        continue
                
                installations.extend(registry_paths)
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
                "E:\\Program Files\\MetaTrader*\\terminal64.exe"
            ]
            
            for pattern in search_paths:
                try:
                    found_paths = glob.glob(pattern, recursive=True)
                    installations.extend(found_paths)
                except Exception as e:
                    logger.debug(f"Error scanning pattern {pattern}: {e}")
            
            # Remove duplicates while preserving order
            installations = list(dict.fromkeys(installations))
            
        elif platform.system() == "Darwin":  # macOS
            # Wine or other compatibility layers
            search_paths = [
                "/Applications/MetaTrader*.app/Contents/MacOS/terminal64",
                "~/.wine/drive_c/Program Files/MetaTrader*/terminal64.exe"
            ]
            for pattern in search_paths:
                installations.extend(glob.glob(os.path.expanduser(pattern)))
        
        logger.info(f"Found {len(installations)} MT5 installations: {installations}")
        return installations

    async def connect(self) -> bool:
        """Connect to MT5 terminal using simplified approach."""
        try:
            
            # First, try to initialize MT5 without specifying path (let MT5 find the default installation)
            logger.info("Initializing MT5 connection...")
            
            if not mt5.initialize():
                error_code = mt5.last_error()
                logger.warning(f"Default MT5 initialization failed: {error_code}")
                
                # Scan for MT5 installations dynamically
                logger.info("Scanning for MT5 installations...")
                paths_to_try = self._find_mt5_installations()
                
                if not paths_to_try:
                    logger.warning("No MT5 installations found, trying fallback paths")
                    paths_to_try = [
                        "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
                        "C:\\Program Files\\MetaTrader 5 EXNESS\\terminal64.exe",
                        "C:\\Program Files\\MetaTrader 5 IC Markets Global\\terminal64.exe",
                        "C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe"
                    ]
                
                initialized = False
                for path in paths_to_try:
                    logger.info(f"Trying MT5 path: {path}")
                    if mt5.initialize(path=path):
                        logger.info(f"MT5 initialized successfully with path: {path}")
                        initialized = True
                        break
                    else:
                        logger.warning(f"Failed to initialize with path {path}: {mt5.last_error()}")
                
                if not initialized:
                    logger.error("Failed to initialize MT5 with any known path")
                    return False
            else:
                logger.info("MT5 initialized successfully with default path")
            
            # Check if we need to login (skip if using mock or if credentials not provided)
            if not self.config.is_configured:
                logger.info("MT5 credentials not configured, using mock mode")
                self.connected = True
                self.account_info = mt5.account_info()
                return True
            
            # Wait briefly for terminal readiness
            await asyncio.sleep(2)
            
            # Attempt login with configured credentials
            logger.info(f"Attempting to login with account: {self.config.login}")
            
            max_attempts = self.config.retry_attempts
            retry_delay = self.config.retry_delay_ms / 1000  # Convert to seconds
            
            for attempt in range(max_attempts):
                try:
                    success = mt5.login(
                        login=int(self.config.login),
                        password=self.config.password,
                        server=self.config.server
                    )
                    
                    if success:
                        logger.info(f"MT5 login successful on attempt {attempt + 1}")
                        break
                    else:
                        error_code = mt5.last_error()
                        if attempt < max_attempts - 1:
                            logger.warning(f"MT5 login attempt {attempt + 1} failed (error: {error_code}), retrying in {retry_delay} seconds...")
                            await asyncio.sleep(retry_delay)
                        else:
                            logger.error(f"MT5 login failed after {max_attempts} attempts (error: {error_code})")
                            mt5.shutdown()
                            return False
                            
                except Exception as e:
                    logger.error(f"MT5 login error on attempt {attempt + 1}: {e}")
                    if attempt == max_attempts - 1:
                        mt5.shutdown()
                        return False
                    await asyncio.sleep(retry_delay)

            # Connection successful
            self.connected = True
            self.account_info = mt5.account_info()
            
            if self.account_info:
                logger.info(f"Successfully connected to MT5. Account: {self.account_info.login}")
                logger.info(f"Balance: {self.account_info.balance}, Equity: {self.account_info.equity}")
            else:
                logger.warning("Connected to MT5 but could not get account info")
                
            return True
            
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            # Ensure clean shutdown on any error
            try:
                mt5.shutdown()
            except:
                pass
            return False

    async def disconnect(self):
        """Disconnect from MT5 terminal."""
        try:
            if self.connected:
                mt5.shutdown()
                self.connected = False
                self.account_info = None
                logger.info("Disconnected from MT5")
        except Exception as e:
            logger.error(f"Error during MT5 disconnect: {e}")

    async def place_order(self, order: Order) -> Dict:
        """Place a new order in MT5."""
        if not self.connected:
            raise ConnectionError("Not connected to MT5")

        try:
            # Prepare order request
            request = self._prepare_order_request(order)

            # Send order
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = f"Order failed: {result.retcode} - {result.comment}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "retcode": result.retcode}

            logger.info(f"Order placed successfully: {result.order}")

            return {
                "success": True,
                "order": result.order,
                "retcode": result.retcode,
                "comment": result.comment,
            }

        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return {"success": False, "error": str(e)}

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

    async def get_positions(self) -> List[Dict]:
        """Get all open positions from MT5."""
        if not self.connected:
            return []

        try:
            positions = mt5.positions_get()
            if positions is None:
                return []

            return [
                {
                    "ticket": pos.ticket if hasattr(pos, "ticket") else i,
                    "symbol": pos.symbol if hasattr(pos, "symbol") else "EURUSD",
                    "type": pos.type if hasattr(pos, "type") else "BUY",
                    "volume": pos.volume if hasattr(pos, "volume") else 0.01,
                    "price_open": (
                        pos.price_open if hasattr(pos, "price_open") else 1.2000
                    ),
                    "price_current": (
                        pos.price_current if hasattr(pos, "price_current") else 1.2000
                    ),
                    "sl": pos.sl if hasattr(pos, "sl") else 0.0,
                    "tp": pos.tp if hasattr(pos, "tp") else 0.0,
                    "profit": pos.profit if hasattr(pos, "profit") else 0.0,
                    "swap": pos.swap if hasattr(pos, "swap") else 0.0,
                    "time": (
                        pos.time
                        if hasattr(pos, "time")
                        else int(datetime.now().timestamp())
                    ),
                }
                for i, pos in enumerate(positions)
            ]

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
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
                    "free_margin": account.free_margin,
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
