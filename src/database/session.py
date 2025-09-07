"""
Database session management utilities.
"""

import asyncio
import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.exc import DisconnectionError, OperationalError
from sqlalchemy.orm import Session

from .connection import get_database_connection

logger = logging.getLogger(__name__)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup."""
    db = get_database_connection().get_session()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_session_with_retry(max_retries: int = 3) -> Generator[Session, None, None]:
    """Get a database session with retry logic for I/O errors."""
    for attempt in range(max_retries):
        try:
            db = get_database_connection().get_session()
            try:
                yield db
                return  # Success, exit the retry loop
            except (OperationalError, DisconnectionError) as e:
                error_msg = str(e).lower()
                if "disk i/o error" in error_msg or "database is locked" in error_msg:
                    logger.warning(
                        f"SQLite I/O error on attempt {attempt + 1}/{max_retries}: {e}"
                    )
                    db.rollback()
                    db.close()

                    if attempt < max_retries - 1:
                        # Wait before retry with exponential backoff
                        wait_time = 2**attempt
                        logger.info(
                            f"Retrying database operation in {wait_time} seconds..."
                        )
                        import time

                        time.sleep(wait_time)

                        # Try to reconnect
                        try:
                            db_conn = get_database_connection()
                            if hasattr(db_conn, "close"):
                                db_conn.close()
                            db_conn.connect()
                            logger.info("Database reconnection attempted")
                        except Exception as reconnect_error:
                            logger.error(
                                f"Failed to reconnect to database: {reconnect_error}"
                            )
                    else:
                        logger.error(
                            f"Failed to get database session after {max_retries} attempts: {e}"
                        )
                        raise
                else:
                    # Re-raise non-I/O related database errors
                    db.rollback()
                    db.close()
                    raise
            except Exception as e:
                db.rollback()
                db.close()
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database session error on attempt {attempt + 1}: {e}")
                import time

                time.sleep(1)
            else:
                logger.error(
                    f"Failed to get database session after {max_retries} attempts: {e}"
                )
                raise


def get_db_session_direct() -> Session:
    """Get a database session directly (caller must close)."""
    return get_database_connection().get_session()


def SessionLocal() -> Session:
    """Get a database session. This is an alias for get_db_session_direct."""
    return get_db_session_direct()
