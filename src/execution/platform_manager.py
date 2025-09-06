"""Platform manager for multi-exchange trading support."""

from __future__ import annotations

import importlib
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from ..core.logging import get_logger, log_system_event, log_error_with_context
from ..core.error_handler import with_error_handling, ErrorContext
from ..common.interfaces import IExecutor, IPlatformManager, PlatformType

logger = get_logger(__name__)

# Define executor registry for dynamic loading
EXECUTOR_REGISTRY = {
    "binance": {
        "module": "src.execution.platforms.crypto.ccxt_executor",
        "class": "CCXTExecutor",
        "platform_type": PlatformType.BINANCE,
        "os_constraint": None,  # Available on all platforms
        "exchange_name": "binance",
    },
    "bybit": {
        "module": "src.execution.platforms.crypto.ccxt_executor",
        "class": "CCXTExecutor",
        "platform_type": PlatformType.BYBIT,
        "os_constraint": None,  # Available on all platforms
        "exchange_name": "bybit",
    },
    "bitget": {
        "module": "src.execution.platforms.crypto.ccxt_executor",
        "class": "CCXTExecutor",
        "platform_type": PlatformType.BITGET,
        "os_constraint": None,  # Available on all platforms
        "exchange_name": "bitget",
    },
    "mt5": {
        "module": "src.execution.platforms.forex.mt5_executor",
        "class": "MT5Executor",
        "platform_type": PlatformType.MT5,
        "os_constraint": "win32",  # Only available on Windows
        "default": True,  # Set as default platform
        "enabled": True,  # Explicitly enable MT5
    },
    "aiomql": {
        "module": "src.execution.platforms.forex.aiomql_executor",
        "class": "AioMQLExecutor",
        "platform_type": PlatformType.MT5,
        "os_constraint": "win32",  # Only available on Windows
    },
    "paper": {
        "module": "src.execution.platforms.simulation.paper_executor",
        "class": "PaperExecutor",
        "platform_type": PlatformType.PAPER,
        "os_constraint": None,  # Available on all platforms
        "fallback": True,  # Mark as fallback platform
    },
    "demo": {
        "module": "src.execution.platforms.simulation.demo_executor",
        "class": "DemoExecutor",
        "platform_type": PlatformType.DEMO,
        "os_constraint": None,  # Available on all platforms
        "fallback": True,  # Mark as fallback platform
    },
}


