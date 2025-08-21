---

### Documentation & Rules
- [Project Architecture](docs/project-architecture.md)
- [Technical Debt Preventions](docs/technical-debt-preventions.md)
- [Code Quality Guidelines](docs/code-quality.md)
- See `.cursor/rules/` for machine-readable rules for each concern (architecture, technical debt, code quality, etc.)
# telegram-ai-trade

## Overview

A sophisticated, AI-powered trading bot for Forex & Crypto markets, leveraging OpenAI GPT-5 for institutional-grade analysis and precision execution.

## Knowledge Base

### Core Documentation
- [🏗 Project Architecture](docs/project-architecture.md)
  - System Components & Design
  - Data Flow & Integration
  - Performance Requirements
  - Security Architecture
  - Deployment Strategy

- [⚙️ Technical Implementation](docs/code-quality.md)
  - Coding Standards & Style Guide
  - Testing Strategy
  - Error Handling
  - Performance Optimization
  - Logging Standards

- [🔄 Development Workflow](docs/technical-debt-preventions.md)
  - Code Review Process
  - Refactoring Guidelines
  - Quality Metrics
  - Debt Management
  - Maintenance Procedures

- [🔌 API Reference](docs/api-documentation.md)
  - REST Endpoints
  - WebSocket API
  - Authentication
  - Rate Limits
  - SDK Usage

### Trading-Specific Guides
- [📈 Trading Strategy](docs/trading-strategy.md)
  - Smart Money Concepts (SMC)
  - Timeframe Analysis
  - Entry/Exit Rules
  - Risk Parameters
  - Performance Metrics

- [⚠️ Risk Management](docs/risk-management.md)
  - Position Sizing
  - Drawdown Control
  - Exposure Limits
  - Stop-Loss Strategy
  - Account Protection

- [🤖 AI Implementation](docs/ai-implementation.md)
  - GPT-5 Integration
  - Market Analysis
  - Pattern Recognition
  - Signal Generation
  - Backtesting Results

### Platform Integration
- [💱 Exchange Integration](docs/exchange-integration.md)
  - MT4/MT5 Setup
  - Binance API
  - Bybit API
  - Order Types
  - Error Handling

- [📱 Telegram Bot](docs/telegram-integration.md)
  - Command Reference
  - Signal Format
  - Alert Configuration
  - User Management
  - Security Settings

### Operations
- [🚀 Deployment Guide](docs/deployment.md)
  - System Requirements
  - Installation Steps
  - Configuration
  - Monitoring Setup
  - Backup Procedures

- [🛠 Maintenance](docs/maintenance.md)
  - Regular Tasks
  - Troubleshooting
  - Updates & Patches
  - Performance Tuning
  - Emergency Procedures

### Contributing
- [👥 Contribution Guide](docs/contributing.md)
  - Development Setup
  - Coding Standards
  - Pull Request Process
  - Testing Requirements
  - Documentation Rules

## Quick Start

1. Clone the repository
2. Install dependencies: `poetry install`
3. Configure environment variables
4. Run the bot: `poetry run python src/main.py`

## Key Features

### 1. AI-Powered Analysis
- Advanced market analysis using GPT-5
- Multi-timeframe analysis (H4, H1, M15, M5, M1)
- Pattern recognition and market structure analysis
- Sentiment analysis integration

### 2. Smart Money Concepts (SMC)
- Liquidity pool identification
- Order block detection
- Break of structure (BOS) recognition
- Quasimodo pattern detection
- Fair value gap (FVG) analysis

### 3. Risk Management
- Position sizing based on account risk
- Dynamic stop-loss management
- Drawdown control
- Multi-level take-profit strategy

### 4. Multi-Platform Support
- MetaTrader 4/5 integration
- Major crypto exchanges (Binance, Bybit)
- Real-time execution
- Smart order routing

### 5. Telegram Integration
- Real-time trade signals
- Position updates
- Performance metrics
- Command interface

## Features

### 1. AI-Powered Analysis
- Advanced market analysis using GPT-5
- Multi-timeframe analysis (H4, H1, M15, M5, M1)
- Pattern recognition and market structure analysis
- Sentiment analysis integration

### 2. Smart Money Concepts (SMC)
- Liquidity pool identification
- Order block detection
- Break of structure (BOS) recognition
- Quasimodo pattern detection
- Fair value gap (FVG) analysis

### 3. Risk Management
- Position sizing based on account risk
- Dynamic stop-loss management
- Drawdown control
- Multi-level take-profit strategy

### 4. Multi-Platform Support
- MetaTrader 4/5 integration
- Major crypto exchanges (Binance, Bybit)
- Real-time execution
- Smart order routing

### 5. Telegram Integration
- Real-time trade signals
- Position updates
- Performance metrics
- Command interface

---

### Architecture

**Main Components:**
1. **AI Analysis Engine**: Uses OpenAI with a custom prompt for market analysis and signal generation.
2. **Market Data Collector**: Fetches real-time/historical data from brokers and exchanges.
3. **Trade Executor**: Places and manages trades on MT4/MT5 and crypto exchanges.
4. **Risk & Trade Management**: Enforces SOPs for risk, drawdown, and trade lifecycle.
5. **Telegram Bridge**: Sends signals and updates to Telegram, receives commands.
6. **Scheduler & Automation**: Orchestrates analysis, trading cycles, and session filters.
7. **Logging & Monitoring**: Tracks all actions, trades, and AI decisions.

---

### Data Flow
1. Market Data → AI Analysis Engine
2. AI Output (Signal JSON) → Trade Executor
3. Trade Executor → Broker/Exchange
4. Trade Updates → Telegram Bridge
5. All actions → Logging/Monitoring

---

### Technology Stack
- **Backend:** Python
- **AI Integration:** OpenAI API (GPT-5)
- **Trading APIs:** MetaTrader (MT4/MT5 bridge), CCXT (crypto)
- **Messaging:** python-telegram-bot
- **Database:** SQLite/PostgreSQL
- **Scheduler:** APScheduler
- **Deployment:** Docker, Linux

---

### Modules & Responsibilities
- `ai_analysis.py`: Loads prompt, sends data to OpenAI, receives/validates signals
- `data_collector.py`: Fetches OHLCV, news, sentiment
- `trade_executor.py`: Parses signals, places/manages orders
- `risk_manager.py`: Monitors drawdown, losses, enforces SOP
- `telegram_bridge.py`: Sends/receives Telegram messages
- `scheduler.py`: Runs analysis/trading cycles
- `logger.py`: Logs all actions

---

### Example Workflow
1. Scheduler triggers analysis
2. Data Collector fetches market data
3. AI Analysis Engine generates signals
4. Trade Executor places trades
5. Risk Manager manages trades
6. Telegram Bridge sends updates
7. Logger records events

---

### Security & Compliance
- Secure API keys
- Trade logs for audit
- Signal deduplication and TTL

---

### Extensibility
- Add new exchanges/brokers
- Update AI prompt for new strategies
- Modular for future features

---

### Project Setup
1. Clone repo & install dependencies
2. Configure API keys and broker/exchange settings
3. Set up Telegram bot
4. Run with Docker or Python

---

### Rules & SOPs
See `.cursor/rules/` for detailed rules and responsibilities in JSON (.mdc) format.
# telegram-ai-trade
Trading bot using OpenAI and notify to Telegram
