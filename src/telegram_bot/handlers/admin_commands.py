"""
Telegram bot command handlers for admin operations.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from ...services.user_manager import UserManager
from ...services.config_manager import ConfigManager
from ...core.system_manager import system_manager

# EABridge import moved to method level to avoid circular imports
from ...models.telegram_users import SubscriptionStatus

logger = logging.getLogger(__name__)

# Conversation states
WAITING_USER_ID, WAITING_SUBSCRIPTION_STATUS, WAITING_SERVER_CONFIG = range(3)


class AdminCommandHandlers:
    """Handlers for admin-only commands."""

    def __init__(self):
        self.user_manager = UserManager()
        self.config_manager = ConfigManager()
        # Lazy initialization to avoid circular imports
        self.ea_bridge = None

    def _get_ea_bridge(self):
        """Get EABridge with lazy initialization."""
        if self.ea_bridge is None:
            try:
                from ...bridge.ea_bridge import EABridge

                self.ea_bridge = EABridge()
            except ImportError:
                logger.warning("EABridge not available due to import issues")
                self.ea_bridge = None
        return self.ea_bridge

    async def users_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /users command (admin only)."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            await update.message.reply_text("❌ Admin privileges required.")
            return

        users = await self.user_manager.get_all_users(telegram_id)

        if not users:
            await update.message.reply_text("📊 No registered users found.")
            return

        message = "👥 **Registered Users:**\n\n"

        for user in users:
            status_emoji = "✅" if user["is_active"] else "❌"
            role_emoji = "👑" if user["role"] == "admin" else "👤"
            sub_emoji = "💎" if user["subscription_status"] == "active" else "⏸️"

            message += f"""{status_emoji} {role_emoji} **{user['first_name'] or 'N/A'}** (@{user['username'] or 'N/A'})
ID: `{user['telegram_id']}`
Role: {user['role'].title()}
Subscription: {sub_emoji} {user['subscription_status'].title()}
Joined: {user['created_at'].strftime('%Y-%m-%d')}

