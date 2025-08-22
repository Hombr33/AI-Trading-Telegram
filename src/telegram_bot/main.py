"""
Main entry point for the Telegram bot module.
This file provides backward compatibility with the original bot.py implementation.
"""

from .core.trading_bot import TradingBot

# Re-export TradingBot as TelegramBot for backward compatibility
TelegramBot = TradingBot