# AI Trading Bot Project Structure

## Overview
This is a comprehensive AI-powered automated trading bot that integrates with MT5 for institutional-grade trading with SMC/liquidity focus, Quasimodo patterns, and precision execution.

## Project Architecture

```
telegram-ai-trade/
├── .devcontainer/                 # Development container configuration
│   └── devcontainer.json         # Enhanced devcontainer with Python, Node.js, tools
├── .cursor/                       # Cursor IDE rules and configuration
│   └── rules/                    # Comprehensive development rules
│       ├── trading_system_core.mdc           # Core trading system rules
│       ├── ai_analysis_enhanced.mdc          # AI analysis engine rules
│       ├── mt5_execution_enhanced.mdc        # MT5 execution engine rules
│       ├── data_collection_enhanced.mdc      # Data collection system rules
│       ├── telegram_bridge_enhanced.mdc      # Telegram bridge system rules
│       ├── risk_management_enhanced.mdc      # Risk management system rules
│       ├── project_architecture.mdc          # Project architecture rules
│       ├── code_quality.mdc                  # Code quality standards
│       ├── technical_debt_preventions.mdc    # Technical debt prevention
│       ├── security.mdc                      # Security guidelines
│       ├── logger.mdc                        # Logging standards
│       └── scheduler.mdc                     # Scheduling rules
├── src/                           # Source code
│   ├── __init__.py
│   ├── main.py                    # Main application entry point
│   ├── config/                     # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py            # Application settings
│   │   ├── database.py            # Database configuration (SQLite)
│   │   └── logging.py             # Logging configuration
│   ├── core/                       # Core system components
│   │   ├── __init__.py
│   │   ├── interfaces/             # Abstract interfaces
│   │   │   ├── __init__.py
│   │   │   ├── data_collector.py   # IDataCollector interface
│   │   │   ├── analyzer.py         # IAnalyzer interface
│   │   │   ├── executor.py         # ITradeExecutor interface
│   │   │   ├── risk_manager.py     # IRiskManager interface
│   │   │   └── message_broker.py   # IMessageBroker interface
│   │   ├── exceptions.py           # Custom exceptions
│   │   ├── constants.py            # System constants
│   │   └── utils.py                # Utility functions
│   ├── data/                        # Data collection and processing
│   │   ├── __init__.py
│   │   ├── collectors/             # Data collectors
│   │   │   ├── __init__.py
│   │   │   ├── mt5_collector.py    # MT5 data collector
│   │   │   ├── binance_collector.py # Binance data collector
│   │   │   ├── bybit_collector.py  # Bybit data collector
│   │   │   ├── news_collector.py   # News API collector
│   │   │   └── sentiment_collector.py # Sentiment data collector
│   │   ├── processors/             # Data processors
│   │   │   ├── __init__.py
│   │   │   ├── market_data_processor.py # Market data processing
│   │   │   ├── news_processor.py   # News processing
│   │   │   └── sentiment_processor.py # Sentiment processing
│   │   ├── storage/                # Data storage
│   │   │   ├── __init__.py
│   │   │   ├── database.py         # SQLite database operations
│   │   │   ├── cache.py            # Redis cache operations
│   │   │   └── file_storage.py     # File-based storage
│   │   └── models/                 # Data models
│   │       ├── __init__.py
│   │       ├── market_data.py      # Market data models
│   │       ├── news_data.py        # News data models
│   │       └── sentiment_data.py   # Sentiment data models
│   ├── analysis/                    # AI analysis engine
│   │   ├── __init__.py
│   │   ├── ai_engine/              # AI analysis components
│   │   │   ├── __init__.py
│   │   │   ├── market_analyzer.py  # Market analysis engine
│   │   │   ├── pattern_recognizer.py # Pattern recognition
│   │   │   ├── sentiment_analyzer.py # Sentiment analysis
│   │   │   └── signal_generator.py # Signal generation
│   │   ├── strategies/             # Trading strategies
│   │   │   ├── __init__.py
│   │   │   ├── smc_strategy.py     # SMC/liquidity strategy
│   │   │   ├── quasimodo_strategy.py # Quasimodo strategy
│   │   │   └── scalping_strategy.py # Scalping strategy
│   │   ├── indicators/             # Technical indicators
│   │   │   ├── __init__.py
│   │   │   ├── trend_indicators.py # Trend indicators
│   │   │   ├── momentum_indicators.py # Momentum indicators
│   │   │   └── volatility_indicators.py # Volatility indicators
│   │   └── models/                 # Analysis models
│   │       ├── __init__.py
│   │       ├── analysis_result.py  # Analysis result model
│   │       ├── trading_signal.py   # Trading signal model
│   │       └── market_structure.py # Market structure model
│   ├── execution/                   # Trade execution engine
│   │   ├── __init__.py
│   │   ├── mt5/                    # MT5 integration
│   │   │   ├── __init__.py
│   │   │   ├── connection.py       # MT5 connection management
│   │   │   ├── order_manager.py    # Order management
│   │   │   ├── position_manager.py # Position management
│   │   │   └── account_manager.py  # Account management
│   ├── risk/                        # Risk management system
│   │   ├── __init__.py
│   │   ├── position_sizer.py       # Position sizing calculator
│   │   ├── drawdown_manager.py     # Drawdown management
│   │   ├── correlation_manager.py  # Correlation risk management
│   │   ├── volatility_manager.py   # Volatility risk management
│   │   └── emergency_controller.py # Emergency risk controls
│   ├── telegram/                    # Telegram bridge system
│   │   ├── __init__.py
│   │   ├── bot.py                  # Telegram bot implementation
│   │   ├── handlers/               # Message handlers
│   │   │   ├── __init__.py
│   │   │   ├── command_handler.py  # Command handling
│   │   │   ├── signal_handler.py   # Signal message handling
│   │   │   └── notification_handler.py # Notification handling
│   │   ├── formatters/             # Message formatters
│   │   │   ├── __init__.py
│   │   │   ├── signal_formatter.py # Signal message formatting
│   │   │   └── report_formatter.py # Report formatting
│   │   └── models/                 # Telegram models
│   │       ├── __init__.py
│   │       ├── user.py             # User model
│   │       ├── message.py          # Message model
│   │       └── notification.py     # Notification model
│   ├── monitoring/                  # System monitoring
│   │   ├── __init__.py
│   │   ├── metrics.py              # Performance metrics
│   │   ├── health_checker.py       # System health monitoring
│   │   ├── alert_manager.py        # Alert management
│   │   └── dashboard.py            # Monitoring dashboard
│   └── api/                         # REST API
│       ├── __init__.py
│       ├── main.py                 # FastAPI application
│       ├── routes/                 # API routes
│       │   ├── __init__.py
│       │   ├── signals.py          # Signal endpoints
│       │   ├── trades.py           # Trade endpoints
│       │   ├── performance.py      # Performance endpoints
│       │   └── system.py           # System endpoints
│       └── models/                 # API models
│           ├── __init__.py
│           ├── requests.py          # Request models
│           └── responses.py         # Response models
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── unit/                       # Unit tests
│   │   ├── __init__.py
│   │   ├── test_analysis/          # Analysis tests
│   │   ├── test_execution/         # Execution tests
│   │   ├── test_risk/              # Risk management tests
│   │   └── test_telegram/          # Telegram tests
│   ├── integration/                 # Integration tests
│   │   ├── __init__.py
│   │   ├── test_data_flow/         # Data flow tests
│   │   ├── test_trading_flow/      # Trading flow tests
│   │   └── test_api/               # API tests
│   └── e2e/                        # End-to-end tests
│       ├── __init__.py
│       └── test_full_trading_cycle.py # Full trading cycle tests
├── config/                          # Configuration files
│   ├── dev/                        # Development configuration
│   │   ├── config.yaml             # Development settings
│   │   └── database.yaml           # Development database config (SQLite)
│   ├── prod/                       # Production configuration
│   │   ├── config.yaml             # Production settings
│   │   └── database.yaml           # Production database config (SQLite)
│   └── test/                       # Test configuration
│       ├── config.yaml             # Test settings
│       └── database.yaml           # Test database config (SQLite)
├── database/                        # SQLite database files
│   ├── trading_bot.db              # Main database file
│   ├── trading_bot_test.db         # Test database file
│   └── migrations/                 # Database migrations
├── scripts/                         # Utility scripts
│   ├── setup.py                    # Setup script
│   ├── deploy.py                    # Deployment script
│   ├── backup.py                    # Backup script
│   └── maintenance.py               # Maintenance script
├── docs/                            # Documentation
│   ├── api/                         # API documentation
│   ├── architecture/                # Architecture documentation
│   ├── deployment/                  # Deployment guides
│   └── user_guides/                 # User guides
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore file
├── README.md                        # Project README
├── requirements.txt                 # Python dependencies
├── requirements-dev.txt             # Development dependencies
├── pyproject.toml                   # Project configuration
├── docker-compose.yml               # Docker composition
├── Dockerfile                       # Docker image
└── app-code-prompt.json             # AI analysis prompt configuration
```