"""

        # Split message if too long
        if len(message) > 4000:
            messages = [message[i : i + 4000] for i in range(0, len(message), 4000)]
            for msg in messages:
                await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(message, parse_mode="Markdown")

    async def add_admin_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle /add_admin command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            await update.message.reply_text("❌ Admin privileges required.")
            return ConversationHandler.END

        if context.args:
            # User ID provided as argument
            try:
                target_user_id = int(context.args[0])
                success = await self.user_manager.add_admin(telegram_id, target_user_id)

                if success:
                    await update.message.reply_text(
                        f"✅ User {target_user_id} promoted to admin."
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Failed to promote user {target_user_id}. User may not exist."
                    )

                return ConversationHandler.END
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID format.")
                return ConversationHandler.END

        await update.message.reply_text(
            "👑 **Add Administrator**\n\nPlease send the Telegram user ID to promote:"
        )
        return WAITING_USER_ID

    async def handle_add_admin_user_id(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle user ID input for add admin."""
        telegram_id = update.effective_user.id

        try:
            target_user_id = int(update.message.text.strip())
            success = await self.user_manager.add_admin(telegram_id, target_user_id)

            if success:
                await update.message.reply_text(
                    f"✅ User {target_user_id} promoted to admin."
                )
            else:
                await update.message.reply_text(
                    f"❌ Failed to promote user {target_user_id}. User may not exist."
                )

        except ValueError:
            await update.message.reply_text(
                "❌ Invalid user ID. Please send a numeric user ID:"
            )
            return WAITING_USER_ID

        return ConversationHandler.END

    async def remove_admin_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle /remove_admin command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            await update.message.reply_text("❌ Admin privileges required.")
            return ConversationHandler.END

        if context.args:
            try:
                target_user_id = int(context.args[0])
                success = await self.user_manager.remove_admin(
                    telegram_id, target_user_id
                )

                if success:
                    await update.message.reply_text(
                        f"✅ Admin privileges removed from user {target_user_id}."
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Failed to remove admin privileges. User may not be admin or is the initial admin."
                    )

                return ConversationHandler.END
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID format.")
                return ConversationHandler.END

        await update.message.reply_text(
            "👤 **Remove Administrator**\n\nPlease send the Telegram user ID to demote:"
        )
        return WAITING_USER_ID

    async def handle_remove_admin_user_id(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle user ID input for remove admin."""
        telegram_id = update.effective_user.id

        try:
            target_user_id = int(update.message.text.strip())
            success = await self.user_manager.remove_admin(telegram_id, target_user_id)

            if success:
                await update.message.reply_text(
                    f"✅ Admin privileges removed from user {target_user_id}."
                )
            else:
                await update.message.reply_text(
                    f"❌ Failed to remove admin privileges. User may not be admin or is the initial admin."
                )

        except ValueError:
            await update.message.reply_text(
                "❌ Invalid user ID. Please send a numeric user ID:"
            )
            return WAITING_USER_ID

        return ConversationHandler.END

    async def set_subscription_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle /set_subscription command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            await update.message.reply_text("❌ Admin privileges required.")
            return ConversationHandler.END

        if len(context.args) >= 2:
            try:
                target_user_id = int(context.args[0])
                status_str = context.args[1].lower()

                if status_str == "active":
                    status = SubscriptionStatus.ACTIVE
                elif status_str == "expired":
                    status = SubscriptionStatus.EXPIRED
                elif status_str == "suspended":
                    status = SubscriptionStatus.SUSPENDED
                else:
                    await update.message.reply_text(
                        "❌ Invalid status. Use: active, expired, or suspended"
                    )
                    return ConversationHandler.END

                success = await self.user_manager.set_subscription(
                    telegram_id, target_user_id, status
                )

                if success:
                    await update.message.reply_text(
                        f"✅ Subscription for user {target_user_id} set to {status.value}."
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Failed to update subscription. User may not exist."
                    )

                return ConversationHandler.END
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID format.")
                return ConversationHandler.END

        await update.message.reply_text(
            """💎 **Set User Subscription**

Format: /set_subscription <user_id> <status>

Status options:
- active: Full access to trading system
- expired: No access to trading features
- suspended: Temporarily disabled

Please send the user ID:"""
        )
        return WAITING_USER_ID

    async def server_config_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /server_config command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            message = "❌ Admin privileges required."
            if update.callback_query:
                await update.callback_query.answer(message)
                return
            await update.message.reply_text(message)
            return

        configs = await self.config_manager.get_all_server_configs(telegram_id)

        if not configs:
            message = "⚙️ *Server Configuration*\n\nNo server configurations found."
        else:
            message = "⚙️ *Server Configuration*\n\n"
            for key, config in configs.items():
                message += f"*{key}:*\n`{config['value']}`\n"
                if config["description"]:
                    message += f"_{config['description']}_\n"
                message += (
                    f"Updated: {config['updated_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
                )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔧 Edit Config", callback_data="server_config_edit"
                )
            ],
            [InlineKeyboardButton("➕ Add Config", callback_data="server_config_add")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="server_config_refresh")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                message, reply_markup=reply_markup, parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                message, reply_markup=reply_markup, parse_mode="Markdown"
            )

    async def restart_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /restart command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            await update.message.reply_text("❌ Admin privileges required.")
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Restart System", callback_data="confirm_restart"
                )
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_restart")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            """⚠️ **System Restart Confirmation**

This will restart the entire trading system:
- All connections will be temporarily lost
- Active positions will remain open
- System will be unavailable for ~30 seconds

Are you sure you want to restart?""",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def logs_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /logs command."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            message = "❌ Admin privileges required."
            if update.callback_query:
                await update.callback_query.answer(message)
                return
            await update.message.reply_text(message)
            return

        # Get recent logs (implementation depends on logging setup)
        keyboard = [
            [InlineKeyboardButton("📊 System Logs", callback_data="logs_system")],
            [InlineKeyboardButton("📈 Trading Logs", callback_data="logs_trading")],
            [InlineKeyboardButton("❌ Error Logs", callback_data="logs_error")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="logs_refresh")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = "📋 **System Logs**\n\nSelect log category to view:"

        if update.callback_query:
            await update.callback_query.edit_message_text(
                message_text, reply_markup=reply_markup, parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                message_text, reply_markup=reply_markup, parse_mode="Markdown"
            )

    async def close_all_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /close_all command (emergency)."""
        telegram_id = update.effective_user.id

        if not await self.user_manager.is_admin(telegram_id):
            message = "❌ Admin privileges required."
            if update.callback_query:
                await update.callback_query.answer(message)
                return
            await update.message.reply_text(message)
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "🚨 CLOSE ALL POSITIONS", callback_data="confirm_close_all"
                )
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_close_all")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = """🚨 **EMERGENCY: Close All Positions**

⚠️ **WARNING:** This will close ALL open positions across ALL users!

This action should only be used in emergency situations:
- Market crisis
- System malfunction
- Risk management emergency

**This action cannot be undone!**

