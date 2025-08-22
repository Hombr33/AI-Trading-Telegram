# 🤖 AI Trading Bot - Telegram Integration

An institutional-grade AI-powered automated trading bot that integrates OpenAI GPT-5 for market analysis, MT5/MT4 execution via Expert Advisors, and Telegram bot for signal distribution and monitoring.

## 🚀 Features

### 🔄 **2-Way Communication**
- **Socket.IO** for real-time communication with MT5 EA
- **HTTP fallback** for reliable communication when Socket.IO fails
- **Bidirectional data flow** between Python and MT5

### 📊 **Order Execution**
- **Automated order placement** based on AI signals
- **Position management** with real-time monitoring
- **Advanced trailing stops** and partial take profits
- **Risk-based position sizing** (2% risk per trade)

### 🎯 **Trailing Take Profit**
- **Start trailing after 250 points profit**
- **Initial trailing distance: 200 points**
- **Trailing step: 50 points**
- **Breakeven move at 1R profit**
- **Partial TP at 1.5R (50% position)**
- **Full TP at 3.0R**

### 📱 **Telegram Integration**
- **Real-time trading signals** with instant notifications
- **Position updates** and P&L tracking
- **Risk alerts** and drawdown warnings
- **Performance reports** and trading journal
- **Interactive commands** for monitoring and control

### 🛡️ **Risk Management**
- **Maximum 2% risk per trade**
- **Maximum 6% daily drawdown**
- **Consecutive loss management**
- **Correlation exposure limits**
- **Automatic circuit breakers**

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MT5 Terminal  │◄──►│  Python App     │◄──►│  Telegram Bot   │
│   (BridgeEA)    │    │  (FastAPI)      │    │  (Monitoring)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Order Exec    │    │   AI Analyzer   │    │   Notifications │
│   Position Mgmt │    │   Signal Proc   │    │   Risk Alerts   │
│   Trailing Mgmt │    │   Risk Mgmt     │    │   Performance   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔄 Library Integrations & Fallback Mechanisms

The system implements robust fallback mechanisms to ensure reliability:

### 🔌 MetaTrader 5 Integration

- **MT5Executor**: Primary integration with MetaTrader 5 using the official Python package
- **Multiple terminal paths** are tried during connection, with automatic launching if needed
- **Login retry mechanism** with up to 3 attempts and 10-second delays
- **Comprehensive error handling** with detailed logging

### ⚡ Asynchronous MT5 Integration (AioMQL)

- **AioMQLExecutor**: Extends MT5Executor with asynchronous operations using aiomql
- **Graceful fallback** to standard MT5Executor if aiomql is unavailable or fails
- **All trading operations** attempt to use aiomql first, then fall back to MT5Executor
- **Data transformation** between aiomql and standard formats

### 📱 Telegram Bot Integration

- **BaseTelegramBot**: Foundation for Telegram bot functionality using python-telegram-bot
- **Fully asynchronous implementation** with asyncio
- **TradingBot**: Extends BaseTelegramBot with trading-specific commands
- **NotificationManager**: Handles various types of notifications with priority levels

For detailed documentation on library integrations and fallback mechanisms, see [docs/integrations.md](docs/integrations.md).

## 📋 Requirements

### Python Dependencies
```bash
# Core Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0

# Socket.IO and WebSocket
python-socketio>=5.10.0
python-engineio>=4.7.0
websockets>=12.0

# MT5 Integration
MetaTrader5>=5.0.45

# Telegram Bot
python-telegram-bot>=20.7

# Database and Async
sqlalchemy>=2.0.0
aiohttp>=3.9.0
asyncio-mqtt>=0.13.0

# Logging and Monitoring
structlog>=23.2.0
rich>=13.7.0
```

### System Requirements
- **Python 3.8+**
- **MetaTrader 5** terminal
- **PostgreSQL** database (optional, can use SQLite)
- **Telegram Bot Token** (provided: `7773625662:AAHx-Nk8OkoBbU7a4mMP6CQ6fQxplgBpz3E`)

## 🚀 Quick Start

### 📋 Prerequisites

Before running the setup scripts, ensure you have:

