# 🚀 Multi-Platform Trading Bot Setup Guide

Your AI Trading Bot now supports **multiple trading platforms** simultaneously:

## 🏦 Supported Platforms

### **Forex/CFDs** (via MetaTrader 5)
- **MT5 Direct** - Direct MetaTrader 5 connection
- **AioMQL** - Async MT5 connection (preferred)
- **EA Bridge** - Expert Advisor bridge for advanced features

### **Crypto Exchanges**
- **Binance** - World's largest crypto exchange
- **Bybit** - Popular derivatives platform
- **Bitget** - Growing crypto exchange

## 📋 Quick Setup

### 1. **Environment Configuration**

Copy `.env.example` to `.env` and configure your platforms:

```bash
# Copy example configuration
cp .env.example .env
```

**For Crypto Trading:**
```env
# Binance (recommended)
CRYPTO_BINANCE_API_KEY=your_binance_api_key
CRYPTO_BINANCE_SECRET_KEY=your_binance_secret_key
CRYPTO_BINANCE_TESTNET=true  # Set to false for live trading

# Bybit
CRYPTO_BYBIT_API_KEY=your_bybit_api_key
CRYPTO_BYBIT_SECRET_KEY=your_bybit_secret_key
CRYPTO_BYBIT_TESTNET=true

# Bitget
CRYPTO_BITGET_API_KEY=your_bitget_api_key
CRYPTO_BITGET_SECRET_KEY=your_bitget_secret_key
CRYPTO_BITGET_PASSPHRASE=your_bitget_passphrase
CRYPTO_BITGET_TESTNET=true
```

**For Forex Trading:**
```env
# MT5 (if using direct connection)
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_mt5_server

# Bridge (if using EA)
BRIDGE_TOKEN=your-secure-bridge-token
```

### 2. **Install Dependencies**

```bash
# Core dependencies (already included)
pip install -r requirements.txt

# No additional crypto exchange libraries needed!
# All exchanges use direct HTTP/WebSocket connections
```

### 3. **Test Your Setup**

```bash
# Test all platforms
python tests/test_multi_platform.py

# Test integration
python tests/test_integration.py

# Start the bot
python run.py
```

## 🎯 How It Works

### **Intelligent Symbol Routing**

The platform manager **automatically routes** trades to the appropriate exchange:

```python
# Forex pairs → MT5
"EURUSD" → MT5/AioMQL
"GBPUSD" → MT5/AioMQL

# Crypto pairs → Best available exchange
"BTCUSDT" → Binance (if configured)
"ETHUSDT" → Bybit (fallback)
"ADAUSDT" → Bitget (fallback)
```

### **Unified API**

All platforms use the same interface:

```python
# Works with any platform
result = await platform_manager.place_order({
    "symbol": "BTCUSDT",  # Auto-routes to crypto exchange
    "side": "buy",
    "type": "market",
    "quantity": 0.001
})

result = await platform_manager.place_order({
    "symbol": "EURUSD",   # Auto-routes to MT5
    "side": "buy",
    "type": "limit",
    "quantity": 0.01,
    "price": 1.1000
})
```

## 🔧 Platform-Specific Setup

### **Binance Setup**

1. **Create API Keys:**
   - Go to [Binance API Management](https://www.binance.com/en/my/settings/api-management)
   - Create new API key
   - Enable **Spot Trading** permissions
   - **Important:** Use Testnet for testing: [testnet.binance.vision](https://testnet.binance.vision/)

2. **Configure Security:**
   - Add your server IP to API restrictions
   - Enable only necessary permissions
   - **Never share your secret key**

### **Bybit Setup**

1. **Create API Keys:**
   - Go to [Bybit API Management](https://www.bybit.com/app/user/api-management)
   - Create API key with **Unified Trading Account** permissions
   - **Important:** Use Testnet: [testnet.bybit.com](https://testnet.bybit.com/)

### **Bitget Setup**

1. **Create API Keys:**
   - Go to [Bitget API Management](https://www.bitget.com/api-doc)
   - Create API key + secret + passphrase
   - Enable **Spot Trading** permissions

### **MT5 Setup**

If using direct MT5 connection:

1. **Install MetaTrader 5**
2. **Get trading account** from your broker
3. **Configure connection** in `.env`

If using EA Bridge (recommended):
1. **Install BridgeEA.mq5** in your MT5
2. **Configure bridge token**
3. **Run MT5 with EA active**

## 📊 Monitoring & Management

### **Health Monitoring**

```bash
# Check platform status
curl http://localhost:8000/health

# Response includes all platforms
{
  "status": "healthy",
  "platforms": {
    "connected_platforms": 2,
    "total_platforms": 3,
    "details": {
      "mt5": {"status": "connected", "healthy": true},
      "binance": {"status": "connected", "healthy": true},
      "bybit": {"status": "disconnected", "healthy": false}
    }
  }
}
```

### **Telegram Integration**

The bot automatically **notifies you** of:
- ✅ Platform connections/disconnections
- 📈 Trade executions across all platforms
- ⚠️ Errors or warnings
- 📊 Account summaries from all exchanges

### **Platform Preferences**

Set specific platform preferences:

```python
# Force BTCUSDT to trade on Bybit
platform_manager.set_platform_preference("BTCUSDT", "bybit")

# Check routing
platform = platform_manager.get_platform_for_symbol("BTCUSDT")
print(f"BTCUSDT will trade on: {platform}")
```

## 🔒 Security Best Practices

### **API Keys**
- ✅ **Use testnet** for development
- ✅ **Restrict IP access** to your server only
- ✅ **Minimum permissions** required
- ✅ **Separate keys** for different environments
- ❌ **Never commit keys** to version control

### **Network Security**
- ✅ **HTTPS only** for all API calls
- ✅ **Proper signature** verification
- ✅ **Request timeouts** implemented
- ✅ **Rate limiting** respected

## 🚀 Production Deployment

### **Go Live Checklist**

1. **Test Everything**
   ```bash
   python tests/test_multi_platform.py  # Should pass all tests
   ```

2. **Switch to Live Trading**
   ```env
   CRYPTO_BINANCE_TESTNET=false
   CRYPTO_BYBIT_TESTNET=false
   CRYPTO_BITGET_TESTNET=false
   ```

3. **Fund Accounts**
   - Add funds to exchange accounts
   - Verify minimum balances
   - Test small trades first

4. **Monitor Closely**
   - Watch Telegram notifications
   - Check `/health` endpoint regularly
   - Review trade logs

## 🛟 Troubleshooting

### **Common Issues**

**"No platforms connected"**
- Check API keys in `.env`
- Verify network connectivity
- Check exchange status pages

**"Order placement failed"**
- Check account balances
- Verify symbol format (BTCUSDT not BTC/USDT)
- Check minimum order sizes

**"Symbol routing failed"**
- Update platform preferences
- Check symbol availability on exchange
- Verify exchange supports the trading pair

### **Debug Mode**

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python run.py
```

### **Getting Help**

1. **Check logs** in `/runtime/logs/`
2. **Run health check** `curl localhost:8000/health`
3. **Test individual platforms** with `test_multi_platform.py`
4. **Review configuration** in `.env`

---

## 🎉 You're Ready!

Your AI Trading Bot now supports **unlimited platforms** and can trade:
- **Forex** on MT5
- **Crypto** on Binance, Bybit, Bitget
- **Any symbol** with intelligent routing

**Start with testnet, test thoroughly, then go live!** 🚀

---

*Need help? Check the troubleshooting section or review the test output for specific errors.*
