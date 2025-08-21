# AI Trading Bot EA - Setup and Usage Guide

## Overview

The AI Trading Bot EA is a comprehensive MetaTrader 4/5 Expert Advisor that integrates with your AI trading application to provide automated screenshot capture, signal execution, and position management.

## Features

### Core Functionality
- **Automatic Screenshot Capture**: Captures chart screenshots at configurable intervals
- **API Integration**: Sends screenshots to your AI trading app for analysis
- **Signal Execution**: Receives and executes AI-generated trading signals
- **Risk Management**: Built-in position sizing and risk controls
- **Position Management**: Automatic stop-loss, take-profit, and trailing stop
- **Telegram Integration**: Real-time alerts and notifications

### Trading Capabilities
- Support for all major currency pairs and instruments
- Multiple timeframe analysis (M1, M5, M15, H1, H4)
- Institutional-grade risk management (2% risk per trade)
- Daily loss limits and trade count controls
- Session-based trading filters

## Installation

### Prerequisites
- MetaTrader 4 or MetaTrader 5
- AI Trading Bot application running (API endpoint accessible)
- Internet connection for API communication

### Setup Steps

1. **Copy EA Files**
   - Copy `AI_Trading_Bot.mq4` to `MQL4/Experts/` folder
   - Copy `AI_Trading_Bot.mq5` to `MQL5/Experts/` folder
   - Restart MetaTrader

2. **Configure WebRequest Settings**
   - In MetaTrader, go to Tools → Options → Expert Advisors
   - Check "Allow WebRequest for listed URL"
   - Add your API endpoint: `http://localhost:8000`

3. **Apply Chart Template**
   - Create a chart template with SMC/Liquidity indicators
   - Save as `SMC_Liquidity_Template.tpl`
   - Place in `Templates/` folder

## Configuration

### Input Parameters

| Parameter | Description | Default | Recommended |
|-----------|-------------|---------|-------------|
| `API_ENDPOINT` | Your AI trading app API endpoint | `http://localhost:8000/api/v1/market-analysis/screenshot` | Your actual API URL |
| `API_KEY` | Authentication key for API access | Empty | Your API key |
| `SCREENSHOT_INTERVAL` | Minutes between screenshots | 5 | 5-15 minutes |
| `ENABLE_AUTO_SCREENSHOTS` | Enable automatic screenshot capture | true | true |
| `ENABLE_SIGNAL_EXECUTION` | Enable automatic signal execution | true | true |
| `MAGIC_NUMBER` | Unique identifier for trades | 1001 | Unique number |
| `MAX_RISK_PERCENT` | Maximum risk per trade (%) | 2.0 | 1.0-3.0 |
| `MAX_DAILY_TRADES` | Maximum trades per day | 50 | 20-100 |
| `MAX_DAILY_LOSS` | Maximum daily loss (USD) | 25.0 | Based on account size |
| `ENABLE_TELEGRAM_ALERTS` | Enable Telegram notifications | true | true |

### Chart Setup

#### Required Indicators
- **ATR (14)**: Average True Range for volatility measurement
- **Volume Profile**: Volume analysis for liquidity zones
- **Support/Resistance Levels**: Key price levels
- **Order Block Markers**: Institutional order flow

#### Chart Template
Create a chart template with:
- Clean, professional appearance
- Proper color scheme for SMC analysis
- All required indicators properly positioned
- Multiple timeframe support

## Usage

### Starting the EA

1. **Attach to Chart**
   - Drag EA from Navigator to chart
   - Configure input parameters
   - Click OK to start

2. **Initialization**
   - EA will test API connection
   - Create screenshot directory
   - Apply chart template
   - Start screenshot capture cycle

### Monitoring

#### EA Status
- Check Experts tab for EA status
- Monitor screenshot capture frequency
- Verify API communication

#### Trading Activity
- Monitor open positions
- Check trade execution logs
- Verify risk management

### Troubleshooting

#### Common Issues

**API Connection Failed**
- Verify API endpoint is correct
- Check firewall settings
- Ensure AI trading app is running

**Screenshot Capture Failed**
- Check folder permissions
- Verify chart template exists
- Ensure sufficient disk space

**Signal Execution Failed**
- Verify signal format
- Check risk parameters
- Monitor account balance

## API Integration

### Screenshot Endpoint
```
POST /api/v1/market-analysis/screenshot
```

**Request Payload:**
```json
{
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "timestamp": "2024-01-21T09:01:00Z",
  "image_data": "base64_encoded_screenshot",
  "market_context": {
    "current_price": 2345.67,
    "session": "london",
    "volatility_level": "normal",
    "news_impact": "low"
  }
}
```

### Signal Endpoint
```
GET /api/v1/market-analysis/signals
```

**Response Format:**
```json
{
  "signals": [
    {
      "type": "BUY",
      "symbol": "XAUUSD",
      "entry_zone": [2340.0, 2345.0],
      "stop_loss": 2335.0,
      "take_profit": [2350.0, 2360.0],
      "confidence": 85,
      "notes": "H1 breakout confirmed"
    }
  ]
}
```

## Risk Management

### Position Sizing
- Risk-based position sizing (2% per trade)
- Automatic lot size calculation
- Respects broker limits

### Daily Limits
- Maximum 50 trades per day
- Maximum $25 daily loss
- Automatic trading pause on limits

### Consecutive Loss Management
- 2 losses: Reduce size by 50%
- 3 losses: Pause trading for 2 hours
- 4 losses: Emergency stop

## Performance Optimization

### Screenshot Optimization
- Compress images before sending
- Use efficient encoding
- Optimize capture timing

### API Communication
- Implement retry logic
- Use connection pooling
- Monitor response times

### Memory Management
- Clean up old screenshots
- Optimize indicator usage
- Monitor resource consumption

## Security Considerations

### API Security
- Use HTTPS endpoints
- Implement authentication
- Rate limiting

### Data Protection
- Encrypt sensitive data
- Secure API keys
- Audit logging

## Support and Maintenance

### Regular Maintenance
- Monitor EA performance
- Update chart templates
- Review risk parameters

### Performance Monitoring
- Track screenshot success rate
- Monitor signal execution
- Analyze trading performance

### Updates
- Keep EA updated
- Monitor API changes
- Test new features

## Disclaimer

This EA is for educational and research purposes. Trading involves substantial risk. Always test thoroughly in demo accounts before live trading.
