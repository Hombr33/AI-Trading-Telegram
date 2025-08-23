"""
Configuration management for the AI Trading Bot.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
from .logging import get_logger

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    url: str = Field(default="postgresql://user:password@localhost/trading_bot")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)

    class Config:
        env_prefix = "DB_"
        extra = "ignore"


class MT5Config(BaseSettings):
    """MT5 configuration."""

    login: Optional[int] = Field(default=None, env="MT5_LOGIN")  # Default to None for demo/testing
    password: Optional[str] = Field(default="")
    server: Optional[str] = Field(default="")
    broker_name: Optional[str] = Field(default="", env="MT5_BROKER_NAME")
    timeout: int = Field(default=30000)
    retry_attempts: int = Field(default=3)
    retry_delay_ms: int = Field(default=1000)
    
    @field_validator('login', mode='before')
    @classmethod
    def validate_login(cls, v):
        if v == '' or v is None:
            return None
        return int(v) if v else None

    @property
    def is_configured(self) -> bool:
        """Check if MT5 is properly configured."""
        return bool(self.login and self.password and self.server and self.broker_name)

    class Config:
        env_prefix = "MT5_"
        extra = "ignore"


class BridgeConfig(BaseSettings):
    """Bridge configuration."""

    bridge_token: str = Field(default="your_bridge_token_here")
    bridge_url: str = Field(default="http://127.0.0.1:8000")
    socketio_enabled: bool = Field(default=True)
    socket_io_port: int = Field(default=8001)
    fallback_enabled: bool = Field(default=True)

    class Config:
        env_prefix = "BRIDGE_"
        extra = "ignore"


class TelegramConfig(BaseSettings):
    """Telegram configuration."""

    bot_token: str = Field(default="7773625662:AAHx-Nk8OkoBbU7a4mMP6CQ6fQxplgBpz3E")
    chat_id: Optional[int] = Field(default=6077091585)
    webhook_url: Optional[str] = Field(default=None)
    webhook_enabled: bool = Field(default=False)
    
    @field_validator('chat_id', mode='before')
    @classmethod
    def validate_chat_id(cls, v):
        if v == '' or v is None:
            return None
        return int(v) if v else None

    class Config:
        env_prefix = "TELEGRAM_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


class OpenAIConfig(BaseSettings):
    """OpenAI configuration."""

    api_key: str = Field(default="your_openai_api_key_here")
    model: str = Field(default="gpt-4")
    max_tokens: int = Field(default=2000)
    temperature: float = Field(default=0.1)

    class Config:
        env_prefix = "OPENAI_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


class RiskConfig(BaseSettings):
    """Risk management configuration."""

    risk_per_trade_pct: float = Field(default=2.0, env="RISK_PER_TRADE_PCT")
    max_daily_drawdown_pct: float = Field(default=6.0, env="MAX_DAILY_DRAWDOWN_PCT")
    max_daily_loss_usd: float = Field(default=25.0, env="MAX_DAILY_LOSS_USD")
    max_open_positions: int = Field(default=10)
    max_correlation_exposure: float = Field(default=0.7)
    consecutive_loss_limit: int = Field(default=4)

    class Config:
        env_prefix = "RISK_"
        extra = "ignore"


class CryptoConfig(BaseSettings):
    """Crypto exchange configuration."""
    
    # Binance
    binance_api_key: str = Field(default="")
    binance_secret_key: str = Field(default="")
    binance_testnet: bool = Field(default=True)
    
    # Bybit
    bybit_api_key: str = Field(default="")
    bybit_secret_key: str = Field(default="")
    bybit_testnet: bool = Field(default=True)
    
    # Bitget
    bitget_api_key: str = Field(default="")
    bitget_secret_key: str = Field(default="")
    bitget_passphrase: str = Field(default="")
    bitget_testnet: bool = Field(default=True)
    
    # Common settings
    default_leverage: int = Field(default=1)
    max_leverage: int = Field(default=10)
    
    @property
    def binance_configured(self) -> bool:
        return bool(self.binance_api_key and self.binance_secret_key)
    
    @property
    def bybit_configured(self) -> bool:
        return bool(self.bybit_api_key and self.bybit_secret_key)
    
    @property
    def bitget_configured(self) -> bool:
        return bool(self.bitget_api_key and self.bitget_secret_key and self.bitget_passphrase)

    class Config:
        env_prefix = "CRYPTO_"
        extra = "ignore"


class TradingConfig(BaseSettings):
    """Trading configuration."""

    # Risk management
    risk_management: Dict[str, Any] = Field(
        default={
            "max_risk_per_trade_pct": 2.0,
            "max_daily_drawdown_pct": 6.0,
            "max_daily_trades": 50,
            "max_open_positions": 10,
            "consecutive_loss_limit": 4,
        }
    )

    # Position sizing
    position_sizing: Dict[str, Any] = Field(
        default={
            "min_position_size": 0.01,
            "max_position_size": 10.0,
            "position_size_rounding": "down",
        }
    )

    # Trailing stop
    trailing_stop: Dict[str, Any] = Field(
        default={
            "enabled": True,
            "start_points": 250,
            "stop_points": 200,
            "step_points": 50,
        }
    )

    # Take profit
    take_profit: Dict[str, Any] = Field(
        default={"tp1_ratio": 1.5, "tp2_ratio": 3.0, "partial_close_pct": 0.5}
    )

    # Execution settings
    execution: Dict[str, Any] = Field(
        default={
            "slippage_points": 10,
            "magic_number": 1001,
            "order_filling": "FOK",
            "order_time": "GTC",
            "deviation": 10,
        }
    )

    class Config:
        env_prefix = "TRADING_"
        extra = "ignore"


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")
    file_path: Optional[str] = Field(default=None, env="LOG_FILE")
    max_size_mb: int = Field(default=100)
    backup_count: int = Field(default=5)

    class Config:
        env_prefix = "LOG_"
        extra = "ignore"


class AutoTradingConfig(BaseSettings):
    """Auto trading configuration."""
    
    enabled: bool = Field(default=False, env="AUTO_TRADING_ENABLED")
    auto_signal_generation: bool = Field(default=False, env="AUTO_SIGNAL_GENERATION")
    signal_interval_minutes: int = Field(default=15, env="SIGNAL_INTERVAL_MINUTES")
    max_trades_per_day: int = Field(default=10, env="MAX_TRADES_PER_DAY")
    
    # Trading pairs for auto signals (no env vars to avoid JSON parsing issues)
    forex_pairs: List[str] = Field(default=["EURUSD", "GBPUSD", "USDJPY"])
    crypto_pairs: List[str] = Field(default=["BTCUSDT", "ETHUSDT", "ADAUSDT"])
    
    # Risk per trade for auto trading
    risk_per_trade_percent: float = Field(default=1.0, env="AUTO_RISK_PER_TRADE")
    
    class Config:
        env_prefix = "AUTO_"
        env_ignore = {"forex_pairs", "crypto_pairs"}
        extra = "ignore"


class AppConfig(BaseSettings):
    """Main application configuration."""

    # Application
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    timezone: str = Field(default="UTC", env="TIMEZONE")

    # Server
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    reload: bool = Field(default=False)

    # Components
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    mt5: MT5Config = Field(default_factory=MT5Config)
    bridge: BridgeConfig = Field(default_factory=BridgeConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    crypto: CryptoConfig = Field(default_factory=CryptoConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    # Auto trading config initialized manually to avoid env parsing issues
    auto_trading: Optional[AutoTradingConfig] = Field(default=None)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_nested_delimiter = "__"
        extra = "ignore"  # Ignore extra fields from environment
        env_prefix = ""  # No prefix for main config

    def __init__(self, **kwargs):
        """Initialize configuration.
        
        This method handles the initialization of all configuration components
        and ensures proper validation of all settings.
        """
        # Override with environment variables if they exist
        if "host" not in kwargs and os.getenv("API_HOST"):
            kwargs["host"] = os.getenv("API_HOST")
        if "port" not in kwargs and os.getenv("API_PORT"):
            kwargs["port"] = int(os.getenv("API_PORT"))
            
        super().__init__(**kwargs)
        self.debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        
        # Initialize auto_trading manually with safe defaults
        if self.auto_trading is None:
            # Create simple object with attributes to avoid Pydantic validation issues
            class SimpleAutoConfig:
                def __init__(self):
                    self.enabled = os.getenv("AUTO_TRADING_ENABLED", "false").lower() == "true"
                    self.auto_signal_generation = os.getenv("AUTO_SIGNAL_GENERATION", "false").lower() == "true"
                    self.signal_interval_minutes = int(os.getenv("SIGNAL_INTERVAL_MINUTES", "15"))
                    self.max_trades_per_day = int(os.getenv("MAX_TRADES_PER_DAY", "10"))
                    self.forex_pairs = ["EURUSD", "GBPUSD", "USDJPY"]
                    self.crypto_pairs = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
                    self.risk_per_trade_percent = float(os.getenv("AUTO_RISK_PER_TRADE", "1.0"))
            
            self.auto_trading = SimpleAutoConfig()

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
                "timeout": self.mt5.timeout,
            },
            "bridge": self.bridge.dict(),
            "telegram": {
                "bot_token": (
                    self.telegram.bot_token[:10] + "..."
                    if self.telegram.bot_token
                    else None
                ),
                "chat_id": self.telegram.chat_id,
                "webhook_enabled": self.telegram.webhook_enabled,
            },
            "openai": {
                "model": self.openai.model,
                "max_tokens": self.openai.max_tokens,
                "temperature": self.openai.temperature,
            },
            "risk": self.risk.dict(),
            "trading": self.trading.dict(),
            "logging": self.logging.dict(),
            "auto_trading": self.auto_trading.dict(),
        }


# Global configuration instance - reload env vars to ensure they're picked up
load_dotenv(env_path, override=True)
config = AppConfig()
