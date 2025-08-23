# AI Trading Bot - Agent Guidelines

## Test Commands
- `pytest` - Run all tests
- `pytest tests/unit/` - Run unit tests only  
- `pytest tests/integration/` - Run integration tests
- `pytest tests/unit/test_analysis/test_market_analyzer.py::test_specific_function` - Run single test
- `pytest --cov=src --cov-report=html` - Run tests with coverage
- `python run.py` - Start application with uvicorn
- `python tests/test_setup.py` - Test core setup and imports

## Architecture
Institutional-grade AI trading bot with 2-way MT5 communication:
- `src/core/` - Configuration, logging, security framework
- `src/execution/` - MT5Executor (base), AioMQLExecutor (async), OrderManager, PositionManager, TrailingManager 
- `src/bridge/` - Socket.IO bridge + HTTP fallback for EA communication
- `src/telegram_bot/` - Telegram bot with handlers, notifications, commands
- `src/analysis/` - AI market analysis using OpenAI GPT-5
- `src/api/routes/` - FastAPI endpoints (health, bridge, trading, v1)
- `ea/` - MT5 Expert Advisors (BridgeEA.mq5/mq4)
- Database: SQLAlchemy with PostgreSQL/SQLite, Alembic migrations

## Code Style & Standards
- Python 3.8+ with `from __future__ import annotations`
- **Type hints mandatory**: `from typing import Dict, List, Optional, Any`
- **Pydantic validation**: `BaseModel`, `Field`, `BaseSettings` for all data models
- **Async/await patterns**: `async def`, `await`, `asyncio.create_task()`, `asyncio.wait_for()`
- **Class-based architecture** with dependency injection and clear interfaces
- **Configuration-driven** design with environment variables and config classes
- **Structured logging**: `get_logger(__name__)`, `log_error_with_context()`, `log_system_event()`
- **Error handling**: Always use `try/except` with specific exception types, timeout handling
- **Docstrings required** for all public methods and complex logic
- **Resource cleanup**: Use async context managers (`async with`) and proper disconnection

## Critical Patterns
- **Graceful Fallbacks**: AioMQLExecutor → MT5Executor → Mock for development
- **Timeout Control**: `asyncio.wait_for()` for all external operations (30s default)
- **Bridge Communication**: Socket.IO primary, HTTP fallback, EA connects to Python
- **Risk-First Design**: 2% max risk per trade, 6% daily drawdown limits
- **Notification Flow**: All events → Telegram notifications with emojis and formatting

## Error Handling Rules
- **Specific exceptions**: Catch `asyncio.TimeoutError`, `ConnectionError`, `ValueError` separately
- **Context logging**: Always log with relevant context (symbol, order_id, etc.)
- **Graceful degradation**: System continues with reduced functionality on component failures
- **Resource cleanup**: Use `finally` blocks and async context managers
- **User notifications**: Critical errors sent to Telegram, operational errors logged only
