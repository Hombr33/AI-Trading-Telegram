# 🚀 AI Trading Bot - Cross-Platform Deployment Guide

## 📋 Overview

This guide provides step-by-step deployment instructions for the AI Trading Bot across different operating systems. The bot supports both Forex trading (via MetaTrader 5) and cryptocurrency trading (via multiple exchanges).

## 🏗️ Architecture Summary

- **Windows**: Full functionality (MT5 + Crypto)
- **Linux/macOS**: Crypto-only mode (MT5 not supported)
- **Docker**: Cross-platform containerized deployment
- **Cloud**: AWS, GCP, Azure compatible

---

## 🪟 Windows Deployment

### Prerequisites
- Python 3.8+ (recommended: 3.12)
- MetaTrader 5 terminal (for Forex trading)
- Git

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd telegram-ai-trade
```

### Step 2: Install Dependencies
```bash
# Install all dependencies including MT5
pip install -r requirements-windows.txt
pip install -r requirements.txt
```

### Step 3: Configuration
```bash
# Copy environment template
copy .env.example .env
```

Edit `.env` file:
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_ALLOWED_USERS=user1,user2

# MT5 Configuration (for Forex)
MT5_LOGIN=your_mt5_account
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_mt5_server

# Crypto Exchange APIs
CRYPTO_BINANCE_API_KEY=your_binance_api_key
CRYPTO_BINANCE_SECRET_KEY=your_binance_secret
CRYPTO_BINANCE_TESTNET=true

# Add other crypto exchanges as needed
```

### Step 4: Database Setup
```bash
# Initialize database
alembic upgrade head
```

### Step 5: Run Application
```bash
# Start the bot
python run.py
```

### Step 6: Verify Installation
```bash
# Test multi-platform functionality
python tests/test_multi_platform.py
```

---

## 🐧 Linux Deployment

### Prerequisites
- Python 3.8+ (recommended: 3.12)
- pip, virtualenv
- Git

### Step 1: System Setup
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# CentOS/RHEL
sudo yum install python3 python3-pip git
```

### Step 2: Clone and Setup
```bash
git clone <repository-url>
cd telegram-ai-trade

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (crypto-only)
pip install -r requirements.txt
```

### Step 3: Configuration
```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

Configure crypto-only setup:
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_ALLOWED_USERS=user1,user2

# Crypto Exchanges (no MT5 on Linux)
CRYPTO_BINANCE_API_KEY=your_binance_api_key
CRYPTO_BINANCE_SECRET_KEY=your_binance_secret
CRYPTO_BINANCE_TESTNET=true

CRYPTO_BYBIT_API_KEY=your_bybit_api_key
CRYPTO_BYBIT_SECRET_KEY=your_bybit_secret
CRYPTO_BYBIT_TESTNET=true
```

### Step 4: Database Setup
```bash
alembic upgrade head
```

### Step 5: Run Application
```bash
python run.py
```

### Step 6: Test Crypto-Only Mode
```bash
python tests/test_crypto_only.py
```

### Step 7: Production Setup (Optional)
```bash
# Install systemd service
sudo nano /etc/systemd/system/trading-bot.service
```

Service file content:
```ini
[Unit]
Description=AI Trading Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/telegram-ai-trade
Environment=PATH=/path/to/telegram-ai-trade/venv/bin
ExecStart=/path/to/telegram-ai-trade/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

---

## 🍎 macOS Deployment

### Prerequisites
- Python 3.8+ (use Homebrew or pyenv)
- Git

### Step 1: Install Python
```bash
# Using Homebrew
brew install python@3.12

# Or using pyenv (recommended)
brew install pyenv
pyenv install 3.12.10
pyenv global 3.12.10
```

### Step 2: Clone and Setup
```bash
git clone <repository-url>
cd telegram-ai-trade

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configuration
```bash
cp .env.example .env
nano .env  # or code .env
```

### Step 4: Database and Run
```bash
# Setup database
alembic upgrade head

# Test crypto functionality
python tests/test_crypto_only.py

# Run the bot
python run.py
```

---

## 🐳 Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 trading && chown -R trading:trading /app
USER trading

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "run.py"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  trading-bot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - CRYPTO_BINANCE_API_KEY=${CRYPTO_BINANCE_API_KEY}
      - CRYPTO_BINANCE_SECRET_KEY=${CRYPTO_BINANCE_SECRET_KEY}
    volumes:
      - ./runtime:/app/runtime
    restart: unless-stopped

  db:
    image: sqlite:latest
    volumes:
      - ./runtime/data:/data
```

