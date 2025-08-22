# AI Trading Bot - Agent Guidelines

## Test Commands
- `pytest` - Run all tests
- `pytest tests/unit/` - Run unit tests only  
- `pytest tests/integration/` - Run integration tests
- `pytest tests/unit/test_analysis/test_market_analyzer.py::test_specific_function` - Run single test
- `pytest --cov=src --cov-report=html` - Run tests with coverage
- `python run.py` - Start application with uvicorn

## Architecture
FastAPI app with Socket.IO bridge connecting to MT5 via Expert Advisor. Core components:
- `src/core/` - Configuration, logging, security
- `src/execution/` - MT5Executor, OrderManager, PositionManager, TrailingManager 
- `src/bridge/` - Socket.IO bridge with HTTP fallback
- `src/telegram/` - Telegram bot integration with notifications
- `src/analysis/` - AI market analysis using OpenAI GPT-5
- Database: SQLAlchemy with PostgreSQL/SQLite, Alembic migrations

## Code Style
- Python 3.8+ with `from __future__ import annotations`
- Type hints required: `from typing import Dict, List, Optional, Any`
- Pydantic models for validation: `BaseModel`, `Field`, `BaseSettings`
- Async/await for I/O: `async def`, `await`, `asyncio.create_task()`
- Class-based components with clear interfaces
- Configuration-driven design with environment variables
- Structured logging via loguru: `get_logger(__name__)`
- Error handling with context: `log_error_with_context()`
- Docstrings for all public methods
