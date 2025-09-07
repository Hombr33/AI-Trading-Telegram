"""
Database health check and maintenance utilities.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.exc import DisconnectionError, OperationalError

from .connection import get_database_connection
from .session import get_db_session_with_retry

logger = logging.getLogger(__name__)


class DatabaseHealthChecker:
    """Database health monitoring and maintenance."""

    def __init__(self):
        self.last_check_time = 0
        self.check_interval = 300  # 5 minutes
        self.health_status = "unknown"
        self.last_error = None

    async def check_database_health(self) -> Dict[str, Any]:
        """Check database health and return status."""
        current_time = time.time()

        # Skip if checked recently
        if current_time - self.last_check_time < self.check_interval:
            return {
                "status": self.health_status,
                "last_check": self.last_check_time,
                "last_error": self.last_error,
            }

        try:
            with get_db_session_with_retry(max_retries=2) as db:
                # Test basic connectivity
                result = db.execute(text("SELECT 1")).fetchone()

                # Check database file size and integrity
                db_path = self._get_database_path()
                file_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

                # Check WAL file status
                wal_path = f"{db_path}-wal"
                wal_exists = os.path.exists(wal_path)
                wal_size = os.path.getsize(wal_path) if wal_exists else 0

                # Run PRAGMA integrity_check (lightweight)
                integrity_result = db.execute(text("PRAGMA quick_check")).fetchone()
                integrity_ok = (
                    integrity_result[0] == "ok" if integrity_result else False
                )

                self.health_status = "healthy"
                self.last_error = None
                self.last_check_time = current_time

                return {
                    "status": "healthy",
                    "last_check": current_time,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "wal_exists": wal_exists,
                    "wal_size_mb": (
                        round(wal_size / (1024 * 1024), 2) if wal_exists else 0
                    ),
                    "integrity_check": integrity_ok,
                    "last_error": None,
                }

        except (OperationalError, DisconnectionError) as e:
            error_msg = str(e).lower()
            if "disk i/o error" in error_msg or "database is locked" in error_msg:
                self.health_status = "io_error"
                self.last_error = str(e)
                self.last_check_time = current_time

                logger.warning(f"Database I/O error detected: {e}")
                return {
                    "status": "io_error",
                    "last_check": current_time,
                    "last_error": str(e),
                    "error_type": "io_error",
                }
            else:
                self.health_status = "error"
                self.last_error = str(e)
                self.last_check_time = current_time

                logger.error(f"Database error: {e}")
                return {
                    "status": "error",
                    "last_check": current_time,
                    "last_error": str(e),
                    "error_type": "database_error",
                }

        except Exception as e:
            self.health_status = "error"
            self.last_error = str(e)
            self.last_check_time = current_time

            logger.error(f"Unexpected database health check error: {e}")
            return {
                "status": "error",
                "last_check": current_time,
                "last_error": str(e),
                "error_type": "unexpected_error",
            }

    def _get_database_path(self) -> str:
        """Get the database file path."""
        try:
            db_conn = get_database_connection()
            url = db_conn.config.url
            # Extract path from sqlite:///./path/to/db
            if url.startswith("sqlite:///"):
                return url.replace("sqlite:///", "")
            return url
        except Exception:
            return "./runtime/data/trade.sqlite3"

    async def perform_maintenance(self) -> Dict[str, Any]:
        """Perform database maintenance operations."""
        try:
            with get_db_session_with_retry(max_retries=2) as db:
                # Run VACUUM to reclaim space and optimize
                logger.info("Starting database VACUUM...")
                db.execute(text("VACUUM"))

                # Run ANALYZE to update statistics
                logger.info("Starting database ANALYZE...")
                db.execute(text("ANALYZE"))

                # Check WAL file and checkpoint if needed
                wal_checkpoint_result = db.execute(
                    text("PRAGMA wal_checkpoint(TRUNCATE)")
                ).fetchone()

                logger.info("Database maintenance completed successfully")
                return {
                    "status": "success",
                    "vacuum_completed": True,
                    "analyze_completed": True,
                    "wal_checkpoint": (
                        wal_checkpoint_result[0] if wal_checkpoint_result else None
                    ),
                }

        except Exception as e:
            logger.error(f"Database maintenance failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def recover_from_io_error(self) -> bool:
        """Attempt to recover from I/O errors."""
        try:
            logger.info("Attempting database recovery from I/O error...")

            # Try to reconnect
            db_conn = get_database_connection()
            if hasattr(db_conn, "close"):
                db_conn.close()

            # Wait a moment
            await asyncio.sleep(2)

            # Reconnect
            db_conn.connect()

            # Test the connection
            health = await self.check_database_health()

            if health["status"] == "healthy":
                logger.info("Database recovery successful")
                return True
            else:
                logger.error(f"Database recovery failed: {health.get('last_error')}")
                return False

        except Exception as e:
            logger.error(f"Database recovery error: {e}")
            return False


# Global health checker instance
_health_checker = DatabaseHealthChecker()


async def check_database_health() -> Dict[str, Any]:
    """Check database health."""
    return await _health_checker.check_database_health()


async def perform_database_maintenance() -> Dict[str, Any]:
    """Perform database maintenance."""
    return await _health_checker.perform_maintenance()


async def recover_database_from_io_error() -> bool:
    """Recover from database I/O errors."""
    return await _health_checker.recover_from_io_error()
