# MetaTrader 5 Setup Guide

This guide will help you configure MetaTrader 5 to work with the AI Trading Bot.

## Why is the Bot Using Mock Data?

The bot is currently using mock data because:

1. **MT5 Credentials Not Configured**: The settings file contains placeholder credentials
2. **MT5 Not Connected**: MetaTrader 5 terminal is not properly connected
3. **Missing Broker Configuration**: Broker-specific settings need to be configured

## MT5 Configuration Steps

### 1. Configure MT5 Credentials

Edit `config/settings.yaml` and update the MetaTrader5 section:

```yaml
metatrader5:
  path: "C:\\Program Files\\MetaTrader 5 YourBroker\\terminal64.exe"  # Your MT5 path
  server: "YourBroker-Live01"     # Your broker's server
  login: 1234567890              # Your actual account number
  password: "YourActualPassword"  # Your actual password
  timeout: 60000
  retry_delay: 5
  max_retries: 3
  broker_name: "YourBroker"      # Your broker name (e.g., "Exness", "IC Markets")
```

### 2. Common MT5 Installation Paths

The bot will automatically scan for MT5 installations, but common paths include:

#### Popular Brokers:
- **Exness**: `C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe`
- **IC Markets**: `C:\Program Files\MetaTrader 5 IC Markets Global\terminal64.exe`
- **XM**: `C:\Program Files\MetaTrader 5 XM\terminal64.exe`
- **FXCM**: `C:\Program Files\MetaTrader 5 FXCM\terminal64.exe`
- **OANDA**: `C:\Program Files\MetaTrader 5 OANDA\terminal64.exe`

#### Generic Paths:
- `C:\Program Files\MetaTrader 5\terminal64.exe`
- `C:\Program Files (x86)\MetaTrader 5\terminal64.exe`

### 3. Enable Algorithmic Trading

1. Open MetaTrader 5
2. Go to **Tools** → **Options**
3. Select the **Expert Advisors** tab
4. Check the following options:
   - ✅ Allow algorithmic trading
   - ✅ Allow DLL imports
   - ✅ Allow imports of external experts

### 4. Configure API Access

1. In MT5, go to **Tools** → **Options**
2. Select the **Expert Advisors** tab
3. Ensure **Allow automated trading** is enabled
4. **Restart MT5** after making changes

### 5. Test Connection

After configuring, restart the bot to test the connection:

```bash
python run.py
```

Check the logs for connection status:
- ✅ **Success**: "MT5 initialized successfully"
- ❌ **Failed**: "MT5 credentials not configured, using mock mode"

## Symbol Mapping Configuration

For broker-specific symbol naming, configure symbol mappings:

```bash
# Add symbol mapping (if your broker uses different symbol names)
/addsymbol EURUSD EURUSDm YourBrokerName
```

## Troubleshooting

### Common Issues:

1. **"MT5 credentials not configured"**
   - Update the credentials in `config/settings.yaml`
   - Ensure login, password, and server are correct

2. **"MT5 login failed: Invalid login argument"**
   - Verify your account number and password
   - Check that the server name is correct
   - Ensure your account is active and funded

3. **"No MT5 installations found"**
   - Manually set the path in `config/settings.yaml`
   - Install MetaTrader 5 from your broker

4. **"Terminal not ready"**
   - Ensure MT5 is not already running
   - Close all MT5 instances before starting the bot
   - Check Windows firewall/antivirus settings

### Security Notes:

- **Never commit real credentials** to version control
- Use environment variables for production:
  ```yaml
  login: ${MT5_LOGIN}
  password: ${MT5_PASSWORD}
  server: ${MT5_SERVER}
  ```

- Set environment variables:
  ```bash
  set MT5_LOGIN=your_account_number
  set MT5_PASSWORD=your_password
  set MT5_SERVER=your_server
  ```

## Verification

Once configured correctly, you should see in the logs:
```
INFO | MT5 initialized successfully with path: C:\...\terminal64.exe
INFO | MT5 connected to server: YourBroker-Live01
INFO | Account: 1234567890, Balance: $10,000.00
```

The Telegram bot will then show real account data instead of mock data.

## Support

If you continue to have issues:
1. Check the logs in `logs/ai_trading_bot.log`
2. Verify your broker supports MT5 API access
3. Contact your broker for API configuration assistance
