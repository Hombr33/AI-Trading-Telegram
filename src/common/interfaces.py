from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum


# Platform and Execution Interfaces
class PlatformType(Enum):
    """Trading platform types."""
    MT5 = "mt5"
    BINANCE = "binance"
    BYBIT = "bybit"
    BITGET = "bitget"
    DEMO = "demo"


class OrderType(Enum):
    """Universal order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Universal order sides."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Universal order status."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class IExecutor(ABC):
    """Interface for trading platform executors."""
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform display name."""
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to platform."""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to trading platform."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from trading platform."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test platform connection."""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information."""
        pass
    
    @abstractmethod
    async def get_balance(self, asset: str = "USD") -> float:
        """Get account balance for specific asset."""
        pass
    
    @abstractmethod
    async def place_order(self, symbol: str, order_type: OrderType, side: OrderSide, 
                         volume: float, price: Optional[float] = None, 
                         stop_loss: Optional[float] = None, 
                         take_profit: Optional[float] = None, 
                         **kwargs) -> Dict[str, Any]:
        """Place a new order."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an existing order."""
        pass


class IPlatformManager(ABC):
    """Interface for platform manager."""
    
    @abstractmethod
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all configured platforms."""
        pass
    
    @abstractmethod
    async def disconnect_all(self) -> Dict[str, bool]:
        """Disconnect from all platforms."""
        pass
    
    @abstractmethod
    def get_platform_for_symbol(self, symbol: str, platform_hint: Optional[str] = None) -> Optional[str]:
        """Get the best platform for trading a specific symbol."""
        pass
    
    @abstractmethod
    def get_executor(self, platform_name: str) -> Optional[IExecutor]:
        """Get executor for a specific platform."""
        pass


class IOrderManager(ABC):
    """Interface for order management services."""
    
    @abstractmethod
    async def place_order(self, platform: str, symbol: str, order_type: OrderType, side: OrderSide,
                         volume: float, price: Optional[float] = None, 
                         stop_loss: Optional[float] = None, 
                         take_profit: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        """Place an order on the specified platform."""
        pass
    
    @abstractmethod
    async def cancel_order(self, platform: str, order_id: str, symbol: str) -> bool:
        """Cancel an existing order."""
        pass
    
    @abstractmethod
    async def get_order(self, platform: str, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get information about a specific order."""
        pass
    
    @abstractmethod
    async def get_open_orders(self, platform: str = None, symbol: str = None) -> List[Dict[str, Any]]:
        """Get all open orders, optionally filtered by platform and symbol."""
        pass
    
    @abstractmethod
    async def get_positions(self, platform: str = None, symbol: str = None) -> List[Dict[str, Any]]:
        """Get all open positions, optionally filtered by platform and symbol."""
        pass


# Analysis Interfaces
class IAnalyzer(ABC):
    """
    Interface for an analysis service that processes market data
    to generate a trading signal.
    """

    @abstractmethod
    async def analyze(self, screenshot_data: bytes, market_context: dict) -> Any:
        """
        Analyzes the provided market data and returns a trading signal.

        Args:
            screenshot_data: The byte content of the market screenshot.
            market_context: A dictionary containing additional context about the market.

        Returns:
            A structured trading signal, or None if no signal is generated.
        """
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test analyzer connection."""
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if analyzer is available."""
        pass


class IPositionManager(ABC):
    """Interface for position management services."""
    
    @abstractmethod
    async def get_positions(self) -> List[Any]:
        """Get all active positions."""
        pass
    
    @abstractmethod
    async def modify_position(self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None) -> Dict[str, Any]:
        """Modify position stop loss or take profit."""
        pass
    
    @abstractmethod
    def get_position(self, ticket: int) -> Optional[Any]:
        """Get position by ticket."""
        pass
    
    @abstractmethod
    def get_positions_by_symbol(self, symbol: str) -> List[Any]:
        """Get positions by symbol."""
        pass


class ISignalGenerationService(ABC):
    """Interface for signal generation services."""
    
    @abstractmethod
    async def generate_signal(self, screenshot_data: bytes, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a trading signal from screenshot and market context."""
        pass
    
    @abstractmethod
    def add_analyzer(self, analyzer: IAnalyzer, priority: int = 0) -> None:
        """Add an analyzer to the service with a priority level."""
        pass
    
    @abstractmethod
    def remove_analyzer(self, analyzer_id: str) -> bool:
        """Remove an analyzer from the service."""
        pass
    
    @abstractmethod
    async def get_available_analyzers(self) -> List[Dict[str, Any]]:
        """Get a list of available analyzers."""
        pass
    
    @abstractmethod
    async def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate a trading signal."""
        pass


# Service Interfaces
class IAutoTradingService(ABC):
    """Interface for automatic trading services."""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the auto trading service."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the auto trading service."""
        pass
    
    @abstractmethod
    def add_signal(self, signal: Dict[str, Any]) -> bool:
        """Add a trading signal to the pending queue."""
        pass
    
    @abstractmethod
    def set_order_manager(self, order_manager: 'IOrderManager') -> None:
        """Set the order manager instance."""
        pass
