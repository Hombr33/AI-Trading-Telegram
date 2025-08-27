# Project Architecture

This document describes the architecture of the Institutional-Grade AI-Powered Trading Bot.

## Core Principles
- Modular, event-driven design
- Strict separation of concerns
- Type-safe interfaces between modules
- Real-time performance optimization
- Risk-first approach

## System Components

### 1. AI Analysis Engine (GPT-5 Integration)
```python
class MarketAnalyzer:
    """Institutional-grade market analysis using GPT-5."""
    timeframes = {
        "bias": ["H4", "H1"],
        "setup": ["M15", "M5"],
        "execution": ["M1"]
    }
    
    async def analyze_market(self, data: MarketData) -> AnalysisResult:
        """Perform multi-timeframe analysis."""
        pass
```

### 2. Market Data Collector
- Real-time price feeds from MT4/MT5
- Liquidity pool monitoring
- Order block detection
- Market structure analysis

### 3. Trade Executor
- Smart order routing
- Position sizing based on risk %
- Multi-tier take profit management
- Trailing stop implementation

### 4. Risk Management Engine
```python
class RiskManager:
    """Enforces risk parameters and position limits."""
    def __init__(self):
        self.risk_per_trade = 0.02  # 2%
        self.max_daily_drawdown = 0.06  # 6%
        self.consecutive_loss_rules = [
            (2, "reduce_size_50_percent"),
            (3, "pause_and_review")
        ]
```

### 5. Telegram Bridge
- Command processing
- Real-time trade notifications
- Performance reporting
- Risk alerts

### 6. Scheduler & Automation
- Session-based trading windows
- News event filtering
- Auto position management
- Performance analytics

### 7. Logging & Monitoring
- Structured logging
- Performance metrics
- Error tracking
- System health monitoring

## Integration Points
- MT4/MT5 via ZeroMQ
- Telegram Bot API
- Exchange REST APIs
- WebSocket market data feeds

## Configuration
- Environment-based settings
- Risk parameters
- Trading rules
- API credentials

## Performance Requirements
- Analysis latency < 100ms
- Order execution < 50ms
- Real-time updates
- 99.9% uptime

## Security Architecture
- API key encryption
- Secure websocket connections
- Rate limiting
- Access control

## Deployment Strategy
- Docker containerization
- Automated CI/CD
- Health monitoring
- Backup systems