Are you absolutely sure?"""

        if update.callback_query:
            await update.callback_query.edit_message_text(
                message_text, reply_markup=reply_markup, parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                message_text, reply_markup=reply_markup, parse_mode="Markdown"
            )

    async def handle_admin_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle admin callback queries."""
        query = update.callback_query
        await query.answer()

        telegram_id = query.from_user.id
        data = query.data

        if not await self.user_manager.is_admin(telegram_id):
            await query.edit_message_text("❌ Admin privileges required.")
            return

        # Handle main admin menu callbacks
        if data == "users":
            # Handle users callback directly
            try:
                users = await self.user_manager.get_all_users(telegram_id)

                if not users:
                    await query.edit_message_text("📊 No registered users found.")
                    return

                message = "👥 *Registered Users:*\n\n"

                for user in users:
                    status_emoji = "✅" if user["is_active"] else "❌"
                    role_emoji = "👑" if user["role"] == "admin" else "👤"
                    sub_emoji = "💎" if user["subscription_status"] == "active" else "⏸️"

                    # Escape special characters in usernames
                    first_name = (
                        (user["first_name"] or "N/A")
                        .replace("_", "\\_")
                        .replace("*", "\\*")
                        .replace("[", "\\[")
                        .replace("]", "\\]")
                        .replace("(", "\\(")
                        .replace(")", "\\)")
                    )
                    username = (
                        (user["username"] or "N/A")
                        .replace("_", "\\_")
                        .replace("*", "\\*")
                        .replace("[", "\\[")
                        .replace("]", "\\]")
                        .replace("(", "\\(")
                        .replace(")", "\\)")
                    )

                    message += f"""{status_emoji} {role_emoji} {first_name} (@{username})
ID: {user['telegram_id']}
Role: {user['role'].title()}
Subscription: {sub_emoji} {user['subscription_status'].title()}
Joined: {user['created_at'].strftime('%Y-%m-%d')}

"""

                # Split message if too long
                if len(message) > 4000:
                    messages = [
                        message[i : i + 4000] for i in range(0, len(message), 4000)
                    ]
                    for i, msg in enumerate(messages):
                        if i == 0:
                            await query.edit_message_text(msg, parse_mode="Markdown")
                        else:
                            await query.message.reply_text(msg, parse_mode="Markdown")
                else:
                    await query.edit_message_text(message, parse_mode="Markdown")

            except Exception as e:
                logger.error(f"Error in users callback: {e}")
                await query.edit_message_text("❌ Error retrieving users list.")

        elif data == "add_admin":
            await query.edit_message_text(
                "👑 *Add Administrator*\n\n"
                "To add a new admin, use the command:\n"
                "`/add_admin <user_id>`\n\n"
                "Example: `/add_admin 123456789`\n\n"
                "The user must have sent at least one message to the bot first.",
                parse_mode="Markdown",
            )

        elif data == "set_subscription":
            await query.edit_message_text(
                "💎 *Manage Subscriptions*\n\n"
                "To manage user subscriptions, use:\n"
                "`/set_subscription <user_id> <status>`\n\n"
                "Status options: `active`, `expired`, `suspended`\n\n"
                "Example: `/set_subscription 123456789 active`",
                parse_mode="Markdown",
            )

        elif data == "server_config":
            await self.server_config_command(update, context)

        elif data == "restart":
            await query.edit_message_text(
                "🔄 *System Restart*\n\n"
                "⚠️ *Warning*: This will restart the entire trading system.\n"
                "All active connections will be temporarily interrupted.\n\n"
                "*What happens during restart:*\n"
                "• Bot will stop responding temporarily\n"
                "• All services will be restarted\n"
                "• Connections will be re-established\n"
                "• System will resume normal operation\n\n"
                "*Note*: This feature is not yet implemented.\n"
                "Please restart manually using the server console.",
                parse_mode="Markdown",
            )

        elif data == "logs":
            await self.logs_command(update, context)

        elif data == "close_all":
            await self.close_all_command(update, context)

        # Handle confirmation callbacks
        elif data == "confirm_restart":
            await query.edit_message_text(
                "🔄 *System Restart Initiated*\n\nRestarting trading system..."
            )

            # Get telegram bot instance for notifications
            telegram_bot = getattr(context, "bot", None)
            admin_telegram_id = query.from_user.id

            try:
                # Perform graceful restart using system manager
                restart_result = await system_manager.graceful_restart(
                    telegram_bot=telegram_bot, admin_telegram_id=admin_telegram_id
                )

                if not restart_result["success"]:
                    await query.edit_message_text(
                        f"❌ *Restart Failed*\n\n"
                        f"Error: {restart_result.get('error', 'Unknown error')}\n\n"
                        f"System is still running normally.",
                        parse_mode="Markdown",
                    )
            except Exception as e:
                logger.error(f"Restart failed: {e}")
                await query.edit_message_text(
                    f"❌ *Restart Failed*\n\n"
                    f"Error: {str(e)}\n\n"
                    f"System is still running normally.",
                    parse_mode="Markdown",
                )

        elif data == "cancel_restart":
            await query.edit_message_text("❌ System restart cancelled.")

        elif data == "confirm_close_all":
            await query.edit_message_text(
                "🚨 *Closing All Positions*\n\nEmergency position closure in progress..."
            )

            admin_telegram_id = query.from_user.id

            try:
                # Get multi-user service for position management
                from ...services.multi_user_service import MultiUserService

                # Initialize if not already available
                if not hasattr(self, "multi_user_service"):
                    # This should ideally be injected, but for now we'll access it
                    # through the application context or create a new instance
                    pass

                # Get all users
                all_users = await self.user_manager.get_all_users(admin_telegram_id)

                if not all_users:
                    await query.edit_message_text(
                        "❌ *No users found*\n\nNo active users to close positions for.",
                        parse_mode="Markdown",
                    )
                    return

                closed_positions = 0
                failed_closures = 0
                processed_users = 0

                # Close positions for each user
                for user in all_users:
                    user_telegram_id = user["telegram_id"]

                    try:
                        # Get EA bridge for this user
                        ea_bridge = self._get_ea_bridge()
                        if ea_bridge:
                            # Get user positions
                            positions = await ea_bridge.get_positions_from_ea(
                                user_telegram_id
                            )

                            if positions:
                                # Close each position
                                for position in positions:
                                    try:
                                        close_result = await ea_bridge.close_position(
                                            user_telegram_id, position.get("ticket")
                                        )
                                        if close_result.get("success"):
                                            closed_positions += 1
                                        else:
                                            failed_closures += 1
                                    except Exception as e:
                                        logger.error(
                                            f"Failed to close position {position.get('ticket')} for user {user_telegram_id}: {e}"
                                        )
                                        failed_closures += 1

                        processed_users += 1

                    except Exception as e:
                        logger.error(f"Failed to process user {user_telegram_id}: {e}")
                        failed_closures += 1

                # Send final report
                if closed_positions > 0 or failed_closures > 0:
                    message = f"🚨 *Emergency Position Closure Complete*\n\n"
                    message += f"📊 **Summary:**\n"
                    message += f"• Users processed: {processed_users}\n"
                    message += f"• Positions closed: {closed_positions}\n"
                    message += f"• Failed closures: {failed_closures}\n\n"

                    if failed_closures > 0:
                        message += f"⚠️ Some positions could not be closed. Check logs for details.\n\n"

                    message += f"✅ Emergency procedure completed at {datetime.now().strftime('%H:%M:%S UTC')}"
                else:
                    message = f"ℹ️ *No Open Positions Found*\n\nNo positions were found to close across all users."

                await query.edit_message_text(message, parse_mode="Markdown")

                # Send admin alert
                if hasattr(self, "telegram_bot") and self.telegram_bot:
                    await self.telegram_bot.send_admin_alert(
                        f"Emergency close all executed by admin {admin_telegram_id}. "
                        f"Closed: {closed_positions}, Failed: {failed_closures}"
                    )

            except Exception as e:
                logger.error(f"Emergency close all failed: {e}")
                await query.edit_message_text(
                    f"❌ *Emergency Close Failed*\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Manual intervention may be required.",
                    parse_mode="Markdown",
                )

        elif data == "cancel_close_all":
            await query.edit_message_text("❌ Emergency close cancelled.")

        elif data.startswith("server_config_"):
            action = data.replace("server_config_", "")

            if action == "refresh":
                # Refresh server config display
                await self.server_config_command(update, context)
            elif action == "edit":
                await query.edit_message_text(
                    "🔧 *Edit Server Configuration*\n\n"
                    "*Feature not yet implemented.*\n\n"
                    "This will allow you to modify existing server configurations.\n"
                    "Use `/server_config` to view current configurations.",
                    parse_mode="Markdown",
                )
            elif action == "add":
                await query.edit_message_text(
                    "➕ *Add Server Configuration*\n\n"
                    "*Feature not yet implemented.*\n\n"
                    "This will allow you to add new server configurations.\n"
                    "Use `/server_config` to view current configurations.",
                    parse_mode="Markdown",
                )

        elif data.startswith("logs_"):
            log_type = data.replace("logs_", "")

            if log_type in ["system", "trading", "error", "refresh"]:
                if log_type == "refresh":
                    await self.logs_command(update, context)
                else:
                    message_text = (
                        f"📋 *{log_type.title()} Logs*\n\n"
                        f"🔍 *Log Category*: {log_type.title()}\n\n"
                        f"*Status*: Log viewing interface is not yet implemented.\n\n"
                        f"*Available Options*:\n"
                        f"• Check server log files directly\n"
                        f"• Use system monitoring tools\n"
                        f"• Contact administrator for log access\n\n"
                        f"*Note*: This feature will be implemented in a future update."
                    )
                    await query.edit_message_text(message_text, parse_mode="Markdown")

    async def cancel_conversation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Cancel current conversation."""
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
