"""Command handler for Telegram bot."""

from typing import Dict, Any, List

from telegram import Update
from telegram.ext import CommandHandler as TelegramCommandHandler, ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.commands.handler import CommandHandler as BotCommandHandler

logger = get_logger(__name__)


class CommandHandlerManager:
    """Command handler manager for Telegram bot."""

    def __init__(self, command_handler: BotCommandHandler):
        """Initialize command handler manager.
        
        Args:
            command_handler: The command handler to use.
        """
        self.command_handler = command_handler

    def get_handlers(self) -> List[TelegramCommandHandler]:
        """Get command handlers.
        
        Returns:
            List of command handlers.
        """
        handlers = []
        command_handlers = self.command_handler.get_command_handlers()

        for command, handler_func in command_handlers.items():
            handlers.append(TelegramCommandHandler(command, handler_func))

        return handlers