"""
Custom exceptions for the AI Trading Bot.
"""

from typing import Optional, Dict, Any


class TradingBotException(Exception):
    """Base exception for the trading bot."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)


class MT5ConnectionError(TradingBotException):
    """Error connecting to MT5 terminal."""

    pass


class MT5ExecutionError(TradingBotException):
    """Error executing MT5 operations."""

    pass


class AioMQLError(TradingBotException):
    """Error with AioMQL operations."""

    pass


class BridgeConnectionError(TradingBotException):
    """Error with bridge communication."""

    pass


class TelegramBotError(TradingBotException):
    """Error with Telegram bot operations."""

    pass


class OrderValidationError(TradingBotException):
    """Error validating order parameters."""

    pass


class RiskManagementError(TradingBotException):
    """Error with risk management validation."""

    pass


class ConfigurationError(TradingBotException):
    """Error with configuration settings."""

    pass


class DatabaseError(TradingBotException):
    """Error with database operations."""

    pass


class SignalProcessingError(TradingBotException):
    """Error processing trading signals."""

    pass


class EABridgeError(TradingBotException):
    """Error with EA bridge operations."""

    pass


class UserIsolationError(TradingBotException):
    """Error with user data isolation."""

    pass


class PositionManagerError(TradingBotException):
    """Error with position management operations."""

    pass


class OrderManagerError(TradingBotException):
    """Error with order management operations."""

    pass