## Key Features

### 1. AI Analysis Engine
- Multi-timeframe analysis (H4, H1, M15, M5, M1)
- SMC/liquidity pattern recognition
- Quasimodo pattern detection
- Institutional-grade analysis with reality checks
- Confidence scoring system

### 2. MT5 Integration
- Real-time connection management
- Advanced order management
- Position tracking and modification
- Risk controls and circuit breakers
- Performance monitoring

### 3. Risk Management
- Position sizing based on risk percentage
- Drawdown controls and limits
- Consecutive loss management
- Correlation risk management
- Volatility-based adjustments

### 4. Data Collection
- Multi-source data collection (MT5, Binance, Bybit)
- News sentiment analysis
- Real-time market data streaming
- Data quality validation and enrichment

### 5. Telegram Bridge
- Real-time signal distribution
- User interaction and commands
- Performance reporting
- Bot management and control

### 6. System Architecture
- Modular and extensible design
- Event-driven architecture
- Dependency injection
- Comprehensive error handling
- Performance monitoring

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy
- **Database**: SQLite (portable), Redis
- **Trading Platform**: MetaTrader 5
- **AI/ML**: scikit-learn, pandas, numpy
- **Communication**: Telegram Bot API
- **Monitoring**: Prometheus, structured logging
- **Testing**: pytest, pytest-asyncio
- **Development**: Black, flake8, mypy

## Performance Targets

- **Signal Generation**: < 500ms
- **Execution Latency**: < 100ms
- **System Uptime**: > 99.5%
- **Memory Usage**: < 2GB
- **CPU Usage**: < 70%

## Risk Parameters

- **Risk per Trade**: 2% of equity
- **Daily Drawdown Limit**: 6% of equity
- **Consecutive Loss Rules**: Progressive reduction
- **Position Limits**: Maximum 10 concurrent positions
- **Correlation Limit**: Maximum 70% correlation

## Development Guidelines

- Follow SOLID principles and DRY methodology
- Comprehensive testing (unit, integration, e2e)
- Code quality standards (Black, flake8, mypy)
- Security best practices
- Performance optimization
- Comprehensive documentation

## Database Strategy

### SQLite Benefits
- **Portability**: Single file database, easy to distribute
- **Zero Configuration**: No server setup required
- **Lightweight**: Minimal resource usage
- **Embedded**: Perfect for VPS/RDP deployment
- **Backup**: Simple file copy for backup/restore

### Database Structure
- **Trading Data**: OHLCV, signals, trades, positions
- **User Data**: Telegram users, preferences, permissions
- **System Data**: Logs, metrics, configuration
- **Performance Data**: P&L, drawdown, risk metrics
