"""
Database connection management.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from .config import DatabaseConfig
from src.models import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine = None
_session_factory = None


class DatabaseConnection:
    """Database connection manager."""

    def __init__(self, config: DatabaseConfig):
        """Initialize database connection."""
        self.config = config
        self.engine = None
        self.session_factory = None

    def connect(self) -> None:
        """Create database engine and session factory."""
        try:
            # Create engine with SQLite-specific configuration
            self.engine = create_engine(
                self.config.url,
                echo=self.config.echo,
                pool_pre_ping=True,
                pool_recycle=3600,
            )

            # Configure SQLite pragmas
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()

            # Create session factory
            self.session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )

            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to establish database connection: {e}")
            raise

    def create_tables(self) -> None:
        """Create all tables."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    def drop_tables(self) -> None:
        """Drop all tables."""
        try:
            Base.metadata.drop_all(self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise

    def get_session(self) -> Session:
        """Get a new database session."""
        if not self.session_factory:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


def get_database_connection() -> DatabaseConnection:
    """Get database connection instance."""
    global _engine, _session_factory

    if _engine is None:
        config = DatabaseConfig.from_env()
        db_conn = DatabaseConnection(config)
        db_conn.connect()
        _engine = db_conn.engine
        _session_factory = db_conn.session_factory
        return db_conn

    # Return existing connection
    config = DatabaseConfig.from_env()
    db_conn = DatabaseConnection(config)
    db_conn.engine = _engine
    db_conn.session_factory = _session_factory
    return db_conn


def close_database_connection() -> None:
    """Close database connection."""
    global _engine, _session_factory

    if _engine:
        _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database connection closed")


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session context manager."""
    db_conn = get_database_connection()
    with db_conn.session_scope() as session:
        yield session


def get_db_session_direct() -> Session:
    """Get database session directly (caller must manage lifecycle)."""
    db_conn = get_database_connection()
    return db_conn.get_session()
