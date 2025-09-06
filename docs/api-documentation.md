# API Documentation

## Overview

This document details the API endpoints, interfaces, and integration points of the trading bot system.

## REST API Endpoints

### Market Analysis

#### Get Market Analysis
```http
GET /api/v1/analysis/{symbol}

Parameters:
  - symbol: Trading pair (e.g., "BTCUSDT")
  - timeframe: Optional timeframe (default: "1h")

Response:
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "analysis": {
    "trend": "bullish",
    "support": 50000,
    "resistance": 52000,
    "signals": [
      {
        "type": "ENTRY",
        "price": 51000,
        "confidence": 85
      }
    ]
  }
}
```

#### Generate Trading Signal
```http
POST /api/v1/signals

Request:
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "analysis_type": "full"
}

Response:
{
  "signal_id": "sig_123",
  "symbol": "BTCUSDT",
  "type": "LONG",
  "entry": {
    "price": 51000,
    "style": "LIMIT"
  },
  "exits": {
    "stop_loss": 50500,
    "take_profit": [51500, 52000]
  }
}
```

### Trade Execution

#### Place Trade
```http
POST /api/v1/trades

Request:
{
  "signal_id": "sig_123",
  "broker": "binance",
  "position_size": 0.1
}

Response:
{
  "trade_id": "trade_456",
  "status": "executed",
  "details": {
    "entry_price": 51005,
    "size": 0.1,
    "timestamp": "2025-08-21T10:00:00Z"
  }
}
```

#### Modify Trade
```http
PUT /api/v1/trades/{trade_id}

Request:
{
  "stop_loss": 50600,
  "take_profit": [51600, 52100]
}

Response:
{
  "trade_id": "trade_456",
  "status": "modified",
  "details": {
    "stop_loss": 50600,
    "take_profit": [51600, 52100]
  }
}
```

### Risk Management

#### Get Account Risk Status
```http
GET /api/v1/risk/status

Response:
{
  "account_balance": 10000,
  "open_positions": 2,
  "current_risk": 4.5,
  "daily_drawdown": 2.1,
  "available_risk": 1.5
}
```

### System Status

#### Health Check
```http
GET /api/v1/health

Response:
{
  "status": "healthy",
  "services": {
    "analysis": "up",
    "execution": "up",
    "risk": "up",
    "telegram": "up"
  }
}
```

## WebSocket API

### Market Data Stream
```javascript
// Connect to WebSocket
ws://api/v1/stream/market

// Subscribe to market data
{
  "op": "subscribe",
  "channel": "market",
  "symbols": ["BTCUSDT", "ETHUSDT"]
}

// Market data message
{
  "type": "market_update",
  "symbol": "BTCUSDT",
  "data": {
    "price": 51000,
    "volume": 100,
    "timestamp": "2025-08-21T10:00:00Z"
  }
}
```

### Trade Updates Stream
```javascript
// Connect to WebSocket
ws://api/v1/stream/trades

// Trade update message
{
  "type": "trade_update",
  "trade_id": "trade_456",
  "status": "filled",
  "details": {
    "entry_price": 51005,
    "size": 0.1,
    "timestamp": "2025-08-21T10:00:00Z"
  }
}
```

## Integration Interfaces

### Broker Interface
```python
class IBrokerInterface:
    async def place_order(self, order: Order) -> OrderResult:
        """Place an order with the broker."""
        pass

    async def modify_order(self, order_id: str,
                          modifications: Dict) -> OrderResult:
        """Modify an existing order."""
        pass

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        pass
```

### Analysis Interface
```python
class IAnalysisInterface:
    async def analyze_market(self, data: MarketData) -> Analysis:
        """Analyze market data and generate signals."""
        pass

    async def validate_signal(self, signal: Signal) -> bool:
        """Validate a trading signal."""
        pass
```

## Authentication

### API Key Authentication
```http
Authorization: Bearer <api_key>
```

### WebSocket Authentication
```javascript
{
  "op": "auth",
  "api_key": "<api_key>",
  "timestamp": 1629500000000,
  "signature": "<hmac_signature>"
}
```

## Rate Limits

| Endpoint | Rate Limit |
|----------|------------|
| Market Analysis | 60/minute |
| Trade Execution | 30/minute |
| Risk Status | 120/minute |
| WebSocket Connection | 5/minute |

## Error Codes

| Code | Description |
|------|-------------|
| 1001 | Invalid API key |
| 1002 | Rate limit exceeded |
| 2001 | Invalid trade parameters |
| 2002 | Insufficient funds |
| 3001 | Market data unavailable |
| 3002 | Analysis service error |

## Webhook Integration

### Signal Webhook
```http
POST /webhook/signal

{
  "signal": {
    "symbol": "BTCUSDT",
    "type": "LONG",
    "entry": 51000,
    "stop_loss": 50500,
    "take_profit": [51500, 52000]
  },
  "metadata": {
    "source": "external_analyzer",
    "confidence": 85
  }
}
```

### Trade Webhook
```http
POST /webhook/trade

{
  "trade": {
    "id": "trade_456",
    "symbol": "BTCUSDT",
    "type": "LONG",
    "status": "closed",
    "profit": 500
  }
}
```

## SDKs and Client Libraries

### Python SDK
```python
from trading_bot_sdk import TradingBot

bot = TradingBot(api_key="your_key")

# Get market analysis
analysis = await bot.get_analysis("BTCUSDT")

# Place trade
trade = await bot.place_trade(
    symbol="BTCUSDT",
    side="BUY",
    quantity=0.1
)
```

### TypeScript SDK
```typescript
import { TradingBot } from 'trading-bot-sdk';

const bot = new TradingBot({ apiKey: 'your_key' });

// Get market analysis
const analysis = await bot.getAnalysis('BTCUSDT');

// Place trade
const trade = await bot.placeTrade({
  symbol: 'BTCUSDT',
  side: 'BUY',
  quantity: 0.1
});
```
