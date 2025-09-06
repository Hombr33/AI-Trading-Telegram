"""Keyboard utilities for Telegram bot."""

from typing import Any, Dict, List

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)


def create_keyboard(buttons: List[List[tuple]]) -> InlineKeyboardMarkup:
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
            if isinstance(button, tuple) and len(button) == 2:
                text, callback_data = button
                keyboard_row.append(
                    InlineKeyboardButton(text=text, callback_data=callback_data)
                )
            elif isinstance(button, dict):
                keyboard_row.append(
                    InlineKeyboardButton(
                        text=button["text"], callback_data=button["callback_data"]
                    )
                )
        keyboard.append(keyboard_row)

    return InlineKeyboardMarkup(keyboard)


def get_status_keyboard() -> InlineKeyboardMarkup:
    """Get the status command keyboard."""
    buttons = [
        [
            {"text": "🔄 Refresh", "callback_data": "refresh_status"},
            {"text": "⚙️ Settings", "callback_data": "settings"},
        ],
        [
            {"text": "📈 View Positions", "callback_data": "positions"},
            {"text": "⚠️ Risk Metrics", "callback_data": "risk"},
        ],
    ]
    return create_keyboard(buttons)


def get_positions_keyboard() -> InlineKeyboardMarkup:
    """Get the positions command keyboard."""
    buttons = [
        [
            {"text": "🔄 Refresh", "callback_data": "refresh_positions"},
            {"text": "📊 Charts", "callback_data": "charts"},
        ],
        [
            {"text": "⚠️ Risk Analysis", "callback_data": "risk"},
            {"text": "📈 Performance", "callback_data": "performance"},
        ],
    ]
    return create_keyboard(buttons)


def get_signals_keyboard() -> InlineKeyboardMarkup:
    """Get the signals command keyboard."""
    buttons = [
        [
            {"text": "🔄 Refresh", "callback_data": "refresh_signals"},
            {"text": "📊 Analysis", "callback_data": "analysis"},
        ],
        [
            {"text": "⚙️ Signal Settings", "callback_data": "signal_settings"},
            {"text": "📈 Market Overview", "callback_data": "market_overview"},
        ],
    ]
    return create_keyboard(buttons)


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Get the help command keyboard."""
    buttons = [
        [
            {"text": "📈 Open Positions", "callback_data": "positions"},
            {"text": "🎯 Latest Signals", "callback_data": "signals"},
        ],
        [
            {"text": "💼 Account", "callback_data": "account"},
            {"text": "⚠️ Risk", "callback_data": "risk"},
        ],
        [
            {"text": "⚙️ Settings", "callback_data": "settings"},
            {"text": "📊 Status", "callback_data": "status"},
        ],
    ]
    return create_keyboard(buttons)


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Get the start command keyboard."""
    buttons = [
        [
            {"text": "📊 Status", "callback_data": "status"},
            {"text": "📈 Positions", "callback_data": "positions"},
        ],
        [
            {"text": "💼 Account", "callback_data": "account"},
            {"text": "📋 Orders", "callback_data": "orders"},
        ],
        [
            {"text": "🎯 Signals", "callback_data": "signals"},
            {"text": "⚠️ Risk", "callback_data": "risk"},
        ],
        [
            {"text": "🖥️ Monitor", "callback_data": "monitor"},
            {"text": "⚙️ Settings", "callback_data": "settings"},
        ],
        [{"text": "❓ Help", "callback_data": "help"}],
    ]
    return create_keyboard(buttons)


def get_account_keyboard() -> InlineKeyboardMarkup:
    """Get the account command keyboard."""
    buttons = [
        [
            {"text": "🔄 Refresh", "callback_data": "refresh_account"},
            {"text": "📈 Positions", "callback_data": "positions"},
        ],
        [
            {"text": "📋 Orders", "callback_data": "orders"},
            {"text": "⚠️ Risk", "callback_data": "risk"},
        ],
    ]
    return create_keyboard(buttons)


def get_monitor_keyboard() -> InlineKeyboardMarkup:
    """Get the monitor command keyboard."""
    buttons = [
        [
            {"text": "🔄 Refresh", "callback_data": "refresh_monitor"},
            {"text": "📊 Status", "callback_data": "status"},
        ],
        [
            {"text": "💼 Account", "callback_data": "account"},
            {"text": "⚙️ Settings", "callback_data": "settings"},
        ],
    ]
    return create_keyboard(buttons)


