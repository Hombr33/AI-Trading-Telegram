"""
Database session management utilities.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from .connection import get_database_connection


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


def get_db_session_direct() -> Session:
    """Get a database session directly (caller must close)."""
    return get_database_connection().get_session()
