# AI Trading Bot - Automated Trading with Institutional Intelligence

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![MT5](https://img.shields.io/badge/MT5-Integration-orange.svg)](https://www.metatrader5.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Overview

An advanced AI-powered automated trading bot that combines institutional-grade market analysis with precision execution through MetaTrader 5. Built with a focus on SMC/liquidity patterns, Quasimodo formations, and scalping strategies for retail traders.

## ✨ Key Features

- **🤖 AI-Powered Analysis**: Multi-timeframe analysis with institutional-grade intelligence
- **📊 SMC/Liquidity Focus**: Advanced pattern recognition for institutional-level trading
- **🎯 Quasimodo Patterns**: Break of structure and change of character detection
- **⚡ Real-Time Execution**: MT5 integration with sub-100ms execution latency
- **🛡️ Advanced Risk Management**: Position sizing, drawdown controls, correlation management
- **📱 Telegram Integration**: Real-time signal distribution and bot management
- **📈 Multi-Source Data**: MT5, Binance, Bybit, News APIs, and sentiment analysis
- **🔍 Comprehensive Monitoring**: Performance metrics, health checks, and alerting

## 🏗️ Architecture

The system follows a modular, event-driven architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │  AI Analysis    │    │   Execution     │
│                 │    │                 │    │                 │
│ • MT5           │───▶│ • SMC Patterns  │───▶│ • MT5 Orders    │
│ • Binance       │    │ • Quasimodo     │    │ • Risk Mgmt     │
│ • News APIs     │    │ • Multi-TF      │    │ • Position Mgmt │
│ • Sentiment     │    │ • Confidence    │    │ • Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Storage   │    │  Signal Bridge  │    │  Risk Engine    │
│                 │    │                 │    │                 │
│ • SQLite        │    │ • Telegram Bot  │    │ • Position Size │
│ • Redis Cache   │    │ • JSON Schema   │    │ • User Mgmt     │
│ • Parquet Files │    │ • Drawdown Ctrl │    │ • Correlation   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎯 Trading Strategy

### Multi-Timeframe Analysis
- **H4**: Big picture trend and major supply/demand zones
- **H1**: Market structure and minor liquidity pools
- **M15**: Entry zone refinement and FVG validation
- **M5**: Execution timing and candle rejection patterns
- **M1**: Immediate entry triggers and confirmation

### SMC/Liquidity Focus
- **Liquidity Zones**: Equal highs/lows, round numbers, previous swings
- **Order Blocks**: Bullish/bearish order blocks and mitigation zones
- **Fair Value Gaps**: Imbalance detection and inefficiency fills
- **Stop Hunt Areas**: Inducement zones and liquidity sweeps

### Risk Management
- **Position Sizing**: 2% risk per trade based on SL distance
- **Daily Limits**: 6% maximum drawdown, $25 maximum loss
- **Consecutive Losses**: Progressive risk reduction (2→1%, 3→0.5%, 4→stop)
- **Correlation Control**: Maximum 70% correlation exposure

## 🛠️ Technology Stack

### Backend & Framework
- **Python 3.11+**: Core application language
- **FastAPI**: High-performance web framework
- **SQLAlchemy**: Database ORM and migrations
- **Pydantic**: Data validation and settings management

### Trading & Data
- **MetaTrader 5**: Primary trading platform integration
- **Binance/Bybit APIs**: Crypto market data
- **News APIs**: Economic calendar and sentiment
- **Pandas/NumPy**: Data processing and analysis

### AI & Machine Learning
- **scikit-learn**: Pattern recognition and analysis
- **Technical Analysis**: Advanced indicator calculations
- **Sentiment Analysis**: News and social media processing

### Infrastructure
- **SQLite**: Portable, lightweight database
- **Redis**: Caching and real-time data
- **Docker**: Containerization and deployment
- **Prometheus/Grafana**: Monitoring and visualization

## 📦 Installation

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- MetaTrader 5 (for live trading)
- Telegram Bot Token

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/telegram-ai-trade.git
   cd telegram-ai-trade
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Trading Bot API: http://localhost:8000
   - Grafana Dashboard: http://localhost:3000 (admin/admin123)
   - Prometheus: http://localhost:9090
   - SQLite Database: ./database/trading_bot.db

### Manual Installation

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up database**
   ```bash
   # SQLite database will be created automatically
   # Database file: ./database/trading_bot.db
   
   # Run migrations (if using Alembic)
   alembic upgrade head
   ```

3. **Configure MT5 connection**
   ```bash
   # Set environment variables
   export MT5_LOGIN=your_login
   export MT5_PASSWORD=your_password
   export MT5_SERVER=your_server
   ```

4. **Start the application**
   ```bash
   python src/main.py
   ```

## ⚙️ Configuration

### Environment Variables

```bash
# Trading Configuration
TRADING_ENV=development
RISK_PER_TRADE_PCT=2.0
MAX_DAILY_DRAWDOWN_PCT=6.0
MAX_DAILY_LOSS_USD=25

# MT5 Configuration
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Database Configuration
DATABASE_URL=sqlite:///./database/trading_bot.db
REDIS_URL=redis://localhost:6379

# API Keys
BINANCE_API_KEY=your_binance_key
BINANCE_SECRET_KEY=your_binance_secret
NEWS_API_KEY=your_news_api_key
```

### Trading Parameters

```yaml
# config/trading.yaml
risk_management:
  risk_per_trade_pct: 2.0
  max_daily_drawdown_pct: 6.0
  max_consecutive_losses: 4
  
position_sizing:
  method: "risk_based_on_sl_distance"
  min_position_size: 0.01
  max_position_size: 10.0
  
execution:
  magic_number: 1001
  slippage_points: 10
  prefer_limit_orders: true
  
session_filters:
  avoid_high_impact_news: true
  prefer_london_ny_overlap: true
  timezone: "Asia/Jakarta"
```

## 📱 Usage

### Telegram Commands

- `/start` - Initialize the bot and show welcome message
- `/status` - Check bot status and current performance
- `/trades` - View recent trades and open positions
- `/performance` - Get performance statistics and reports
- `/settings` - Configure risk parameters and preferences

### Signal Format

The bot generates signals in the following format:

```json
{
  "id": "xau-2025-01-21-0901",
  "symbol": "XAUUSD",
  "bias": "BEARISH",
  "setups": [
    {
      "type": "SELL",
      "entry_zone": [3343.0, 3345.0],
      "entry_style": "limit",
      "sl": 3348.0,
      "tp": [3336.0, 3330.5],
      "confidence": 82,
      "notes": "Retest H1 supply + liquidity sweep; M5 rejection confirmed."
    }
  ],
  "risk": {"risk_per_trade_pct": 2.0},
  "management": {"move_to_BE_at_R1": true, "partial_tp": {"tp1_close_pct": 0.5}}
}
```

## 🧪 Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/

# All tests with coverage
pytest --cov=src --cov-report=html
```

### Test Coverage

- **Unit Tests**: >80% coverage target
- **Integration Tests**: Critical paths 100% coverage
- **Performance Tests**: Load testing and stress testing
- **Security Tests**: Authentication and authorization

## 📊 Monitoring

### Performance Metrics

- **Trading Performance**: Win rate, profit factor, drawdown
- **System Performance**: Latency, throughput, error rates
- **Risk Metrics**: Position correlation, exposure levels
- **Business Metrics**: Daily P&L, trade frequency

### Alerting

- **Risk Alerts**: Drawdown warnings, correlation breaches
- **System Alerts**: Connection failures, high error rates
- **Performance Alerts**: Low win rates, excessive losses
- **Maintenance Alerts**: Scheduled maintenance, updates

## 🔒 Security

### Security Features

- **Authentication**: API key and OAuth2 support
- **Authorization**: Role-based access control
- **Data Protection**: Encryption in transit and at rest
- **Audit Logging**: Complete action history tracking
- **Input Validation**: Comprehensive input sanitization

### Best Practices

- Store sensitive data in environment variables
- Use HTTPS for all communications
- Implement rate limiting and DDoS protection
- Regular security audits and updates
- Follow OWASP security guidelines

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   # Set production environment
   export TRADING_ENV=production
   export LOG_LEVEL=INFO
   ```

2. **Database Migration**
   ```bash
   alembic upgrade head
   ```

3. **Service Deployment**
   ```bash
   # Using Docker Compose
   docker-compose -f docker-compose.prod.yml up -d
   
   # Using Kubernetes
   kubectl apply -f k8s/
   ```

### Scaling

- **Horizontal Scaling**: Multiple bot instances
- **Load Balancing**: Round-robin distribution
- **Database Scaling**: Read replicas and connection pooling
- **Cache Scaling**: Redis cluster for high availability

## 🤝 Contributing

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**
3. **Follow coding standards**
   - Use Black for code formatting
   - Follow PEP 8 guidelines
   - Write comprehensive tests
4. **Submit a pull request**

### Code Standards

- **Python**: PEP 8, Black formatting, type hints
- **Testing**: pytest, >80% coverage
- **Documentation**: Google style docstrings
- **Security**: Input validation, secure defaults

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**This software is for educational and research purposes only. Trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. Always consult with a qualified financial advisor before making investment decisions.**

## 🆘 Support

### Documentation

Please see our comprehensive [Documentation Guide](docs/README.md) that covers:

- Core System Documentation (architecture, quality, monitoring)
- Trading Documentation (strategy, implementation, risk)
- Machine-Readable Rules (in `.cursor/rules/`)

### Community
- [GitHub Issues](https://github.com/yourusername/telegram-ai-trade/issues)
- [Discord Server](https://discord.gg/your-invite)
- [Telegram Group](https://t.me/your-group)

### Professional Support
- Email: support@yourcompany.com
- Priority support for enterprise customers

---

**Built with ❤️ for the trading community**