def create_reply_keyboard(
    buttons: List[List[str]], resize: bool = True, one_time: bool = False
) -> ReplyKeyboardMarkup:
    """Create a reply keyboard markup.

    Args:
        buttons: List of button rows, where each row is a list of button texts.
        resize: Whether to resize the keyboard.
        one_time: Whether to hide keyboard after use.

    Returns:
        ReplyKeyboardMarkup: The created reply keyboard.
    """
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for button_text in row:
            keyboard_row.append(KeyboardButton(button_text))
        keyboard.append(keyboard_row)

    return ReplyKeyboardMarkup(
        keyboard, resize_keyboard=resize, one_time_keyboard=one_time
    )


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get the main menu reply keyboard."""
    buttons = [
        ["📊 Status", "💰 Account", "📈 Positions"],
        ["🎯 Signals", "⚠️ Risk", "📊 Performance"],
        ["🖥️ Monitor", "⚙️ Settings", "❓ Help"],
    ]
    return create_reply_keyboard(buttons)


def get_trading_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get the trading menu keyboard."""
    buttons = [
        ["📈 Open Positions", "📋 Pending Orders"],
        ["💰 Account Info", "🎯 Trading Signals"],
        ["📊 Performance", "⚠️ Risk Analysis"],
        ["🔙 Main Menu"],
    ]
    return create_reply_keyboard(buttons)


def get_analysis_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get the analysis menu keyboard."""
    buttons = [
        ["📊 Performance Stats", "⚠️ Risk Metrics"],
        ["📝 Trading Journal", "📈 Market Analysis"],
        ["🎯 Signal Analysis", "💹 Portfolio Overview"],
        ["🔙 Main Menu"],
    ]
    return create_reply_keyboard(buttons)


def get_system_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get the system menu keyboard."""
    buttons = [
        ["📊 System Status", "🖥️ Resource Monitor"],
        ["⚙️ Bot Settings", "🔧 Configuration"],
        ["📊 Logs", "🔄 Restart Services"],
        ["🔙 Main Menu"],
    ]
    return create_reply_keyboard(buttons)


def create_progress_keyboard(
    current: int, total: int, prefix: str = "progress"
) -> InlineKeyboardMarkup:
    """Create a progress bar keyboard.

    Args:
        current: Current progress value.
        total: Total progress value.
        prefix: Callback data prefix.

    Returns:
        InlineKeyboardMarkup: Progress bar keyboard.
    """
    progress_percent = int((current / total) * 10) if total > 0 else 0
    progress_bar = "█" * progress_percent + "░" * (10 - progress_percent)

    buttons = [
        [(f"📊 {progress_bar} {current}/{total}", f"{prefix}_progress")],
        [("🔄 Refresh", f"{prefix}_refresh"), ("❌ Cancel", f"{prefix}_cancel")],
    ]
    return create_keyboard(buttons)


