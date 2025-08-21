---

### Documentation & Rules
- [Project Architecture](docs/project-architecture.md)
- [Technical Debt Preventions](docs/technical-debt-preventions.md)
- [Code Quality Guidelines](docs/code-quality.md)
- See `.cursor/rules/` for machine-readable rules for each concern (architecture, technical debt, code quality, etc.)
## Automated Forex & Crypto Trading Bot

### Overview
This project is an institutional-grade automated trading bot for Forex & Crypto, powered by OpenAI (GPT-5) for market analysis and precision execution. It is designed for retail platforms (MT4/MT5, major crypto exchanges) and follows strict risk and trade management SOPs.

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