- **Windows 10/11** (or compatible Windows version)
- **Python 3.8+** installed and added to PATH
- **Git** installed and added to PATH
- **At least 2GB free disk space**
- **At least 4GB RAM**

### 🎯 Getting Started

#### 1. Download the Repository
```bash
git clone https://github.com/oyi77/telegram-ai-trade
cd telegram-ai-trade
```

#### 2. Run the Setup (Recommended for Windows Users)
Double-click `setup.bat` in the root folder, or run it from command prompt:
```cmd
setup.bat
```

The setup wizard will present you with 8 options:

- **Option 1: Complete Setup** ⭐ (Recommended for first time)
- **Option 2: Install Dependencies Only**
- **Option 3: Setup Database**
- **Option 4: Configure Environment**
- **Option 5: Test Installation**
- **Option 6: Run Application**
- **Option 7: Clean & Reset**
- **Option 8: Exit**

#### 3. First Time Setup (Recommended)
1. **Choose Option 1: Complete Setup**
   - This will install everything automatically
   - Creates virtual environment
   - Installs all Python packages
   - Sets up database
   - Configures environment
   - Creates startup scripts

2. **Configure Your API Keys**
   - Edit `.env.local` file with your actual values:
     - `OPENAI_API_KEY` - Get from [OpenAI Platform](https://platform.openai.com/api-keys)
     - `TELEGRAM_BOT_TOKEN` - Get from [@BotFather](https://t.me/BotFather)
     - `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` - Your MT5 credentials

3. **Test the Installation**
   - Choose Option 5 to run comprehensive tests
   - Ensure all tests pass (80%+ success rate)

4. **Run the Application**
   - Choose Option 6 to start the trading bot
   - Access the web interface at http://localhost:8000

### 🔧 Manual Setup (Alternative)

If you prefer to set up components manually or are on non-Windows systems:

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Configure Environment
Create a `.env` file:
```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=7773625662:AAHx-Nk8OkoBbU7a4mMP6CQ6fQxplgBpz3E
TELEGRAM_CHAT_ID=your_chat_id_here

# MT5 Configuration
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_mt5_server

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/trading_bot
```

#### 3. Start the Application
```bash
# Run the FastAPI application
python run.py

# Or use uvicorn directly
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 4. Test Telegram Bot
```bash
python test_telegram.py
```

### 📁 What Gets Created (Windows Setup)

The setup scripts will create:

- **`venv/`** - Python virtual environment
- **`runtime/`** - Runtime data, logs, and configuration
- **`.env`** - Environment template
- **`.env.local`** - Your actual configuration (edit this!)
- **`.env.example`** - Example configuration
- **`scripts/`** - Additional utility scripts
- **Desktop shortcut** - Quick access to setup

### 🚨 Troubleshooting

#### Common Issues

1. **Python not found**
   - Install Python 3.8+ from [python.org](https://python.org)
   - Ensure Python is added to PATH

2. **Git not found**
   - Install Git from [git-scm.com](https://git-scm.com)
   - Ensure Git is added to PATH

3. **Port 8000 already in use**
   - Stop other applications using port 8000
   - Or change the port in `.env.local`

4. **Database connection failed**
   - Run "Setup Database" option
   - Check file permissions

5. **Package installation failed**
   - Ensure you have internet connection
   - Try running "Install Dependencies" again
   - Check Python version compatibility

#### Reset Everything (Windows)

If something goes wrong, use Option 7 to clean and reset:
```cmd
scripts\clean_reset.bat
```

This will remove everything and let you start fresh.

## 📱 Telegram Bot Commands

### 🚀 **Basic Commands**
- `/start` - Welcome message and bot setup
- `/help` - Show all available commands
- `/status` - System and component status

### 📊 **Trading Commands**
- `/positions` - View open positions
- `/orders` - View pending orders
- `/performance` - Trading performance metrics
- `/risk` - Risk metrics and alerts
- `/journal` - Trading journal entries

### ⚙️ **Configuration**
- `/settings` - Bot settings and configuration
- `/notifications` - Notification preferences
- `/risk_limits` - Risk management settings

## 🔧 Configuration

### Bridge Configuration
```python
# Socket.IO with HTTP fallback
BRIDGE_TOKEN=your_bridge_token
BRIDGE_URL=http://127.0.0.1:8000
SOCKETIO_ENABLED=true
FALLBACK_ENABLED=true
```

### Risk Management
```python
# Risk limits
MAX_RISK_PER_TRADE_PCT=2.0
MAX_DAILY_DRAWDOWN_PCT=6.0
MAX_OPEN_POSITIONS=10
MAX_CORRELATION_EXPOSURE=0.7
```

### Trading Configuration
```python
# Trading parameters
DEFAULT_LOT_SIZE=0.01
MIN_LOT_SIZE=0.01
MAX_LOT_SIZE=10.0
SLIPPAGE_POINTS=10
MAGIC_NUMBER=1001
```

## 🔄 Communication Flow

### 1. **Signal Generation**
```
MT5 Screenshot → AI Analysis → Signal Generation → Telegram Notification
```

### 2. **Order Execution**
```
Telegram Signal → Python App → MT5 Execution → Position Update → Telegram Alert
```

### 3. **Position Management**
```
Position Monitor → Trailing Stop → Partial TP → Full TP → Telegram Update
```

### 4. **Risk Management**
```
Risk Monitor → Alert Generation → Telegram Notification → Action Required
```

## 📊 API Endpoints

### Health and Status
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /status` - System status
- `GET /config` - Configuration

### Bridge Communication
- `POST /api/v1/bridge/order` - Process order
- `POST /api/v1/bridge/signal` - Process signal
- `POST /api/v1/bridge/position_update` - Position update
- `POST /api/v1/bridge/risk_alert` - Risk alert

### Trading Operations
- `GET /api/v1/trading/positions` - Get positions
- `GET /api/v1/trading/orders` - Get orders
- `POST /api/v1/trading/execute` - Execute signal

## 🧪 Testing

### Test Telegram Bot
```bash
python test_telegram.py
```

### Test Socket.IO Bridge
```bash
# Start the application
python run.py

# In another terminal, test Socket.IO connection
python -c "
import socketio
sio = socketio.Client()
sio.connect('http://localhost:8000', auth={'token': 'your_token'})
sio.emit('test', {'message': 'Hello'})
sio.disconnect()
"
```

### Test Order Execution
```bash
python scripts/execute_orders.py
```

## 📁 Project Structure

```
telegram-ai-trade/
├── src/
│   ├── core/           # Configuration and logging
│   ├── bridge/         # Communication bridges
│   ├── execution/      # Trading execution
│   ├── telegram/       # Telegram bot integration
│   └── models/         # Data models
├── ea/                 # MetaTrader 5 Expert Advisors
├── scripts/            # Setup and utility scripts
├── tests/              # Test files
├── requirements.txt    # Python dependencies
├── run.py             # Application startup
├── setup.bat          # Windows setup wizard (main entry point)
└── README.md          # This file
```

## 🛠️ Setup Scripts (Windows)

The project includes comprehensive Windows batch scripts for easy setup and management:

### **Main Entry Point**
- **`setup.bat`** - Interactive menu-driven setup wizard

### **Individual Scripts** (in `/scripts` folder)
- **`complete_setup.bat`** - Full installation from scratch
- **`install_dependencies.bat`** - Python package installation
- **`setup_database.bat`** - Database setup and migrations
- **`configure_environment.bat`** - Environment configuration
- **`test_installation.bat`** - Comprehensive testing suite
- **`run_application.bat`** - Application startup
- **`clean_reset.bat`** - Complete cleanup and reset

### **What the Scripts Do**
- **System requirement checks** (Python, Git, disk space)
- **Virtual environment creation** and management
- **Package installation** with fallback options
- **Database setup** with SQLite and Alembic
- **Environment configuration** with templates
- **Startup script creation** for easy access
- **Desktop shortcuts** for quick setup access
- **Comprehensive testing** of all components
- **Cleanup and reset** capabilities

## 🔒 Security Features

- **Token-based authentication** for bridge communication
- **Environment variable** configuration
- **Input validation** and sanitization
- **Rate limiting** and request throttling
- **Error handling** without information leakage

## 📈 Performance Features

- **Async/await** for high-performance I/O
- **Connection pooling** for database operations
- **Caching** for frequently accessed data
- **Background tasks** for non-blocking operations
- **Real-time updates** via WebSocket/Socket.IO

## 🚨 Monitoring and Alerting

### System Health
- **Component status** monitoring
- **Connection health** checks
- **Performance metrics** tracking
- **Error rate** monitoring

### Trading Alerts
- **Signal notifications** with confidence scores
- **Position updates** and P&L changes
- **Risk limit** breaches
- **Performance milestones**

### Risk Alerts
- **Drawdown warnings** at 3%, 4%, 5%
- **Correlation exposure** alerts
- **Position limit** warnings
- **Emergency stop** notifications

## 🔧 Troubleshooting

### Common Issues

#### 1. **Telegram Bot Not Responding**
```bash
# Check bot token
echo $TELEGRAM_BOT_TOKEN

# Test bot manually
python test_telegram.py
```

#### 2. **Socket.IO Connection Failed**
```bash
# Check bridge configuration
curl http://localhost:8000/config

# Test HTTP fallback
curl -X POST http://localhost:8000/api/v1/bridge/signal \
  -H "Content-Type: application/json" \
  -d '{"test": "signal"}'
```

#### 3. **MT5 Connection Issues**
```bash
# Check MT5 configuration
echo $MT5_LOGIN
echo $MT5_SERVER

# Test MT5 connection
python -c "
import MetaTrader5 as mt5
print(mt5.initialize())
print(mt5.account_info())
"
```

### Logs and Debugging
```bash
# Set debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Check application logs
tail -f logs/app.log

# Check system status
curl http://localhost:8000/status
```

## 🚀 Deployment

### Development
```bash
python run.py
```

### Production
```bash
# Using gunicorn
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Using systemd service
sudo systemctl start ai-trading-bot
sudo systemctl enable ai-trading-bot
```

### Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "run.py"]
```

## ⚙️ MT5 Connectivity (aiomql Optional)

- The app prefers `AioMQLExecutor` which uses `aiomql` if present and gracefully falls back to `MT5Executor` (with a robust mock when `MetaTrader5` is unavailable). No changes needed in managers or routes.
- To enable aiomql:
  - Install `MetaTrader5` and `aiomql` in your environment.
  - Ensure the MT5 terminal is running and configured.
  - Restart the app; the executor detects `aiomql` automatically.
- To disable aiomql: uninstall or omit `aiomql`. The app will continue using the standard executor path with mock fallback.

### Quick verify
```bash
python -c "from src.execution.aiomql_executor import AioMQLExecutor; from src.core.config import config; import asyncio; print(asyncio.run(AioMQLExecutor(config.trading).connect()))"
```

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running
- **Code Documentation**: Inline docstrings and type hints
- **Architecture**: See `docs/architecture.md` (Executor section covers aiomql)
- **Configuration**: See `src/core/config.py`
- **Quick Start Guide**: See `docs/QUICK_START.md` for detailed setup instructions

## 🎯 Next Steps After Setup

### 1. **Read the Documentation**
- Check `docs/` folder for detailed guides
- Review `docs/architecture.md` for system architecture
- Read `docs/trading-strategy.md` for trading strategy details

### 2. **Configure Trading Parameters**
- Edit risk management settings in `.env.local`
- Adjust position sizing and drawdown limits
- Configure session filters and volatility adjustments

### 3. **Test with Demo Account**
- Use demo MT5 account first
- Verify all connections work correctly
- Test signal generation and execution

### 4. **Monitor Performance**
- Check logs in `runtime/logs/`
- Monitor trading performance metrics
- Review risk metrics and alerts

### 5. **Customize Notifications**
- Configure Telegram notification preferences
- Set up risk alert thresholds
- Customize performance reporting

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results.

## 🆘 Support

- **Issues**: Create a GitHub issue
- **Documentation**: Check the README and inline docs
- **Configuration**: Review the config files and environment variables
- **Testing**: Use the provided test scripts

---

**🚀 Ready to start automated trading with AI-powered signals and real-time Telegram monitoring!**
