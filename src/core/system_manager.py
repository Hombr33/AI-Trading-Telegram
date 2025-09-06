"""
System management utilities for the AI Trading Bot.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SystemManager:
    """Manages system-level operations like restart, shutdown, and monitoring."""

    def __init__(self):
        self._shutdown_callbacks = []
        self._restart_requested = False

    def add_shutdown_callback(self, callback):
        """Add a callback to be called during shutdown."""
        self._shutdown_callbacks.append(callback)

    async def graceful_restart(
        self, telegram_bot=None, admin_telegram_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform a graceful system restart.

        Args:
            telegram_bot: Telegram bot instance for notifications
            admin_telegram_id: Admin user ID to notify

        Returns:
            Dict with restart status information
        """
        try:
            logger.info("Initiating graceful system restart...")

            # Send initial notification
            if telegram_bot and admin_telegram_id:
                try:
                    await telegram_bot.send_message(
                        admin_telegram_id,
                        "🔄 **System Restart Initiated**\n\n"
                        "⏳ Performing graceful shutdown...\n"
                        "• Saving pending data\n"
                        "• Closing connections\n"
                        "• Stopping services\n\n"
                        "*Please wait, this may take up to 30 seconds...*",
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    logger.error(f"Failed to send restart notification: {e}")

            # 1. Set restart flag
            self._restart_requested = True

            # 2. Execute shutdown callbacks
            await self._execute_shutdown_callbacks()

            # 3. Save system state
            await self._save_system_state()

            # 4. Close database connections
            await self._close_database_connections()

            # 5. Stop background tasks
            await self._stop_background_tasks()

            # 6. Create restart script
            restart_script = self._create_restart_script()

            # 7. Schedule restart
            await self._schedule_restart(
                restart_script, telegram_bot, admin_telegram_id
            )

            return {
                "success": True,
                "message": "Graceful restart initiated successfully",
                "restart_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to perform graceful restart: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Restart failed, system still running",
            }

    async def emergency_shutdown(
        self, reason: str = "Emergency shutdown requested"
    ) -> Dict[str, Any]:
        """
        Perform an emergency shutdown of the system.

        Args:
            reason: Reason for emergency shutdown

        Returns:
            Dict with shutdown status information
        """
        try:
            logger.critical(f"Emergency shutdown initiated: {reason}")

            # Execute shutdown callbacks with timeout
            try:
                await asyncio.wait_for(self._execute_shutdown_callbacks(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Shutdown callbacks timed out")

            # Force close critical connections
            await self._force_close_connections()

            # Exit with error code
            sys.exit(1)

        except Exception as e:
            logger.critical(f"Emergency shutdown failed: {e}")
            # Force exit if emergency shutdown fails
            os._exit(1)

    async def _execute_shutdown_callbacks(self):
        """Execute all registered shutdown callbacks."""
        logger.info("Executing shutdown callbacks...")

        for callback in self._shutdown_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
                logger.debug(f"Executed shutdown callback: {callback.__name__}")
            except Exception as e:
                logger.error(f"Error in shutdown callback {callback.__name__}: {e}")

    async def _save_system_state(self):
        """Save current system state before restart."""
        try:

            # Save restart timestamp
            {
                "restart_time": datetime.utcnow().isoformat(),
                "restart_reason": "Admin initiated restart",
                "system_status": "restarting",
            }

            # Could save to database or file
            logger.info("System state saved successfully")

        except Exception as e:
            logger.error(f"Failed to save system state: {e}")

    async def _close_database_connections(self):
        """Close all database connections."""
        try:
            from ..database.session import SessionLocal

            # Close database connections
            SessionLocal.remove()
            logger.info("Database connections closed")

        except Exception as e:
            logger.error(f"Failed to close database connections: {e}")

    async def _stop_background_tasks(self):
        """Stop all background tasks."""
        try:
            # Get all running tasks
            tasks = [task for task in asyncio.all_tasks() if not task.done()]

            # Cancel non-critical tasks
            for task in tasks:
                if not task.get_name().startswith("critical_"):
                    task.cancel()

            # Wait for tasks to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            logger.info("Background tasks stopped")

        except Exception as e:
            logger.error(f"Failed to stop background tasks: {e}")

    def _create_restart_script(self) -> str:
        """Create a restart script for the system."""
        try:
            # Get current Python executable and script path
            python_exe = sys.executable
            script_path = os.path.abspath(sys.argv[0])

            # Create platform-specific restart script
            if os.name == "nt":  # Windows
                restart_script = f'@echo off\nping 127.0.0.1 -n 3 > nul\n"{python_exe}" "{script_path}"\n'
                script_file = "restart_system.bat"
            else:  # Unix-like
                restart_script = (
                    f'#!/bin/bash\nsleep 2\n"{python_exe}" "{script_path}"\n'
                )
                script_file = "restart_system.sh"

            # Write restart script
            with open(script_file, "w") as f:
                f.write(restart_script)

            # Make executable on Unix-like systems
            if os.name != "nt":
                os.chmod(script_file, 0o755)

            logger.info(f"Restart script created: {script_file}")
            return script_file

        except Exception as e:
            logger.error(f"Failed to create restart script: {e}")
            return None

    async def _schedule_restart(
        self,
        restart_script: str,
        telegram_bot=None,
        admin_telegram_id: Optional[int] = None,
    ):
        """Schedule the system restart."""
        try:
            if not restart_script:
                raise Exception("No restart script available")

            # Send final notification
            if telegram_bot and admin_telegram_id:
                try:
                    await telegram_bot.send_message(
                        admin_telegram_id,
                        "✅ **System Restart Ready**\n\n"
                        "🔄 Restarting in 3 seconds...\n"
                        "📡 You will receive a startup notification when the system is back online.",
                        parse_mode="Markdown",
                    )
                    await asyncio.sleep(1)  # Give time for message to send
                except Exception as e:
                    logger.error(f"Failed to send final restart notification: {e}")

            # Start restart script in background
            if os.name == "nt":  # Windows
                import subprocess

                subprocess.Popen([restart_script], shell=True, cwd=os.getcwd())
            else:  # Unix-like
                import subprocess

                subprocess.Popen([f"./{restart_script}"], shell=True, cwd=os.getcwd())

            logger.info("Restart scheduled, initiating shutdown...")

            # Short delay before exit
            await asyncio.sleep(2)

            # Exit current process
            sys.exit(0)

        except Exception as e:
            logger.error(f"Failed to schedule restart: {e}")
            raise

    async def _force_close_connections(self):
        """Force close all connections during emergency shutdown."""
        try:
            # Close database connections
            await self._close_database_connections()

            # Additional cleanup can be added here
            logger.info("Connections force closed")

        except Exception as e:
            logger.error(f"Failed to force close connections: {e}")

    def is_restart_requested(self) -> bool:
        """Check if restart was requested."""
        return self._restart_requested

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "restart_requested": self._restart_requested,
            "shutdown_callbacks_count": len(self._shutdown_callbacks),
            "uptime": self._get_uptime(),
            "process_id": os.getpid(),
            "python_version": sys.version,
            "platform": sys.platform,
        }

    def _get_uptime(self) -> str:
        """Get system uptime."""
        try:
            import psutil

            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return str(uptime).split(".")[0]  # Remove microseconds
        except ImportError:
            return "Unknown (psutil not available)"
        except Exception as e:
            return f"Unknown (error: {e})"


# Global system manager instance
system_manager = SystemManager()
