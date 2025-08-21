# AI Agent Instructions for telegram-ai-trade

This document provides essential guidance for AI agents working on the telegram-ai-trade project, a sophisticated trading bot leveraging AI for market analysis and execution.

## Project Architecture

### Core Components
- **AI Analysis Engine**: Handles market analysis using GPT-5
- **Market Data Collector**: Gathers market data from exchanges
- **Trade Executor**: Manages trade execution and order lifecycle
- **Risk Manager**: Implements position sizing and risk controls
- **Telegram Bridge**: User interface and command handling
- **Scheduler**: Orchestrates automated tasks
- **Logger**: Structured logging for monitoring and debugging

### Key Design Patterns
- Use class-based components with clear interfaces
- Configuration-driven integrations
- Strong type hints and validation
- Event-driven architecture for real-time processing

## Trading Strategy Implementation

### Smart Money Concepts (SMC)
Key classes in strategy implementation:
```python
class OrderBlock:
    type: Literal["bullish", "bearish"]
    high: float
    low: float
    volume: float
    confidence: float

class TradingSignal:
    direction: Literal["long", "short"]
    entry_zone: Range
    stop_loss: float
    targets: List[float]
    timeframe: str
    confidence: float
```

### Risk Management
- Position sizing based on account risk percentage
- Multi-tier take profit levels (TP1: 1.5R, TP2: 3.0R)
- Trailing stop activation on reaching specified targets
- Maximum drawdown and exposure limits enforced

## Development Guidelines

### Code Structure
- Modular design with clear separation of concerns
- New modules must not break existing functionality
- Configuration files for integration parameters
- Extensive type hints and validation

### Testing Requirements
- Unit tests for strategy components
- Integration tests for exchange connectivity
- Backtesting validation for new features
- Risk management rule validation

### Error Handling
- Graceful degradation on API failures
- Retry mechanisms for transient errors
- Clear error logging with context
- User notifications for critical issues

## Common Tasks

### Adding New Features
1. Update configuration in appropriate `.json` files
2. Implement changes following modular design
3. Add tests and documentation
4. Update Telegram command handlers if needed

### Debugging
- Check logs for structured error messages
- Verify exchange API connectivity
- Validate risk parameters in configuration
- Test Telegram command responses

## Documentation
- Project architecture: `docs/project-architecture.md`
- Trading strategy: `docs/trading-strategy.md`
- API documentation: `docs/api-documentation.md`
- Risk management: `docs/risk-management.md`

## Questions?
Contact the maintainers or reference the detailed documentation in the `docs/` directory.
