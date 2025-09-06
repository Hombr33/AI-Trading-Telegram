#!/usr/bin/env python3
"""Run the AI Trading Bot application."""

import asyncio
import signal
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import app


async def main():
    """Main entry point with proper signal handling."""
    import uvicorn

    # Create server config
    config = uvicorn.Config(
        app,
        host=str(os.getenv("API_HOST")),
        port=int(os.getenv("API_PORT")),
        log_level="info",
        access_log=False,
        reload=False,
    )

    server = uvicorn.Server(config)

    # Let uvicorn handle signals naturally - no custom handlers needed

    try:
        # Run the server
        await server.serve()
    except KeyboardInterrupt:
        pass
    finally:
        # Ensure clean shutdown
        if hasattr(server, "shutdown"):
            await server.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        # Force exit to prevent hanging
        sys.exit(0)
