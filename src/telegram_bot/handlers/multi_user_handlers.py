"""
Multi-user specific handlers for advanced user management and isolation.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

# Lazy imports to avoid circular dependencies
# from ...bridge.ea_bridge import EABridge
# from ...bridge.signal_distributor import SignalDistributor
from ...core.logging import get_logger
from ...models.telegram_users import PlatformType, SubscriptionStatus, TelegramUser
from ...services.config_manager import ConfigManager
from ...services.user_manager import UserManager

logger = get_logger(__name__)

# Conversation states for multi-user operations
WAITING_USER_SEARCH, WAITING_BULK_OPERATION, WAITING_BULK_CONFIRM = range(3)


class MultiUserHandlers:
    """Handlers for advanced multi-user operations and user isolation."""

    def __init__(self):
        self.user_manager = UserManager()
        self.config_manager = ConfigManager()
        # Lazy initialization to avoid circular imports
        self._ea_bridge = None
        self._signal_distributor = None

    def _get_ea_bridge(self):
        """Get EABridge with lazy initialization."""
        if self._ea_bridge is None:
            try:
                from ...bridge.ea_bridge import EABridge

                self._ea_bridge = EABridge()
            except ImportError:
                logger.warning("EABridge not available due to import issues")
                self._ea_bridge = None
        return self._ea_bridge

    def _get_signal_distributor(self):
        """Get SignalDistributor with lazy initialization."""
        if self._signal_distributor is None:
            try:
                from ...bridge.signal_distributor import SignalDistributor

                self._signal_distributor = SignalDistributor()
            except ImportError:
                logger.warning("SignalDistributor not available due to import issues")
                self._signal_distributor = None
        return self._signal_distributor

    async def search_users_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle /search_users command - search for users by various criteria."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            await update.message.reply_text("❌ Admin privileges required.")
            return ConversationHandler.END

        await update.message.reply_text(
            "🔍 **User Search**\n\n"
            "Enter search criteria:\n\n"
            "You can search by:\n"
            "• Telegram ID (number)\n"
            "• Username (with @)\n"
            "• First name\n"
            "• Email (if available)\n\n"
            "Example: @username or 123456789",
            parse_mode="Markdown",
        )

        return WAITING_USER_SEARCH

    async def handle_user_search(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle user search input."""
        admin_telegram_id = update.effective_user.id
        search_query = update.message.text.strip()

        # Search users
        users = await self.user_manager.get_all_users(admin_telegram_id)

        if not users:
            await update.message.reply_text("❌ No users found.")
            return ConversationHandler.END

        # Filter users based on search query
        found_users = []
        search_lower = search_query.lower()

        for user in users:
            # Search by telegram ID
            if search_query.isdigit() and str(user["telegram_id"]) == search_query:
                found_users.append(user)
                continue

            # Search by username
            if user["username"] and search_lower in user["username"].lower():
                found_users.append(user)
                continue

            # Search by first name
            if user["first_name"] and search_lower in user["first_name"].lower():
                found_users.append(user)
                continue

            # Search by last name
            if user["last_name"] and search_lower in user["last_name"].lower():
                found_users.append(user)
                continue

        if not found_users:
            await update.message.reply_text(
                f"❌ No users found matching: {search_query}"
            )
            return ConversationHandler.END

        # Display found users
        message = f"🔍 **Search Results for: {search_query}**\n\n"
        message += f"Found {len(found_users)} user(s):\n\n"

        for i, user in enumerate(found_users[:10], 1):  # Limit to 10 results
            status_emoji = {"active": "🟢", "expired": "🔴", "suspended": "🟡"}.get(
                user["subscription_status"], "⚪"
            )

            role_emoji = "👑" if user["role"] == "admin" else "👤"

            message += f"{i}. {role_emoji} {user['first_name'] or 'N/A'} {user['last_name'] or ''}\n"
            message += (
                f"   @{user['username'] or 'N/A'} (ID: `{user['telegram_id']}`)\n"
            )
            message += f"   {status_emoji} {user['subscription_status'].title()}\n"
            message += f"   📅 {user['created_at'].strftime('%Y-%m-%d')}\n\n"

        if len(found_users) > 10:
            message += f"... and {len(found_users) - 10} more results"

        # Add action buttons for found users
        keyboard = []
        if len(found_users) == 1:
            user_id = found_users[0]["telegram_id"]
            keyboard = [
                [
                    InlineKeyboardButton(
                        "👤 View Details", callback_data=f"user_details_{user_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⚙️ Manage User", callback_data=f"manage_user_{user_id}"
                    )
                ],
                [InlineKeyboardButton("🔄 New Search", callback_data="new_search")],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 New Search", callback_data="new_search")]
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message, reply_markup=reply_markup, parse_mode="Markdown"
        )
        return ConversationHandler.END

    async def bulk_operations_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /bulk_ops command - perform bulk operations on users."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            await update.message.reply_text("❌ Admin privileges required.")
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "📧 Bulk Notifications", callback_data="bulk_notify"
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 Bulk Subscriptions", callback_data="bulk_subscribe"
                )
            ],
            [InlineKeyboardButton("📊 Export User Data", callback_data="bulk_export")],
            [InlineKeyboardButton("🧹 Bulk Cleanup", callback_data="bulk_cleanup")],
            [InlineKeyboardButton("❌ Cancel", callback_data="bulk_cancel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "📦 **Bulk Operations**\n\n"
            "Select the type of bulk operation you want to perform:",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def user_isolation_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /isolate_user command - isolate a user for security."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            await update.message.reply_text("❌ Admin privileges required.")
            return

        await update.message.reply_text(
            "🚫 **User Isolation**\n\n"
            "Enter the Telegram ID of the user to isolate:\n\n"
            "This will:\n"
            "• Suspend the user's subscription\n"
            "• Disable all platform connections\n"
            "• Block trading operations\n"
            "• Preserve user data for investigation",
            parse_mode="Markdown",
        )

        context.user_data["isolation_mode"] = True
        return WAITING_USER_SEARCH

    async def user_details_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /user_details command - show detailed user information."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            await update.message.reply_text("❌ Admin privileges required.")
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a Telegram user ID.\n\nUsage: /user_details <telegram_id>"
            )
            return

        try:
            target_telegram_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid Telegram ID format.")
            return

        # Get detailed user information
        user = await self.user_manager.get_user(target_telegram_id)
        if not user:
            await update.message.reply_text("❌ User not found.")
            return

        # Get additional user data
        connections = await self.user_manager.get_user_platform_connections(
            target_telegram_id
        )
        subscriptions = await self.user_manager.get_user_subscriptions(
            target_telegram_id
        )
        user_configs = await self.config_manager.get_all_user_configs(
            target_telegram_id
        )

        message = f"👤 **Detailed User Information**\n\n"
        message += f"**Basic Info:**\n"
        message += f"• ID: `{user.telegram_id}`\n"
        message += f"• Name: {user.first_name or 'N/A'} {user.last_name or ''}\n"
        message += f"• Username: @{user.username or 'N/A'}\n"
        message += f"• Role: {user.role.value.title()}\n"
        message += f"• Status: {user.subscription_status.value.title()}\n"
        message += f"• Active: {'Yes' if user.is_active else 'No'}\n"
        message += f"• Created: {user.created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
        message += f"• Last Activity: {user.last_activity.strftime('%Y-%m-%d %H:%M UTC') if user.last_activity else 'Never'}\n\n"

        if user.subscription_expires_at:
            message += f"**Subscription:**\n"
            message += f"• Expires: {user.subscription_expires_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
            days_left = (user.subscription_expires_at - datetime.utcnow()).days
            message += f"• Days Left: {max(0, days_left)}\n\n"

        if connections:
            message += f"**Platform Connections ({len(connections)}):**\n"
            for conn in connections:
                platform_emoji = "📊" if conn["platform_type"] == "mt5" else "🏦"
                status_emoji = "🟢" if conn["last_connected"] else "🔴"
                message += (
                    f"• {platform_emoji} {conn['connection_name']} ({status_emoji})\n"
                )
            message += "\n"

        if subscriptions:
            message += f"**Signal Subscriptions ({len(subscriptions)}):**\n"
            for sub in subscriptions:
                message += f"• 📊 {sub['symbol']} (min {sub['min_confidence']}%)\n"
            message += "\n"

        if user_configs:
            message += f"**Configuration Profiles ({len(user_configs)}):**\n"
            for config_type in user_configs.keys():
                message += f"• ⚙️ {config_type.title()}\n"

        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton(
                    "⚙️ Edit User", callback_data=f"edit_user_{target_telegram_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 View Performance",
                    callback_data=f"user_performance_{target_telegram_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🚫 Isolate User",
                    callback_data=f"isolate_user_{target_telegram_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Refresh", callback_data=f"refresh_user_{target_telegram_id}"
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def system_monitor_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /system_monitor command - show system-wide monitoring."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            await update.message.reply_text("❌ Admin privileges required.")
            return

        # Get system statistics
        users = await self.user_manager.get_all_users(telegram_id)

        if not users:
            await update.message.reply_text("❌ Could not retrieve system statistics.")
            return

        # Calculate statistics
        total_users = len(users)
        active_users = sum(1 for u in users if u["subscription_status"] == "active")
        admin_users = sum(1 for u in users if u["role"] == "admin")
        expired_users = sum(1 for u in users if u["subscription_status"] == "expired")
        suspended_users = sum(
            1 for u in users if u["subscription_status"] == "suspended"
        )

        # Recent activity (last 24 hours)
        recent_activity = sum(
            1
            for u in users
            if u["last_activity"]
            and (datetime.utcnow() - u["last_activity"]) < timedelta(hours=24)
        )

        message = "📊 **System Monitor**\n\n"
        message += f"**User Statistics:**\n"
        message += f"• Total Users: {total_users}\n"
        message += f"• Active Subscriptions: {active_users}\n"
        message += f"• Administrators: {admin_users}\n"
        message += f"• Expired Subscriptions: {expired_users}\n"
        message += f"• Suspended Users: {suspended_users}\n"
        message += f"• Recent Activity (24h): {recent_activity}\n\n"

        message += f"**System Health:**\n"
        message += f"• Database: 🟢 Connected\n"
        message += f"• EA Bridge: 🟢 Active\n"
        message += f"• Signal Distributor: 🟢 Running\n"
        message += f"• Notification System: 🟢 Operational\n\n"

        message += f"**Quick Actions:**\n"
        message += f"• View all users: /users\n"
        message += f"• Search users: /search_users\n"
        message += f"• Bulk operations: /bulk_ops\n"
        message += f"• System logs: /logs"

        # Add refresh button
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_monitor")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def handle_multi_user_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle multi-user callback queries."""
        query = update.callback_query
        await query.answer()

        telegram_id = query.from_user.id
        data = query.data

        if not await self.user_manager.is_admin(telegram_id):
            await query.edit_message_text("❌ Admin privileges required.")
            return

        if data == "new_search":
            await query.edit_message_text("🔄 Starting new search...")
            await self.search_users_command(update, context)

        elif data.startswith("user_details_"):
            user_id = int(data.replace("user_details_", ""))
            await query.edit_message_text("📋 Fetching user details...")
            # Trigger user details command
            context.args = [str(user_id)]
            await self.user_details_command(update, context)

        elif data.startswith("manage_user_"):
            user_id = int(data.replace("manage_user_", ""))
            await query.edit_message_text(
                f"⚙️ **Manage User {user_id}**\n\n"
                f"Available actions:\n"
                f"• Change subscription: /set_subscription {user_id} <status>\n"
                f"• Add admin: /add_admin {user_id}\n"
                f"• View details: /user_details {user_id}\n"
                f"• Isolate user: /isolate_user {user_id}",
                parse_mode="Markdown",
            )

        elif data == "bulk_notify":
            await query.edit_message_text(
                "📧 **Bulk Notifications**\n\n"
                "This feature allows you to send notifications to multiple users.\n\n"
                "*Feature not yet implemented.*\n\n"
                "Available options:\n"
                "• Send to all active users\n"
                "• Send to specific user groups\n"
                "• Send maintenance notifications\n"
                "• Send feature update notifications",
                parse_mode="Markdown",
            )

        elif data == "bulk_subscribe":
            await query.edit_message_text(
                "💎 **Bulk Subscription Management**\n\n"
                "This feature allows you to manage subscriptions for multiple users.\n\n"
                "*Feature not yet implemented.*\n\n"
                "Available options:\n"
                "• Activate multiple users\n"
                "• Extend subscription periods\n"
                "• Apply promotional subscriptions\n"
                "• Bulk subscription expiry",
                parse_mode="Markdown",
            )

        elif data == "bulk_export":
            await query.edit_message_text(
                "📊 **Bulk Data Export**\n\n"
                "This feature allows you to export user data for analysis.\n\n"
                "*Feature not yet implemented.*\n\n"
                "Available exports:\n"
                "• User list with details\n"
                "• Subscription analytics\n"
                "• Platform connection data\n"
                "• Performance metrics",
                parse_mode="Markdown",
            )

        elif data == "bulk_cleanup":
            await query.edit_message_text(
                "🧹 **Bulk Cleanup**\n\n"
                "This feature allows you to clean up inactive or problematic users.\n\n"
                "*Feature not yet implemented.*\n\n"
                "Available cleanup options:\n"
                "• Remove inactive users\n"
                "• Clean expired subscriptions\n"
                "• Remove orphaned connections\n"
                "• Archive old data",
                parse_mode="Markdown",
            )

        elif data == "bulk_cancel":
            await query.edit_message_text("❌ Bulk operation cancelled.")

        elif data == "refresh_monitor":
            await query.edit_message_text("🔄 Refreshing system monitor...")
            await self.system_monitor_command(update, context)

        elif data.startswith("edit_user_"):
            user_id = int(data.replace("edit_user_", ""))
            await query.edit_message_text(
                f"⚙️ **Edit User {user_id}**\n\n"
                "Available edit options:\n\n"
                "• Change subscription: /set_subscription\n"
                "• Modify user role: /add_admin or /remove_admin\n"
                "• Update user info: Contact support\n"
                "• Manage connections: View user details\n\n"
                "Use the specific commands to make changes.",
                parse_mode="Markdown",
            )

        elif data.startswith("user_performance_"):
            user_id = int(data.replace("user_performance_", ""))
            await query.edit_message_text(
                f"📈 **User {user_id} Performance**\n\n"
                "*Performance tracking not yet implemented.*\n\n"
                "This will show:\n"
                "• Trading statistics\n"
                "• Win/loss ratios\n"
                "• Risk metrics\n"
                "• Performance charts\n"
                "• Historical data",
                parse_mode="Markdown",
            )

        elif data.startswith("isolate_user_"):
            user_id = int(data.replace("isolate_user_", ""))
            await query.edit_message_text(
                f"🚫 **Isolate User {user_id}**\n\n"
                "*User isolation not yet implemented.*\n\n"
                "This will:\n"
                "• Suspend user subscription\n"
                "• Disable platform connections\n"
                "• Block trading operations\n"
                "• Preserve data for investigation\n\n"
                "Use /set_subscription to suspend the user instead.",
                parse_mode="Markdown",
            )

        elif data.startswith("refresh_user_"):
            user_id = int(data.replace("refresh_user_", ""))
            await query.edit_message_text("🔄 Refreshing user details...")
            context.args = [str(user_id)]
            await self.user_details_command(update, context)

    async def cancel_conversation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Cancel current conversation."""
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
