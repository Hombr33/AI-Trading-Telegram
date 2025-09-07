# Multi-User Trading System Documentation

## Overview

The AI Trading Bot now supports a comprehensive multi-user system that allows multiple users to configure and manage their trading settings through Telegram, with all configurations saved server-side.

## Key Features

### 1. User Management System
- **Admin Privileges**: User ID `6077091585` has initial admin access
- **Role-Based Access**: Admin and regular user roles with different permissions
- **Subscription Management**: Users must be subscribed to access trading features
- **User Registration**: Automatic user creation on first Telegram interaction

### 2. Platform Integration

#### MT5 Integration
1. User installs EA file from `/ea/` directory on MT5 terminal
2. EA displays API key via popup
3. User registers by entering API key in Telegram (`/register_mt5`)
4. All EA control happens through Telegram commands

#### Crypto Integration
1. User provides API key and secret via Telegram (`/register_crypto`)
2. System validates and registers credentials
3. Supports Binance and Bybit exchanges
4. Automatic testnet mode for safety

### 3. Configuration System

Users can customize:
- **Risk Settings**: Position sizing, drawdown limits, consecutive loss rules
- **Symbol Settings**: Active trading pairs, confidence thresholds, session preferences
- **Signal Generation**: Analysis frequency, timeframes, confluence requirements
- **Model Settings**: OpenAI parameters, analysis prompts, context windows
- **Trading Settings**: Order types, execution rules, stop loss/take profit management
- **Rules**: Session filters, news avoidance, volatility adjustments

## Telegram Commands

### User Commands
- `/start` - Welcome message and initial setup
- `/help` - Comprehensive command help
- `/config` - Manage trading configurations
- `/register_mt5` - Register MT5 EA connection
- `/register_crypto` - Register crypto exchange
- `/positions` - View current positions
- `/status` - Account and system status
- `/symbols` - Manage symbol subscriptions

### Admin Commands
- `/users` - View all registered users
- `/add_admin <user_id>` - Promote user to admin
- `/remove_admin <user_id>` - Remove admin privileges
- `/set_subscription <user_id> <status>` - Manage user subscriptions
- `/server_config` - Manage server settings
- `/restart` - Restart trading system
- `/logs` - View system logs
- `/close_all` - Emergency close all positions

## Database Schema

### Core Tables
- `telegram_users` - User accounts and roles
- `user_configurations` - Individual user settings
- `platform_connections` - MT5/Crypto API connections
- `signal_subscriptions` - Symbol-specific subscriptions
- `server_configurations` - System-wide settings

## API Endpoints

### Multi-User API (`/api/v1/multi-user/`)
- `POST /signal/process` - Process and distribute signals
- `GET /users` - Get all users (admin only)
- `POST /users/subscription` - Set user subscription
- `POST /users/platform-connection` - Register platform connection
- `GET /users/{id}/connections` - Get user connections
- `POST /users/configuration` - Set user configuration
- `GET /users/{id}/configuration` - Get user configuration
- `GET /stats` - Service statistics

## Configuration Examples

### Risk Configuration
```json
{
  "risk_per_trade_pct": 2.0,
  "max_daily_drawdown_pct": 6.0,
  "max_daily_loss_usd": 25.0,
  "consecutive_loss_rules": [
    {"losses": 2, "action": "reduce_size_50_percent"},
    {"losses": 3, "action": "pause_and_review"}
  ]
}
```

### Symbol Configuration
```json
{
  "active_symbols": ["XAUUSD", "EURUSD", "GBPUSD"],
  "symbol_settings": {
    "XAUUSD": {
      "min_confidence": 70,
      "max_spread": 5,
      "preferred_sessions": ["london", "newyork"]
    }
  }
}
```

## Environment Variables

Add to your `.env` file:
```bash
# Multi-User System Configuration
INITIAL_ADMIN_TELEGRAM_ID=6077091585
DEFAULT_EA_SERVER_ENDPOINT=http://127.0.0.1:8000

# Signal Distribution Configuration
SIGNAL_DISTRIBUTION_ENABLED=true
SIGNAL_IMMEDIATE_THRESHOLD=80
SIGNAL_DELAYED_THRESHOLD=60
SIGNAL_BATCH_THRESHOLD=40
```

## Setup Instructions

### 1. Database Migration
```bash
cd /path/to/telegram-ai-trade
alembic upgrade head
```

### 2. Environment Configuration
Copy and update `.env.example` to `.env` with your settings.

### 3. Start the System
```bash
python -m src.main
```

### 4. Initial Admin Setup
The user with Telegram ID `6077091585` will automatically have admin privileges on first interaction.

## EA Integration

### Server Endpoints
The EA connects to servers specified in the configuration. Default endpoint: `http://127.0.0.1:8000`

### EA Communication
- All MT5 operations (positions, orders, history) handled through EA
- Real-time position updates via Socket.IO
- HTTP fallback for reliability
- API key authentication for security

## Signal Distribution

### Distribution Tiers
- **Immediate** (80%+ confidence): Instant delivery
- **Delayed** (60-79% confidence): 5-minute delay
- **Batch** (40-59% confidence): Hourly summary

### User Filtering
Signals are filtered based on:
- User symbol subscriptions
- Minimum confidence thresholds
- Session preferences
- Risk tolerance settings

## Security Features

- API key encryption
- Role-based access control
- Audit logging for all actions
- Secure credential storage
- Session management

## Monitoring and Alerts

### System Health
- Connection status monitoring
- Performance metrics tracking
- Error rate monitoring
- Resource usage alerts

### Trading Performance
- Win rate tracking
- Profit factor calculation
- Risk-adjusted returns
- Drawdown monitoring

## Troubleshooting

### Common Issues
1. **EA Connection Failed**: Check API key and server endpoint
2. **Signal Not Received**: Verify symbol subscriptions and confidence thresholds
3. **Permission Denied**: Ensure user has active subscription
4. **Configuration Not Saved**: Check user authorization and config format

### Logs Location
System logs are available through:
- `/logs` admin command in Telegram
- Application log files
- Database audit trail

## Future Enhancements

- Machine learning model integration
- Advanced correlation analysis
- Multi-broker support
- Mobile application
- Portfolio-level risk management

## Support

For technical support or feature requests, contact the development team or create an issue in the project repository.
