"""Keyboard utilities for Telegram bot."""

from typing import List, Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def create_keyboard(buttons: List[List[Dict[str, str]]]) -> InlineKeyboardMarkup:
    """Create an inline keyboard markup from a list of button definitions.
    
    Args:
        buttons: List of button rows, where each row is a list of button definitions.
               Each button definition is a dict with 'text' and 'callback_data' keys.
    
    Returns:
        InlineKeyboardMarkup: The created inline keyboard markup.
    """
    keyboard = []
    
    for row in buttons:
        keyboard_row = []
        for button in row:
            keyboard_row.append(
                InlineKeyboardButton(
                    text=button["text"],
                    callback_data=button["callback_data"]
                )
            )
        keyboard.append(keyboard_row)
    
    return InlineKeyboardMarkup(keyboard)


def get_status_keyboard() -> InlineKeyboardMarkup:
    """Get the status command keyboard."""
    buttons = [
        [
            {"text": "🔄 Refresh", "callback_data": "refresh_status"},
            {"text": "⚙️ Settings", "callback_data": "settings"}
        ],
        [
            {"text": "📈 View Positions", "callback_data": "positions"},
            {"text": "⚠️ Risk Metrics", "callback_data": "risk"}
        ]
    ]
    return create_keyboard(buttons)


def get_positions_keyboard() -> InlineKeyboardMarkup:
    """Get the positions command keyboard."""
    buttons = [
        [
            {"text": "🔄 Refresh", "callback_data": "refresh_positions"},
            {"text": "📊 Charts", "callback_data": "charts"}
        ],
        [
            {"text": "⚠️ Risk Analysis", "callback_data": "risk"},
            {"text": "📈 Performance", "callback_data": "performance"}
        ]
    ]
    return create_keyboard(buttons)


def get_signals_keyboard() -> InlineKeyboardMarkup:
    """Get the signals command keyboard."""
    buttons = [
        [
            {"text": "🔄 Refresh", "callback_data": "refresh_signals"},
            {"text": "📊 Analysis", "callback_data": "analysis"}
        ],
        [
            {"text": "⚙️ Signal Settings", "callback_data": "signal_settings"},
            {"text": "📈 Market Overview", "callback_data": "market_overview"}
        ]
    ]
    return create_keyboard(buttons)


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Get the help command keyboard."""
    buttons = [
        [
            {"text": "📈 Open Positions", "callback_data": "positions"},
            {"text": "🎯 Latest Signals", "callback_data": "signals"}
        ],
        [
            {"text": "💼 Account", "callback_data": "account"},
            {"text": "⚠️ Risk", "callback_data": "risk"}
        ],
        [
            {"text": "⚙️ Settings", "callback_data": "settings"},
            {"text": "📊 Status", "callback_data": "status"}
        ]
    ]
    return create_keyboard(buttons)


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Get the start command keyboard."""
    buttons = [
        [
            {"text": "📊 Status", "callback_data": "status"},
            {"text": "📈 Positions", "callback_data": "positions"}
        ],
        [
            {"text": "💼 Account", "callback_data": "account"},
            {"text": "📋 Orders", "callback_data": "orders"}
        ],
        [
            {"text": "🎯 Signals", "callback_data": "signals"},
            {"text": "⚠️ Risk", "callback_data": "risk"}
        ],
        [
            {"text": "🖥️ Monitor", "callback_data": "monitor"},
            {"text": "⚙️ Settings", "callback_data": "settings"}
        ],
        [
            {"text": "❓ Help", "callback_data": "help"}
        ]
    ]
    return create_keyboard(buttons)


def get_account_keyboard() -> InlineKeyboardMarkup:
    """Get the account command keyboard."""
    buttons = [
        [
            {"text": "🔄 Refresh", "callback_data": "refresh_account"},
            {"text": "📈 Positions", "callback_data": "positions"}
        ],
        [
            {"text": "📋 Orders", "callback_data": "orders"},
            {"text": "⚠️ Risk", "callback_data": "risk"}
        ]
    ]
    return create_keyboard(buttons)


def get_monitor_keyboard() -> InlineKeyboardMarkup:
    """Get the monitor command keyboard."""
    buttons = [
        [
            {"text": "🔄 Refresh", "callback_data": "refresh_monitor"},
            {"text": "📊 Status", "callback_data": "status"}
        ],
        [
            {"text": "💼 Account", "callback_data": "account"},
            {"text": "⚙️ Settings", "callback_data": "settings"}
        ]
    ]
    return create_keyboard(buttons)