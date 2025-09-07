#!/usr/bin/env python3
"""
Script to check admin user setup in database
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import config
from src.database import get_db_session
from src.models.telegram_users import SubscriptionStatus, TelegramUser, UserRole
from src.services.user_manager import UserManager


def check_admin_setup():
    """Check admin user configuration and database setup"""
    print("=== Admin Configuration Check ===")

    # Check environment configuration
    print(f"Telegram Chat ID from config: {config.telegram.chat_id}")
    print(
        f"Telegram Bot Token configured: {'Yes' if config.telegram.bot_token else 'No'}"
    )

    # Check UserManager initial admin ID
    user_manager = UserManager()
    print(f"UserManager initial admin ID: {user_manager.initial_admin_id}")

    # Check if they match
    if config.telegram.chat_id == user_manager.initial_admin_id:
        print("✅ Chat ID matches UserManager initial admin ID")
    else:
        print("❌ Chat ID does NOT match UserManager initial admin ID")

    print("\n=== Database User Check ===")

    try:
        with get_db_session() as session:
            # Check if admin user exists in database
            admin_user = (
                session.query(TelegramUser)
                .filter(TelegramUser.telegram_id == config.telegram.chat_id)
                .first()
            )

            if admin_user:
                print(f"✅ Admin user found in database:")
                print(f"   - Telegram ID: {admin_user.telegram_id}")
                print(f"   - Username: {admin_user.username}")
                print(f"   - First Name: {admin_user.first_name}")
                print(f"   - Role: {admin_user.role.value}")
                print(f"   - Is Admin: {admin_user.is_admin}")
                print(f"   - Is Active: {admin_user.is_active}")
                print(f"   - Subscription: {admin_user.subscription_status.value}")

                if admin_user.is_admin:
                    print("✅ User has admin privileges")
                else:
                    print("❌ User does NOT have admin privileges")
            else:
                print("❌ Admin user NOT found in database")
                print(
                    "   This user needs to be created by sending a message to the bot"
                )

            # List all users in database
            all_users = session.query(TelegramUser).all()
            print(f"\n=== All Users in Database ({len(all_users)} total) ===")
            for user in all_users:
                print(
                    f"ID: {user.telegram_id}, Role: {user.role.value}, Admin: {user.is_admin}, Active: {user.is_active}"
                )

    except Exception as e:
        print(f"❌ Database error: {e}")

    print("\n=== Recommendations ===")
    if config.telegram.chat_id != user_manager.initial_admin_id:
        print(
            "1. Update TELEGRAM_CHAT_ID in .env to match UserManager initial_admin_id"
        )
        print("   OR update UserManager.initial_admin_id to match TELEGRAM_CHAT_ID")

    try:
        with get_db_session() as session:
            admin_user = (
                session.query(TelegramUser)
                .filter(TelegramUser.telegram_id == config.telegram.chat_id)
                .first()
            )

            if not admin_user:
                print(
                    "2. Send a message to the bot from the admin Telegram account to create the user"
                )
            elif not admin_user.is_admin:
                print("3. Update the user's role to admin in the database")

    except Exception:
        pass


if __name__ == "__main__":
    check_admin_setup()
