"""
Configuration management for the AI Trading Bot.
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    
    url: str = Field(default="postgresql://user:password@localhost/trading_bot")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)
    
    class Config:
        env_prefix = "DB_"


class MT5Config(BaseSettings):
    """MT5 configuration."""
    
    login: Optional[int] = Field(default=None)
    password: Optional[str] = Field(default=None)
    server: Optional[str] = Field(default=None)
    timeout: int = Field(default=30000)
    retry_attempts: int = Field(default=3)
    retry_delay_ms: int = Field(default=1000)
    
    class Config:
        env_prefix = "MT5_"


class BridgeConfig(BaseSettings):
    """Bridge configuration."""
    
    bridge_token: str = Field(default="your_bridge_token_here")
    bridge_url: str = Field(default="http://127.0.0.1:8000")
    socketio_enabled: bool = Field(default=True)
    fallback_enabled: bool = Field(default=True)
    
    class Config:
        env_prefix = "BRIDGE_"


class TelegramConfig(BaseSettings):
    """Telegram configuration."""
    
    bot_token: str = Field(default="7773625562:AAHx-Nk8OkoBbU7a4mMP6CQ6fQxplBpz3E")
    chat_id: Optional[int] = Field(default=6077091585)
    webhook_url: Optional[str] = Field(default=None)
    webhook_enabled: bool = Field(default=False)
    
    class Config:
        env_prefix = "TELEGRAM_"


class OpenAIConfig(BaseSettings):
    """OpenAI configuration."""
    
    api_key: str = Field(default="your_openai_api_key_here")
    model: str = Field(default="gpt-4")
    max_tokens: int = Field(default=2000)
    temperature: float = Field(default=0.1)
    
    class Config:
        env_prefix = "OPENAI_"


class RiskConfig(BaseSettings):
    """Risk management configuration."""
    
    max_risk_per_trade_pct: float = Field(default=2.0)
    max_daily_drawdown_pct: float = Field(default=6.0)
    max_open_positions: int = Field(default=10)
    max_correlation_exposure: float = Field(default=0.7)
    consecutive_loss_limit: int = Field(default=4)
    
    class Config:
        env_prefix = "RISK_"


class TradingConfig(BaseSettings):
    """Trading configuration."""
    
    # Risk management
    risk_management: Dict[str, Any] = Field(default={
        "max_risk_per_trade_pct": 2.0,
        "max_daily_drawdown_pct": 6.0,
        "max_daily_trades": 50,
        "max_open_positions": 10,
        "consecutive_loss_limit": 4
    })
    
    # Position sizing
    position_sizing: Dict[str, Any] = Field(default={
        "min_position_size": 0.01,
        "max_position_size": 10.0,
        "position_size_rounding": "down"
    })
    
    # Trailing stop
    trailing_stop: Dict[str, Any] = Field(default={
        "enabled": True,
        "start_points": 250,
        "stop_points": 200,
        "step_points": 50
    })
    
    # Take profit
    take_profit: Dict[str, Any] = Field(default={
        "tp1_ratio": 1.5,
        "tp2_ratio": 3.0,
        "partial_close_pct": 0.5
    })
    
    # Execution settings
    execution: Dict[str, Any] = Field(default={
        "slippage_points": 10,
        "magic_number": 1001,
        "order_filling": "FOK",
        "order_time": "GTC",
        "deviation": 10
    })
    
    class Config:
        env_prefix = "TRADING_"


class LoggingConfig(BaseSettings):
    """Logging configuration."""
    
    level: str = Field(default="INFO")
    format: str = Field(default="json")
    file_path: Optional[str] = Field(default=None)
    max_size_mb: int = Field(default=100)
    backup_count: int = Field(default=5)
    
    class Config:
        env_prefix = "LOG_"


class AppConfig(BaseSettings):
    """Main application configuration."""
    
    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=False)
    
    # Components
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    mt5: MT5Config = Field(default_factory=MT5Config)
    bridge: BridgeConfig = Field(default_factory=BridgeConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Load from environment variables
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Database
        if os.getenv("DATABASE_URL"):
            self.database.url = os.getenv("DATABASE_URL")
        
        # MT5
        if os.getenv("MT5_LOGIN"):
            self.mt5.login = int(os.getenv("MT5_LOGIN"))
        if os.getenv("MT5_PASSWORD"):
            self.mt5.password = os.getenv("MT5_PASSWORD")
        if os.getenv("MT5_SERVER"):
            self.mt5.server = os.getenv("MT5_SERVER")
        
        # Telegram
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            self.telegram.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if os.getenv("TELEGRAM_CHAT_ID"):
            self.telegram.chat_id = int(os.getenv("TELEGRAM_CHAT_ID"))
        
        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            self.openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # Environment
        if os.getenv("ENVIRONMENT"):
            self.environment = os.getenv("ENVIRONMENT")
        
        # Debug mode
        if os.getenv("DEBUG"):
            self.debug = os.getenv("DEBUG").lower() in ("true", "1", "yes")
    
    def get_database_url(self) -> str:
        """Get database URL with fallback."""
        if self.database.url != "postgresql://user:password@localhost/trading_bot":
            return self.database.url
        
        # Try to construct from individual components
        user = os.getenv("DB_USER", "user")
        password = os.getenv("DB_PASSWORD", "password")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "trading_bot")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "database": self.database.dict(),
            "mt5": {
                "login": self.mt5.login,
                "server": self.mt5.server,
                "timeout": self.mt5.timeout
            },
            "bridge": self.bridge.dict(),
            "telegram": {
                "bot_token": self.telegram.bot_token[:10] + "..." if self.telegram.bot_token else None,
                "chat_id": self.telegram.chat_id,
                "webhook_enabled": self.telegram.webhook_enabled
            },
            "openai": {
                "model": self.openai.model,
                "max_tokens": self.openai.max_tokens,
                "temperature": self.openai.temperature
            },
            "risk": self.risk.dict(),
            "trading": self.trading.dict(),
            "logging": self.logging.dict()
        }


# Global configuration instance
config = AppConfig()