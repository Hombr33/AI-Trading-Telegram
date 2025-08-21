"""
Database connection management for the AI Trading Bot system.
"""

import os
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from .config import DatabaseConfig
from ..models import Base


class DatabaseConnection:
    """Database connection manager."""
    
    def __init__(self, config: DatabaseConfig):
        """Initialize database connection."""
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
        self._setup_session_factory()
    
    def _setup_engine(self) -> None:
        """Set up the database engine."""
        if self.config.url.startswith("sqlite"):
            # SQLite specific configuration
            self.engine = create_engine(
                self.config.url,
                echo=self.config.echo,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30,
                },
                poolclass=StaticPool,
            )
            
            # Set up SQLite PRAGMA statements
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragmas(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                pragmas = self.config.get_sqlite_pragmas()
                for pragma, value in pragmas.items():
                    cursor.execute(f"PRAGMA {pragma}={value}")
                cursor.close()
        else:
            # Other database types
            self.engine = create_engine(
                self.config.url,
                echo=self.config.echo,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
            )
    
    def _setup_session_factory(self) -> None:
        """Set up the session factory."""
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
    
    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self) -> None:
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
    
    def close(self) -> None:
        """Close the database connection."""
        if self.engine:
            self.engine.dispose()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_database_connection() -> DatabaseConnection:
    """Get the global database connection instance."""
    global _db_connection
    if _db_connection is None:
        config = DatabaseConfig.from_env()
        _db_connection = DatabaseConnection(config)
    return _db_connection


def close_database_connection() -> None:
    """Close the global database connection."""
    global _db_connection
    if _db_connection:
        _db_connection.close()
        _db_connection = None