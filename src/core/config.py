"""
Configuration management for the AI Trading Bot system.
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    """Application configuration."""
    name: str = Field(default="telegram-ai-trade")
    version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    timezone: str = Field(default="Asia/Jakarta")
    debug: bool = Field(default=False)


class APIConfig(BaseModel):
    """API configuration."""
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    workers: int = Field(default=1)
    timeout: int = Field(default=30)
    cors_origins: list[str] = Field(default=["*"])


class BridgeConfig(BaseModel):
    """Bridge configuration."""
    token_env_key: str = Field(default="BRIDGE_TOKEN")
    rate_limit: dict = Field(default={"requests_per_second": 50, "burst_size": 10})
    retry: dict = Field(default={"max_attempts": 3, "backoff_ms": 250})
    heartbeat_interval: int = Field(default=5)


class TradingConfig(BaseModel):
    """Trading configuration."""
    risk_management: dict = Field(default={
        "risk_per_trade_pct": 2.0,
        "max_daily_drawdown_pct": 6.0,
        "max_daily_loss_usd": 25.0,
        "max_open_positions": 10,
        "max_daily_trades": 50
    })
    position_sizing: dict = Field(default={
        "method": "risk_based_on_sl_distance",
        "min_position_size": 0.01,
        "max_position_size": 10.0
    })
    execution: dict = Field(default={
        "magic_number": 1001,
        "slippage_points": 10,
        "prefer_limit_orders": True
    })
    session_filters: dict = Field(default={
        "avoid_high_impact_news": True,
        "prefer_london_ny_overlap": True,
        "timezone": "Asia/Jakarta"
    })


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(default="sqlite:///./runtime/data/trade.sqlite3")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    pool_timeout: int = Field(default=30)
    pool_recycle: int = Field(default=3600)
    sqlite_pragmas: dict = Field(default={
        "journal_mode": "WAL",
        "synchronous": "NORMAL",
        "foreign_keys": True,
        "cache_size": -64000,
        "temp_store": "MEMORY"
    })


class TelegramConfig(BaseModel):
    """Telegram configuration."""
    bot_token_env: str = Field(default="TELEGRAM_BOT_TOKEN")
    chat_id_env: str = Field(default="TELEGRAM_CHAT_ID")
    update_interval: int = Field(default=1)
    timeout: int = Field(default=30)
    notifications: dict = Field(default={
        "signals": True,
        "trade_updates": True,
        "performance_reports": True,
        "risk_alerts": True
    })


class OpenAIConfig(BaseModel):
    """OpenAI configuration."""
    api_key_env: str = Field(default="OPENAI_API_KEY")
    model: str = Field(default="gpt-4")
    max_tokens: int = Field(default=1000)
    temperature: float = Field(default=0.1)
    timeout: int = Field(default=30)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO")
    format: str = Field(default="json")
    output: str = Field(default="stdout")
    file_path: Optional[str] = Field(default=None)
    structured: dict = Field(default={
        "enabled": True,
        "include_timestamp": True,
        "include_level": True,
        "include_module": True
    })


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    health_check_interval: int = Field(default=30)
    metrics_enabled: bool = Field(default=True)
    prometheus_endpoint: str = Field(default="/metrics")
    alerts: dict = Field(default={
        "daily_drawdown_threshold": True,
        "ea_disconnect_heartbeat_missed": True,
        "bridge_http_error_burst": True
    })


class SecurityConfig(BaseModel):
    """Security configuration."""
    auth_enabled: bool = Field(default=True)
    rate_limiting: bool = Field(default=True)
    input_validation: bool = Field(default=True)
    sql_injection_protection: bool = Field(default=True)


class Settings(BaseSettings):
    """Main settings class."""
    app: AppConfig = Field(default_factory=AppConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    bridge: BridgeConfig = Field(default_factory=BridgeConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()