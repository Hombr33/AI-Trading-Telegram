"""
Logging configuration for the AI Trading Bot system.
"""

import logging
import sys
from typing import Optional
import structlog
from .config import get_settings


def setup_logging() -> None:
    """Set up structured logging configuration."""
    settings = get_settings()
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.logging.format == "json" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.logging.level.upper()),
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # Create logger
    logger = structlog.get_logger()
    logger.info("Logging system initialized", level=settings.logging.level)


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_function_call(func_name: str, **kwargs):
    """Decorator to log function calls."""
    def decorator(func):
        def wrapper(*args, **func_kwargs):
            logger = get_logger()
            logger.info(
                "Function called",
                function=func_name,
                args=args,
                kwargs=func_kwargs,
                **kwargs
            )
            try:
                result = func(*args, **func_kwargs)
                logger.info(
                    "Function completed successfully",
                    function=func_name,
                    result=result
                )
                return result
            except Exception as e:
                logger.error(
                    "Function failed",
                    function=func_name,
                    error=str(e),
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def log_trade_event(event_type: str, **kwargs):
    """Log trading events."""
    logger = get_logger("trading")
    logger.info(
        "Trade event",
        event_type=event_type,
        **kwargs
    )


def log_risk_event(event_type: str, severity: str, **kwargs):
    """Log risk management events."""
    logger = get_logger("risk")
    
    if severity.upper() == "CRITICAL":
        logger.critical("Risk event", event_type=event_type, severity=severity, **kwargs)
    elif severity.upper() == "ERROR":
        logger.error("Risk event", event_type=event_type, severity=severity, **kwargs)
    elif severity.upper() == "WARNING":
        logger.warning("Risk event", event_type=event_type, severity=severity, **kwargs)
    else:
        logger.info("Risk event", event_type=event_type, severity=severity, **kwargs)


def log_system_event(event_type: str, **kwargs):
    """Log system events."""
    logger = get_logger("system")
    logger.info("System event", event_type=event_type, **kwargs)