class PlatformManager(IPlatformManager):
    """Manages multiple trading platforms and routes orders intelligently.

    Implements the IPlatformManager interface to provide a standardized way to interact
    with various trading platforms, handling connections, disconnections, and routing
    orders to the appropriate platform based on symbol preferences.
    """

    def __init__(self, config):
        self.config = config
        self.platforms: Dict[str, IExecutor] = {}
        self.primary_platform: Optional[str] = None
        self.platform_preferences: Dict[str, str] = {}  # Symbol -> Platform mapping

        # Initialize available platforms
        self._initialize_platforms()

    def _initialize_platforms(self):
        """Initialize all configured trading platforms using dynamic loading."""
        # Initialize MT5/Forex platforms
        if self.config.mt5.is_configured:
            # Try AioMQL first, then fallback to MT5Executor
            self._load_executor("aiomql", self.config.mt5)

            # If AioMQL failed, try MT5Executor
            if "mt5" not in self.platforms:
                self._load_executor("mt5", self.config.mt5)

            # If still not loaded, log warning
            if "mt5" not in self.platforms:
                logger.warning("MT5 configured but not available on this platform")

        # Initialize Crypto platforms
        if self.config.crypto.binance_configured:
            self._load_executor("binance", self.config.crypto)

        if self.config.crypto.bybit_configured:
            self._load_executor("bybit", self.config.crypto)

        if self.config.crypto.bitget_configured:
            self._load_executor("bitget", self.config.crypto)

        # CRITICAL: If no real platforms loaded, automatically fall back to paper trading
        if not self.platforms:
            logger.warning(
                "No real trading platforms available, falling back to paper trading"
            )
            self._load_paper_trading_fallback()

        # Set platform preferences for different asset types
        self._setup_platform_preferences()

        # Log initialization summary
        if self.platforms:
            logger.info(
                f"Initialized {len(self.platforms)} trading platforms: {', '.join(self.platforms.keys())}"
            )
            logger.info(f"Primary platform: {self.primary_platform}")
        else:
            logger.warning(
                "No trading platforms initialized. Check your configuration."
            )

    def _load_paper_trading_fallback(self):
        """Load paper trading as fallback when no real platforms are available."""
        try:
            # Create paper trading configuration
            paper_config = {
                "enabled": True,
                "initial_balance": 100000.0,  # $100k paper account
                "trading_fees": 0.001,  # 0.1% default
                "use_live_data": True,  # Use live market data if available
                "data_source": "paper",  # Paper trading data source
                "max_leverage": 1.0,
                "slippage": 0.0001,  # 0.01% default slippage
                "execution_delay_ms": 100,
            }

            # Load paper executor
            if self._load_executor("paper", paper_config):
                logger.info("Paper trading fallback loaded successfully")
                # Set paper as primary platform
                self.primary_platform = "paper"

                # Also load demo executor as backup
                demo_config = {
                    "enabled": True,
                    "initial_balance": 50000.0,
                    "trading_fees": 0.001,
                    "use_live_data": False,
                    "data_source": "demo",
                }
                self._load_executor("demo", demo_config)

                logger.info("Paper trading fallback system ready for auto-trading")
            else:
                logger.error("Failed to load paper trading fallback")

        except Exception as e:
            logger.error(f"Error loading paper trading fallback: {e}")
            # Try demo executor as last resort
            try:
                demo_config = {"enabled": True, "initial_balance": 50000.0}
                self._load_executor("demo", demo_config)
                if "demo" in self.platforms:
                    self.primary_platform = "demo"
                    logger.info("Demo trading fallback loaded as last resort")
            except Exception as demo_error:
                logger.error(f"Failed to load demo trading fallback: {demo_error}")

    def _load_executor(self, executor_name: str, config) -> bool:
        """Dynamically load and initialize an executor.

        Args:
            executor_name: Name of the executor in the registry
            config: Configuration for the executor

        Returns:
            True if executor was loaded successfully, False otherwise
        """
        if executor_name not in EXECUTOR_REGISTRY:
            logger.warning(f"Unknown executor: {executor_name}")
            return False

        executor_info = EXECUTOR_REGISTRY[executor_name]

        # Check OS constraint
        if (
            executor_info["os_constraint"]
            and sys.platform != executor_info["os_constraint"]
        ):
            logger.info(f"{executor_name} not available on {sys.platform}")
            return False

        try:
            # Dynamically import the module and class
            module = importlib.import_module(executor_info["module"])
            executor_class = getattr(module, executor_info["class"])

            # Initialize the executor with exchange_name if it's a CCXT executor
            if "exchange_name" in executor_info:
                executor = executor_class(config, executor_info["exchange_name"])
            else:
                executor = executor_class(config)

            # Store the executor
            platform_name = executor_name if executor_name != "aiomql" else "mt5"
            self.platforms[platform_name] = executor

            # Set as primary platform if none set yet
            if not self.primary_platform:
                self.primary_platform = platform_name

            logger.info(f"Initialized {executor_info['class']}")
            return True

        except ImportError as e:
            logger.warning(f"Failed to import {executor_name} executor: {e}")
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize {executor_name} executor: {e}")
            return False

    def _setup_platform_preferences(self):
        """Setup default platform preferences for different symbols."""
        # Forex pairs -> MT5 (only if MT5 available)
        if "mt5" in self.platforms:
            forex_pairs = [
                "EURUSD",
                "GBPUSD",
                "USDJPY",
                "AUDUSD",
                "USDCAD",
                "USDCHF",
                "NZDUSD",
            ]
            for pair in forex_pairs:
                self.platform_preferences[pair] = "mt5"

        # Crypto pairs -> prefer order: Binance > Bybit > Bitget
        crypto_symbols = [
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT",
            "ADAUSDT",
            "DOTUSDT",
            "LINKUSDT",
        ]
        for symbol in crypto_symbols:
            if "binance" in self.platforms:
                self.platform_preferences[symbol] = "binance"
            elif "bybit" in self.platforms:
                self.platform_preferences[symbol] = "bybit"
            elif "bitget" in self.platforms:
                self.platform_preferences[symbol] = "bitget"

        # CRITICAL: If no real platforms available, use paper trading for all symbols
        if not any(
            platform in self.platforms
            for platform in ["mt5", "binance", "bybit", "bitget"]
        ):
            logger.info(
                "No real platforms available, using paper trading for all symbols"
            )

            # Set paper trading for all symbol types
            all_symbols = [
                # Forex
                "EURUSD",
                "GBPUSD",
                "USDJPY",
                "AUDUSD",
                "USDCAD",
                "USDCHF",
                "NZDUSD",
                # Crypto
                "BTCUSDT",
                "ETHUSDT",
                "BNBUSDT",
                "ADAUSDT",
                "DOTUSDT",
                "LINKUSDT",
                # Additional symbols
                "XAUUSD",
                "XAGUSD",
                "OILUSD",
                "SPX500",
                "NAS100",
                "GER30",
            ]

            for symbol in all_symbols:
                if "paper" in self.platforms:
                    self.platform_preferences[symbol] = "paper"
                elif "demo" in self.platforms:
                    self.platform_preferences[symbol] = "demo"

            logger.info(
                f"Paper trading fallback configured for {len(all_symbols)} symbols"
            )

        # If no platforms available, log warning
        if not self.platforms:
            logger.warning(
                "No trading platforms initialized. Check your configuration."
            )

    @with_error_handling("platform_manager_connect", notify_telegram=True)
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all configured platforms."""
        results = {}

        for platform_name, executor in self.platforms.items():
            try:
                async with ErrorContext(f"connect_{platform_name}") as ctx:
                    success = await executor.connect()
                    results[platform_name] = success

                    if success:
                        log_system_event(
                            "platform_manager",
                            "platform_connected",
                            f"Connected to {platform_name}",
                        )
                    else:
                        log_system_event(
                            "platform_manager",
                            "platform_failed",
                            f"Failed to connect to {platform_name}",
                        )
            except Exception as e:
                results[platform_name] = False
                log_error_with_context(
                    e, {"platform": platform_name, "operation": "connect"}
                )

        connected_count = sum(results.values())
        total_count = len(results)

        log_system_event(
            "platform_manager",
            "connect_summary",
            f"Connected to {connected_count}/{total_count} platforms",
        )

        return results

    async def disconnect_all(self) -> Dict[str, bool]:
        """Disconnect from all platforms."""
        results = {}

        for platform_name, executor in self.platforms.items():
            try:
                success = await executor.disconnect()
                results[platform_name] = success

                if success:
                    log_system_event(
                        "platform_manager",
                        "platform_disconnected",
                        f"Disconnected from {platform_name}",
                    )
            except Exception as e:
                results[platform_name] = False
                log_error_with_context(
                    e, {"platform": platform_name, "operation": "disconnect"}
                )

        return results

    def get_platform_for_symbol(
        self, symbol: str, platform_hint: Optional[str] = None
    ) -> Optional[str]:
        """Get the best platform for trading a specific symbol."""
        # Use platform hint if provided and available
        if platform_hint and platform_hint in self.platforms:
            if self.platforms[platform_hint].is_connected:
                return platform_hint

        # Check platform preferences
        if symbol in self.platform_preferences:
            preferred_platform = self.platform_preferences[symbol]
            if (
                preferred_platform in self.platforms
                and self.platforms[preferred_platform].is_connected
            ):
                return preferred_platform

        # Auto-detect based on symbol format
        symbol_upper = symbol.upper()

        # Crypto symbols (ending with USDT, USDC, BTC, ETH)
        if any(
            symbol_upper.endswith(suffix) for suffix in ["USDT", "USDC", "BTC", "ETH"]
        ):
            for platform in ["binance", "bybit", "bitget"]:
                if platform in self.platforms and self.platforms[platform].is_connected:
                    return platform

        # Forex symbols (6-8 characters, common pairs)
        elif len(symbol_upper) in [6, 7, 8] and any(
            symbol_upper.startswith(prefix)
            for prefix in ["EUR", "GBP", "USD", "AUD", "CAD", "CHF", "NZD", "JPY"]
        ):
            if "mt5" in self.platforms and self.platforms["mt5"].is_connected:
                return "mt5"

        # Fallback to primary platform
        if self.primary_platform and self.primary_platform in self.platforms:
            if self.platforms[self.primary_platform].is_connected:
                return self.primary_platform

        # Fallback to any connected platform
        for platform_name, executor in self.platforms.items():
            if executor.is_connected:
                return platform_name

        return None

    def get_executor(self, platform_name: str) -> Optional[IExecutor]:
        """Get executor for specific platform."""
        return self.platforms.get(platform_name)

    def get_executor_for_symbol(
        self, symbol: str, platform_hint: Optional[str] = None
    ) -> Optional[IExecutor]:
        """Get executor for trading a specific symbol."""
        platform_name = self.get_platform_for_symbol(symbol, platform_hint)
        if platform_name:
            return self.platforms[platform_name]
        return None

    async def place_order(
        self, order: Dict[str, Any], platform_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Place order on the appropriate platform."""
        symbol = order.get("symbol", "")

        executor = self.get_executor_for_symbol(symbol, platform_hint)
        if not executor:
            return {
                "success": False,
                "error": f"No available platform for symbol {symbol}",
                "symbol": symbol,
            }

        try:
            result = await executor.place_order(order)
            result["platform"] = executor.platform_type.value
            return result
        except Exception as e:
            log_error_with_context(
                e, {"symbol": symbol, "platform": executor.platform_type.value}
            )
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "platform": executor.platform_type.value,
            }

    async def get_all_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get positions from all connected platforms."""
        all_positions = {}

        for platform_name, executor in self.platforms.items():
            if executor.is_connected:
                try:
                    positions = await executor.get_positions()
                    all_positions[platform_name] = positions
                except Exception as e:
                    log_error_with_context(
                        e, {"platform": platform_name, "operation": "get_positions"}
                    )
                    all_positions[platform_name] = []

        return all_positions

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get positions from all connected platforms (flattened list)."""
        all_positions = await self.get_all_positions()
        flattened_positions = []

        for platform_name, positions in all_positions.items():
            for position in positions:
                position["platform"] = platform_name
                flattened_positions.append(position)

        return flattened_positions

    async def get_all_orders(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get orders from all connected platforms."""
        all_orders = {}

        for platform_name, executor in self.platforms.items():
            if executor.is_connected:
                try:
                    orders = await executor.get_orders()
                    all_orders[platform_name] = orders
                except Exception as e:
                    log_error_with_context(
                        e, {"platform": platform_name, "operation": "get_orders"}
                    )
                    all_orders[platform_name] = []

        return all_orders

    async def get_all_balances(self) -> Dict[str, Dict[str, Any]]:
        """Get account balances from all connected platforms."""
        all_balances = {}

        for platform_name, executor in self.platforms.items():
            if executor.is_connected:
                try:
                    account_info = await executor.get_account_info()
                    if account_info:
                        # Handle both dict and object formats
                        if hasattr(account_info, "balance"):
                            # Object format
                            all_balances[platform_name] = {
                                "balance": account_info.balance,
                                "equity": getattr(account_info, "equity", 0),
                                "margin_used": getattr(account_info, "margin_used", 0),
                                "margin_available": getattr(
                                    account_info, "margin_available", 0
                                ),
                                "is_demo": getattr(account_info, "is_demo", False),
                                "platform": getattr(
                                    account_info, "platform", platform_name
                                ),
                            }
                        else:
                            # Dict format
                            all_balances[platform_name] = account_info
                except Exception as e:
                    log_error_with_context(
                        e, {"platform": platform_name, "operation": "get_account_info"}
                    )
                    all_balances[platform_name] = {}

        return all_balances

    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all platforms."""
        health_results = {}

        for platform_name, executor in self.platforms.items():
            try:
                is_healthy = await executor.health_check()
                health_results[platform_name] = is_healthy
            except Exception as e:
                log_error_with_context(
                    e, {"platform": platform_name, "operation": "health_check"}
                )
                health_results[platform_name] = False

        return health_results

    def get_platform_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all platforms."""
        status = {}

        for platform_name, executor in self.platforms.items():
            status[platform_name] = executor.get_status()

        return {
            "platforms": status,
            "primary_platform": self.primary_platform,
            "total_platforms": len(self.platforms),
            "connected_platforms": sum(
                1 for e in self.platforms.values() if e.is_connected
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def set_platform_preference(self, symbol: str, platform: str):
        """Set platform preference for a specific symbol."""
        if platform in self.platforms:
            self.platform_preferences[symbol] = platform
            logger.info(f"Set platform preference: {symbol} -> {platform}")
        else:
            logger.warning(f"Platform {platform} not available")

    def get_available_platforms(self) -> List[str]:
        """Get list of available platform names."""
        return list(self.platforms.keys())

    def get_connected_platforms(self) -> List[str]:
        """Get list of connected platform names."""
        return [
            name for name, executor in self.platforms.items() if executor.is_connected
        ]