### Deploy with Docker
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f trading-bot

# Stop
docker-compose down
```

---

## ☁️ Cloud Deployment

### AWS EC2
```bash
# Launch EC2 instance (Ubuntu 22.04 LTS)
# Connect via SSH

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER

# Clone and deploy
git clone <repository-url>
cd telegram-ai-trade
cp .env.example .env
# Edit .env with your keys

# Deploy with Docker
docker-compose up -d
```

### Google Cloud Platform
```bash
# Use Cloud Run for serverless deployment
gcloud run deploy trading-bot \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Container Instances
```bash
# Create resource group
az group create --name trading-bot-rg --location eastus

# Deploy container
az container create \
  --resource-group trading-bot-rg \
  --name trading-bot \
  --image your-registry/trading-bot:latest \
  --dns-name-label trading-bot-unique \
  --ports 8000
```

---

## 🔧 Configuration Management

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot token |
| `TELEGRAM_ALLOWED_USERS` | Yes | Comma-separated user IDs |
| `CRYPTO_BINANCE_API_KEY` | Optional | Binance API key |
| `CRYPTO_BINANCE_SECRET_KEY` | Optional | Binance secret key |
| `CRYPTO_BINANCE_TESTNET` | Optional | Use testnet (true/false) |
| `MT5_LOGIN` | Windows only | MT5 account login |
| `MT5_PASSWORD` | Windows only | MT5 account password |
| `MT5_SERVER` | Windows only | MT5 server |

### API Key Setup

**Binance:**
1. Go to Binance API Management
2. Create new API key
3. Enable "Enable Spot & Margin Trading"
4. Add IP restrictions for security
5. Use testnet for development

**Bybit:**
1. Go to API Management in Bybit
2. Create API key with trading permissions
3. Set IP restrictions
4. Use testnet for development

**Bitget:**
1. Create API key in Bitget
2. Set trading permissions
3. Create passphrase
4. Use testnet for development

---

## 🔍 Testing and Validation

### Pre-deployment Tests
```bash
# Test all dependencies
python tests/test_crypto_only.py

# Test multi-platform (Windows only)
python tests/test_multi_platform.py

# Test integration
python tests/test_integration.py
```

### Health Checks
```bash
# Check API endpoint
curl http://localhost:8000/health

# Check logs
tail -f runtime/logs/trading_bot.log

# Check database
sqlite3 runtime/data/trade.sqlite3 ".tables"
```

### Monitoring
- **Logs**: `runtime/logs/`
- **Database**: `runtime/data/trade.sqlite3`
- **Metrics**: `/metrics` endpoint (Prometheus compatible)
- **Health**: `/health` endpoint

---

## 🚨 Troubleshooting

### Common Issues

**1. Import Errors on Linux/macOS**
```bash
# MT5 not available - expected behavior
# Use crypto-only mode
python tests/test_crypto_only.py
```

**2. API Connection Failures**
```bash
# Check API keys and network
# Verify testnet/live environment settings
# Check IP restrictions on exchange
```

**3. Database Issues**
```bash
# Reset database
alembic downgrade base
alembic upgrade head
```

**4. Permission Errors**
```bash
# Fix file permissions
chmod +x run.py
chown -R user:user runtime/
```

### Log Analysis
```bash
# View recent logs
tail -100 runtime/logs/trading_bot.log

# Search for errors
grep "ERROR" runtime/logs/trading_bot.log

# Monitor live logs
tail -f runtime/logs/trading_bot.log
```

---

## 🔐 Security Best Practices

### API Security
- Use testnet for development
- Set IP restrictions on API keys
- Use minimal required permissions
- Rotate API keys regularly
- Store secrets in environment variables

### Server Security
- Use firewall (UFW on Ubuntu)
- Keep system updated
- Use non-root user for application
- Enable fail2ban for SSH protection
- Use SSL/TLS for web endpoints

### Monitoring
- Set up alerting for errors
- Monitor resource usage
- Track trading performance
- Log all trading activities

---

## 📞 Support

For deployment issues:
1. Check logs in `runtime/logs/`
2. Run diagnostic tests
3. Verify configuration
4. Check API connectivity
5. Review platform-specific requirements

---

*Last updated: January 2025*
