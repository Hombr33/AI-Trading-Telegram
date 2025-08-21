"""
Database configuration for the AI Trading Bot system.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database configuration settings."""
    
    url: str = Field(default="sqlite:///./runtime/data/trade.sqlite3")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    pool_timeout: int = Field(default=30)
    pool_recycle: int = Field(default=3600)
    
    # SQLite specific settings
    journal_mode: str = Field(default="WAL")
    synchronous: str = Field(default="NORMAL")
    foreign_keys: bool = Field(default=True)
    cache_size: int = Field(default=-64000)  # 64MB
    temp_store: str = Field(default="MEMORY")
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create configuration from environment variables."""
        return cls(
            url=os.getenv("DATABASE_URL", "sqlite:///./runtime/data/trade.sqlite3"),
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            pool_size=int(os.getenv("DATABASE_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.getenv("DATABASE_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", "3600")),
            journal_mode=os.getenv("DATABASE_JOURNAL_MODE", "WAL"),
            synchronous=os.getenv("DATABASE_SYNCHRONOUS", "NORMAL"),
            foreign_keys=os.getenv("DATABASE_FOREIGN_KEYS", "true").lower() == "true",
            cache_size=int(os.getenv("DATABASE_CACHE_SIZE", "-64000")),
            temp_store=os.getenv("DATABASE_TEMP_STORE", "MEMORY"),
        )
    
    def get_sqlite_pragmas(self) -> dict:
        """Get SQLite PRAGMA statements."""
        return {
            "journal_mode": self.journal_mode,
            "synchronous": self.synchronous,
            "foreign_keys": "ON" if self.foreign_keys else "OFF",
            "cache_size": self.cache_size,
            "temp_store": self.temp_store,
        }