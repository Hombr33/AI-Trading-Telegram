# AI Trading Bot Documentation

Welcome to the comprehensive documentation for the AI Trading Bot system. This document provides detailed information about the architecture, setup, and usage of the system.

## 📚 Documentation Sections

### Core System Documentation
- [Architecture Overview](architecture.md) - System design and component relationships
- [System Design](system-design.md) - Detailed system architecture and design decisions
- [Quality Standards](quality-standards.md) - Code quality and testing requirements
- [Monitoring & Observability](monitoring.md) - System monitoring and alerting

### Trading Documentation
- [Trading Strategy](trading-strategy.md) - AI analysis and trading logic
- [Risk Management](risk-management.md) - Position sizing and risk controls
- [Execution Engine](execution-engine.md) - Order execution and management

### Machine-Readable Rules
- [Rules Directory](../.cursor/rules/) - AI coding assistant rules and guidelines

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Windows 10+ (for MT4/MT5 integration)
- MetaTrader 4 or 5

### Installation
1. Clone the repository
2. Run `scripts/first_run.bat` (Windows) or follow manual setup
3. Set your `BRIDGE_TOKEN` in the `.env` file
4. Start the application with `python -m src.app`

### First Run
1. Set a strong `BRIDGE_TOKEN` in `.env`
2. Start the Python application
3. In MT4/MT5: Tools → Options → Expert Advisors → Allow WebRequest for `http://127.0.0.1`
4. Attach `BridgeEA.mq4` or `BridgeEA.mq5` to a chart
5. Set the `BRIDGE_TOKEN` input parameter to match your `.env` file

## 🔧 Configuration

### Environment Variables
- `BRIDGE_TOKEN` - Authentication token for EA communication
- `TELEGRAM_BOT_TOKEN` - Telegram bot token (optional)
- `TELEGRAM_CHAT_ID` - Telegram chat ID (optional)
- `OPENAI_API_KEY` - OpenAI API key (optional)
- `DATABASE_URL` - Database connection string

### Trading Parameters
- Risk per trade: 2.0%
- Maximum daily drawdown: 6.0%
- Maximum daily loss: $25.00
- Position sizing: Risk-based on stop loss distance

## 📊 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MT4/MT5 EA   │    │  Python API     │    │   Database      │
│                 │    │                 │    │                 │
│ • BridgeEA      │◄──►│ • FastAPI       │◄──►│ • SQLite        │
│ • Heartbeat     │    │ • Bridge Routes │    │ • Models        │
│ • Tick Data     │    │ • Risk Engine   │    │ • Migrations    │
│ • Positions     │    │ • Telegram Bot  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔒 Security

- Bridge token authentication
- Input validation and sanitization
- SQL injection protection
- Rate limiting (50 req/s)

## 📈 Monitoring

### Health Checks
- `/healthz` - Basic health status
- `/readyz` - Readiness check
- `/metrics` - Prometheus metrics

### Logging
- Structured JSON logging
- Trade event logging
- Risk event logging
- System event logging

## 🧪 Testing

### Test Coverage
- Unit tests: >80% target
- Integration tests: Critical paths 100%
- Performance tests: Load and stress testing

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test categories
pytest tests/unit/
pytest tests/integration/
```

## 🚀 Deployment

### Development
```bash
python -m src.app
```

### Production
```bash
# Set environment
export TRADING_ENV=production

# Run with uvicorn
uvicorn src.app:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📞 Support

### Issues
- [GitHub Issues](https://github.com/oyi77/telegram-ai-trade/issues)

### Documentation
- [API Documentation](http://127.0.0.1:8000/docs) (when running)
- [Architecture Decisions](architecture-decisions.md)

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ for the trading community**
