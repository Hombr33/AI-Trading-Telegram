#!/usr/bin/env python3
"""
Startup script for the AI Trading Bot.
"""

import asyncio
import uvicorn
from src.core.config import config
from src.core.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    try:
        logger.info("Starting AI Trading Bot...")
        logger.info(f"Environment: {config.environment}")
        logger.info(f"Debug mode: {config.debug}")
        logger.info(f"Host: {config.host}")
        logger.info(f"Port: {config.port}")
        
        # Run the FastAPI application
        uvicorn.run(
            "src.main:app",
            host=config.host,
            port=config.port,
            reload=config.reload,
            log_level=config.logging.level.lower(),
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    main()