def create_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Create a confirmation keyboard.

    Args:
        action: The action to confirm.

    Returns:
        InlineKeyboardMarkup: Confirmation keyboard.
    """
    buttons = [[("✅ Confirm", f"confirm_{action}"), ("❌ Cancel", f"cancel_{action}")]]
    return create_keyboard(buttons)


def create_paginated_keyboard(
    page: int, total_pages: int, prefix: str = "page"
) -> InlineKeyboardMarkup:
    """Create a paginated keyboard.

    Args:
        page: Current page number (1-indexed).
        total_pages: Total number of pages.
        prefix: Callback data prefix.

    Returns:
        InlineKeyboardMarkup: Paginated keyboard.
    """
    buttons = []

    # Navigation row
    nav_row = []
    if page > 1:
        nav_row.append(("⬅️ Previous", f"{prefix}_prev_{page-1}"))

    nav_row.append((f"📄 {page}/{total_pages}", f"{prefix}_current"))

    if page < total_pages:
        nav_row.append(("➡️ Next", f"{prefix}_next_{page+1}"))

    buttons.append(nav_row)

    # Quick jump row (if more than 3 pages)
    if total_pages > 3:
        jump_row = []
        if page > 1:
            jump_row.append(("⏪ First", f"{prefix}_first"))
        if page < total_pages:
            jump_row.append(("⏩ Last", f"{prefix}_last"))
        if jump_row:
            buttons.append(jump_row)

    # Action row
    buttons.append(
        [("🔄 Refresh", f"{prefix}_refresh"), ("❌ Close", f"{prefix}_close")]
    )

    return create_keyboard(buttons)


def create_quick_actions_keyboard() -> InlineKeyboardMarkup:
    """Create a quick actions floating keyboard."""
    buttons = [
        [("⚡ Quick Trade", "quick_trade"), ("📊 Market Pulse", "market_pulse")],
        [("🎯 AI Signal", "ai_signal"), ("⚠️ Risk Check", "risk_check")],
        [("📈 P&L Summary", "pnl_summary"), ("🔔 Notifications", "notifications")],
    ]
    return create_keyboard(buttons)


def create_animated_loading_keyboard(step: int = 0) -> InlineKeyboardMarkup:
    """Create an animated loading keyboard.

    Args:
        step: Animation step (0-3).

    Returns:
        InlineKeyboardMarkup: Animated loading keyboard.
    """
    loading_frames = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
    frame = loading_frames[step % len(loading_frames)]

    buttons = [
        [(f"{frame} Loading... Please wait", "loading")],
        [("❌ Cancel", "cancel_loading")],
    ]
    return create_keyboard(buttons)


def create_emoji_status_keyboard(status: str) -> InlineKeyboardMarkup:
    """Create status keyboard with dynamic emojis.

    Args:
        status: Current status (connected, disconnected, error, etc.).

    Returns:
        InlineKeyboardMarkup: Status keyboard with appropriate emojis.
    """
    status_emojis = {
        "connected": "🟢",
        "disconnected": "🔴",
        "connecting": "🟡",
        "error": "❌",
        "warning": "⚠️",
        "success": "✅",
    }

    emoji = status_emojis.get(status, "❓")

    buttons = [
        [(f"{emoji} {status.title()}", f"status_{status}")],
        [("🔄 Refresh", "refresh_status"), ("⚙️ Settings", "settings")],
    ]
    return create_keyboard(buttons)


def create_trading_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Create an advanced trading dashboard keyboard."""
    buttons = [
        [("⚡ Live Dashboard", "live_dashboard"), ("🌐 Web App", "webapp")],
        [
            ("💰 Account", "account"),
            ("📈 Positions", "positions"),
            ("📋 Orders", "orders"),
        ],
        [
            ("🎯 Signals", "signals"),
            ("⚠️ Risk", "risk"),
            ("📊 Performance", "performance"),
        ],
        [("🖥️ Monitor", "monitor"), ("⚙️ Settings", "settings"), ("❓ Help", "help")],
        [("🔔 Notifications", "notifications"), ("📱 Quick Actions", "quick_actions")],
    ]
    return create_keyboard(buttons)


def create_webapp_keyboard(
    webapp_url: str = "https://your-webapp.com",
) -> InlineKeyboardMarkup:
    """Create a WebApp keyboard for advanced features."""
    # Note: In production, replace with your actual webapp URL
    buttons = [
        [("🌐 Open Trading WebApp", f"webapp_{webapp_url}")],
        [
            ("📊 Charts & Analysis", "charts"),
            ("💹 Advanced Trading", "advanced_trading"),
        ],
        [("🔙 Back to Bot", "start")],
    ]
    return create_keyboard(buttons)


def create_floating_action_keyboard() -> InlineKeyboardMarkup:
    """Create a floating action button style keyboard."""
    buttons = [
        [("🚀 TRADE NOW", "instant_trade")],
        [("⚡ QUICK BUY", "quick_buy"), ("🔥 QUICK SELL", "quick_sell")],
        [("🎯 AI SIGNAL", "ai_signal"), ("⚠️ RISK CHECK", "risk_check")],
        [("💰 BALANCE", "account"), ("📊 PORTFOLIO", "positions")],
    ]
    return create_keyboard(buttons)


def create_market_watch_keyboard(symbols: List[str]) -> InlineKeyboardMarkup:
    """Create market watch keyboard with live prices."""
    buttons = []

    # Add symbol buttons in rows of 2
    for i in range(0, len(symbols), 2):
        row = []
        for j in range(2):
            if i + j < len(symbols):
                symbol = symbols[i + j]
                row.append((f"📊 {symbol}", f"watch_{symbol}"))
        buttons.append(row)

    # Add action buttons
    buttons.extend(
        [
            [
                ("🔄 Refresh Prices", "refresh_watch"),
                ("⚙️ Customize", "customize_watch"),
            ],
            [("📈 Add Symbol", "add_symbol"), ("🗑️ Remove Symbol", "remove_symbol")],
        ]
    )

    return create_keyboard(buttons)
