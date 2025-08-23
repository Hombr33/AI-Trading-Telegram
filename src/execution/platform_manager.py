"""
Platform manager for multi-exchange trading support.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone

from ..core.logging import get_logger, log_system_event, log_error_with_context
from ..core.error_handler import with_error_handling, ErrorContext
from ..core.exceptions import TradingBotException
from .base_executor import BaseExecutor, PlatformType

logger = get_logger(__name__)

# Import executors  
import sys

# Import crypto executors (always available)
from .crypto.binance_executor import BinanceExecutor
from .crypto.bybit_executor import BybitExecutor
from .crypto.bitget_executor import BitgetExecutor

# Import MT5 executors only on Windows or if explicitly available
MT5Executor = None
AioMQLExecutor = None

if sys.platform == "win32":
    try:
        from .mt5_executor import MT5Executor
        from .aiomql_executor import AioMQLExecutor
        logger.info("MT5 executors loaded (Windows platform)")
    except ImportError as e:
        logger.warning(f"MT5 executors not available: {e}")
        logger.info("Continuing with crypto-only functionality")
else:
    logger.info(f"MT5 executors disabled on {sys.platform} (crypto-only mode)")


class PlatformManager:
    """Manages multiple trading platforms and routes orders intelligently."""
    
    def __init__(self, config):
        self.config = config
        self.platforms: Dict[str, BaseExecutor] = {}
        self.primary_platform: Optional[str] = None
        self.platform_preferences: Dict[str, str] = {}  # Symbol -> Platform mapping
        
        # Initialize available platforms
        self._initialize_platforms()
    
    def _initialize_platforms(self):
        """Initialize all configured trading platforms."""
        # MT5/Forex platforms (Windows only)
        if AioMQLExecutor is not None and self.config.mt5.is_configured:
            try:
                # Use AioMQL if available, fallback to MT5Executor
                mt5_executor = AioMQLExecutor(self.config.mt5)
                self.platforms["mt5"] = mt5_executor
                if not self.primary_platform:
                    self.primary_platform = "mt5"
                logger.info("Initialized MT5/AioMQL executor")
            except Exception as e:
                logger.warning(f"Failed to initialize MT5 executor: {e}")
        elif MT5Executor is not None and self.config.mt5.is_configured:
            try:
                mt5_executor = MT5Executor(self.config.mt5)
                self.platforms["mt5"] = mt5_executor
                if not self.primary_platform:
                    self.primary_platform = "mt5"
                logger.info("Initialized MT5 executor")
            except Exception as e:
                logger.warning(f"Failed to initialize MT5 executor: {e}")
        elif self.config.mt5.is_configured:
            logger.warning("MT5 configured but not available on this platform (Linux/macOS)")
        
        # Crypto platforms
        if self.config.crypto.binance_configured:
            try:
                binance_executor = BinanceExecutor(self.config.crypto)
                self.platforms["binance"] = binance_executor
                if not self.primary_platform:
                    self.primary_platform = "binance"
                logger.info("Initialized Binance executor")
            except Exception as e:
                logger.warning(f"Failed to initialize Binance executor: {e}")
        
        if self.config.crypto.bybit_configured:
            try:
                bybit_executor = BybitExecutor(self.config.crypto)
                self.platforms["bybit"] = bybit_executor
                if not self.primary_platform:
                    self.primary_platform = "bybit"
                logger.info("Initialized Bybit executor")
            except Exception as e:
                logger.warning(f"Failed to initialize Bybit executor: {e}")
        
        if self.config.crypto.bitget_configured:
            try:
                bitget_executor = BitgetExecutor(self.config.crypto)
                self.platforms["bitget"] = bitget_executor
                if not self.primary_platform:
                    self.primary_platform = "bitget"
                logger.info("Initialized Bitget executor")
            except Exception as e:
                logger.warning(f"Failed to initialize Bitget executor: {e}")
        
        # Set platform preferences for different asset types
        self._setup_platform_preferences()
    
    def _setup_platform_preferences(self):
        """Setup default platform preferences for different symbols."""
        # Forex pairs -> MT5 (only if MT5 available)
        if "mt5" in self.platforms:
            forex_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]
            for pair in forex_pairs:
                self.platform_preferences[pair] = "mt5"
        
        # Crypto pairs -> prefer order: Binance > Bybit > Bitget
        crypto_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]
        for symbol in crypto_symbols:
            if "binance" in self.platforms:
                self.platform_preferences[symbol] = "binance"
            elif "bybit" in self.platforms:
                self.platform_preferences[symbol] = "bybit"
            elif "bitget" in self.platforms:
                self.platform_preferences[symbol] = "bitget"
        
        # If no platforms available, log warning
        if not self.platforms:
            logger.warning("No trading platforms initialized. Check your configuration.")
    
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
                        log_system_event("platform_manager", "platform_connected", 
                                        f"Connected to {platform_name}")
                    else:
                        log_system_event("platform_manager", "platform_failed", 
                                        f"Failed to connect to {platform_name}")
            except Exception as e:
                results[platform_name] = False
                log_error_with_context(e, {"platform": platform_name, "operation": "connect"})
        
        connected_count = sum(results.values())
        total_count = len(results)
        
        log_system_event("platform_manager", "connect_summary", 
                        f"Connected to {connected_count}/{total_count} platforms")
        
        return results
    
    async def disconnect_all(self) -> Dict[str, bool]:
        """Disconnect from all platforms."""
        results = {}
        
        for platform_name, executor in self.platforms.items():
            try:
                success = await executor.disconnect()
                results[platform_name] = success
                
                if success:
                    log_system_event("platform_manager", "platform_disconnected", 
                                    f"Disconnected from {platform_name}")
            except Exception as e:
                results[platform_name] = False
                log_error_with_context(e, {"platform": platform_name, "operation": "disconnect"})
        
        return results
    
    def get_platform_for_symbol(self, symbol: str, platform_hint: Optional[str] = None) -> Optional[str]:
        """Get the best platform for trading a specific symbol."""
        # Use platform hint if provided and available
        if platform_hint and platform_hint in self.platforms:
            if self.platforms[platform_hint].is_connected:
                return platform_hint
        
        # Check platform preferences
        if symbol in self.platform_preferences:
            preferred_platform = self.platform_preferences[symbol]
            if preferred_platform in self.platforms and self.platforms[preferred_platform].is_connected:
                return preferred_platform
        
        # Auto-detect based on symbol format
        symbol_upper = symbol.upper()
        
        # Crypto symbols (ending with USDT, USDC, BTC, ETH)
        if any(symbol_upper.endswith(suffix) for suffix in ["USDT", "USDC", "BTC", "ETH"]):
            for platform in ["binance", "bybit", "bitget"]:
                if platform in self.platforms and self.platforms[platform].is_connected:
                    return platform
        
        # Forex symbols (6-8 characters, common pairs)
        elif len(symbol_upper) in [6, 7, 8] and any(symbol_upper.startswith(prefix) for prefix in ["EUR", "GBP", "USD", "AUD", "CAD", "CHF", "NZD", "JPY"]):
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
    
    def get_executor(self, platform_name: str) -> Optional[BaseExecutor]:
        """Get executor for specific platform."""
        return self.platforms.get(platform_name)
    
    def get_executor_for_symbol(self, symbol: str, platform_hint: Optional[str] = None) -> Optional[BaseExecutor]:
        """Get executor for trading a specific symbol."""
        platform_name = self.get_platform_for_symbol(symbol, platform_hint)
        if platform_name:
            return self.platforms[platform_name]
        return None
    
    async def place_order(self, order: Dict[str, Any], platform_hint: Optional[str] = None) -> Dict[str, Any]:
        """Place order on the appropriate platform."""
        symbol = order.get("symbol", "")
        
        executor = self.get_executor_for_symbol(symbol, platform_hint)
        if not executor:
            return {
                "success": False,
                "error": f"No available platform for symbol {symbol}",
                "symbol": symbol
            }
        
        try:
            result = await executor.place_order(order)
            result["platform"] = executor.platform_type.value
            return result
        except Exception as e:
            log_error_with_context(e, {"symbol": symbol, "platform": executor.platform_name})
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "platform": executor.platform_type.value
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
                    log_error_with_context(e, {"platform": platform_name, "operation": "get_positions"})
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
                    log_error_with_context(e, {"platform": platform_name, "operation": "get_orders"})
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
                        all_balances[platform_name] = account_info
                except Exception as e:
                    log_error_with_context(e, {"platform": platform_name, "operation": "get_account_info"})
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
                log_error_with_context(e, {"platform": platform_name, "operation": "health_check"})
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
            "connected_platforms": sum(1 for e in self.platforms.values() if e.is_connected),
            "timestamp": datetime.now(timezone.utc).isoformat()
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
        return [name for name, executor in self.platforms.items() if executor.is_connected]
