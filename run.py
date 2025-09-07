#!/usr/bin/env python3
"""Run the AI Trading Bot application."""

import asyncio
import os
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import app, shutdown_event


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\n🛑 Received signal {signum}. Shutting down...")
    # Set the main application's shutdown event
    shutdown_event.set()

    # Force exit after a very short delay
    import threading

    def force_exit():
        import time

        time.sleep(2)  # Wait only 2 seconds
        print("⚠️ Force exiting...")
        os._exit(1)

    # Start force exit timer in background
    exit_thread = threading.Thread(target=force_exit, daemon=True)
    exit_thread.start()


async def main():
    """Main entry point with proper signal handling."""
    import uvicorn

    # Set up signal handlers to work with the main application
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create server config
    config = uvicorn.Config(
        app,
        host=str(os.getenv("API_HOST", "0.0.0.0")),
        port=int(os.getenv("API_PORT", "8000")),
        log_level="info",
        access_log=False,
        reload=False,
    )

    server = uvicorn.Server(config)

    try:
        # Run the server - let FastAPI's lifespan handle shutdown
        await server.serve()

    except KeyboardInterrupt:
        print("\n🛑 KeyboardInterrupt received. Shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Ensure clean shutdown with timeout
        print("🧹 Cleaning up...")
        try:
            # Give the application 10 seconds to shut down gracefully
            await asyncio.wait_for(server.shutdown(), timeout=10.0)
            print("✅ Graceful shutdown complete")
        except asyncio.TimeoutError:
            print("⚠️ Graceful shutdown timed out, forcing exit...")
        except Exception as e:
            print(f"Warning: Error during server shutdown: {e}")
            print("⚠️ Forcing exit...")

        # Force exit if graceful shutdown failed
        print("👋 Goodbye!")
        os._exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 KeyboardInterrupt in main. Exiting...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    finally:
        print("👋 Goodbye!")
        sys.exit(0)
