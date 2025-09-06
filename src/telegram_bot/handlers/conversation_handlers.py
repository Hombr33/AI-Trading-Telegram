"""
Conversation handlers for complex multi-user operations.
"""

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
)
from telegram.ext.filters import COMMAND, TEXT

from .admin_commands import AdminCommandHandlers
from .multi_user_handlers import MultiUserHandlers
from .user_commands import UserCommandHandlers


def setup_conversation_handlers():
    """Setup all conversation handlers for the bot."""

    # Initialize handlers
    user_handler = UserCommandHandlers()
    admin_handler = AdminCommandHandlers()
    multi_user_handler = MultiUserHandlers()

    conversation_handlers = []

    # MT5 Registration Conversation
    mt5_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("register_mt5", user_handler.register_mt5_command)
        ],
        states={
            user_handler.WAITING_API_KEY: [
                MessageHandler(TEXT & ~COMMAND, user_handler.handle_mt5_api_key)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", user_handler.cancel_conversation),
            MessageHandler(TEXT, user_handler.cancel_conversation),
        ],
        name="mt5_registration",
        persistent=False,
    )
    conversation_handlers.append(mt5_conversation)

    # Crypto Registration Conversation
    crypto_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("register_crypto", user_handler.register_crypto_command)
        ],
        states={
            user_handler.WAITING_CRYPTO_EXCHANGE: [
                CallbackQueryHandler(user_handler.handle_crypto_exchange_selection)
            ],
            user_handler.WAITING_CRYPTO_API_KEY: [
                MessageHandler(TEXT & ~COMMAND, user_handler.handle_crypto_api_key)
            ],
            user_handler.WAITING_CRYPTO_API_SECRET: [
                MessageHandler(TEXT & ~COMMAND, user_handler.handle_crypto_api_secret)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", user_handler.cancel_conversation),
            CallbackQueryHandler(
                user_handler.cancel_conversation, pattern="^crypto_cancel$"
            ),
        ],
        name="crypto_registration",
        persistent=False,
    )
    conversation_handlers.append(crypto_conversation)

    # Admin Add Conversation
    admin_add_conversation = ConversationHandler(
        entry_points=[CommandHandler("add_admin", admin_handler.add_admin_command)],
        states={
            admin_handler.WAITING_ADMIN_TARGET: [
                MessageHandler(TEXT & ~COMMAND, admin_handler.handle_add_admin)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", admin_handler.cancel_conversation),
            MessageHandler(TEXT, admin_handler.cancel_conversation),
        ],
        name="admin_add",
        persistent=False,
    )
    conversation_handlers.append(admin_add_conversation)

    # Admin Remove Conversation
    admin_remove_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("remove_admin", admin_handler.remove_admin_command)
        ],
        states={
            admin_handler.WAITING_ADMIN_TARGET: [
                MessageHandler(TEXT & ~COMMAND, admin_handler.handle_remove_admin)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", admin_handler.cancel_conversation),
            MessageHandler(TEXT, admin_handler.cancel_conversation),
        ],
        name="admin_remove",
        persistent=False,
    )
    conversation_handlers.append(admin_remove_conversation)

    # Subscription Management Conversation
    subscription_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("set_subscription", admin_handler.set_subscription_command)
        ],
        states={
            admin_handler.WAITING_ADMIN_TARGET: [
                MessageHandler(
                    TEXT & ~COMMAND, admin_handler.handle_subscription_target
                )
            ],
            admin_handler.WAITING_SUBSCRIPTION_STATUS: [
                CallbackQueryHandler(admin_handler.handle_subscription_status)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", admin_handler.cancel_conversation),
            CallbackQueryHandler(
                admin_handler.cancel_conversation, pattern="^sub_cancel$"
            ),
        ],
        name="subscription_management",
        persistent=False,
    )
    conversation_handlers.append(subscription_conversation)

    # User Search Conversation
    user_search_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("search_users", multi_user_handler.search_users_command)
        ],
        states={
            multi_user_handler.WAITING_USER_SEARCH: [
                MessageHandler(TEXT & ~COMMAND, multi_user_handler.handle_user_search)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", multi_user_handler.cancel_conversation),
            MessageHandler(TEXT, multi_user_handler.cancel_conversation),
        ],
        name="user_search",
        persistent=False,
    )
    conversation_handlers.append(user_search_conversation)

    # User Isolation Conversation
    user_isolation_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("isolate_user", multi_user_handler.user_isolation_command)
        ],
        states={
            multi_user_handler.WAITING_USER_SEARCH: [
                MessageHandler(TEXT & ~COMMAND, multi_user_handler.handle_user_search)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", multi_user_handler.cancel_conversation),
            MessageHandler(TEXT, multi_user_handler.cancel_conversation),
        ],
        name="user_isolation",
        persistent=False,
    )
    conversation_handlers.append(user_isolation_conversation)

    return conversation_handlers
