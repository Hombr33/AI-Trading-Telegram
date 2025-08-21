# Risk Management

## Overview

Comprehensive risk management system designed to protect trading capital and ensure sustainable performance.

## Position Sizing

### Core Algorithm
```python
def calculate_position_size(
    account_balance: float,
    risk_percentage: float,
    stop_loss_pips: int,
    pip_value: float,
    max_position_size: Optional[float] = None
) -> float:
    """
    Calculate safe position size based on risk parameters.
    
    Args:
        account_balance: Current account balance
        risk_percentage: Risk per trade (e.g., 2.0 for 2%)
        stop_loss_pips: Distance to stop loss in pips
        pip_value: Value of one pip in account currency
        max_position_size: Optional maximum position size
        
    Returns:
        Position size in standard lots
    """
    risk_amount = account_balance * (risk_percentage / 100)
    position_size = risk_amount / (stop_loss_pips * pip_value)
    
    if max_position_size:
        position_size = min(position_size, max_position_size)
        
    return position_size
```

### Risk Limits
```python
RISK_LIMITS = {
    "per_trade": 2.0,      # Percentage
    "daily_max": 6.0,      # Percentage
    "weekly_max": 15.0,    # Percentage
    "max_positions": 3,    # Count
    "max_correlation": 0.7 # Correlation coefficient
}
```

## Drawdown Control

### Daily Drawdown Manager
```python
class DrawdownManager:
    def __init__(self, max_daily_dd: float):
        self.max_daily_dd = max_daily_dd
        self.daily_high = 0.0
        self.current_dd = 0.0
    
    def update(self, balance: float) -> bool:
        """
        Update drawdown calculations and check limits.
        Returns False if trading should be stopped.
        """
        self.daily_high = max(self.daily_high, balance)
        self.current_dd = (self.daily_high - balance) / self.daily_high * 100
        
        return self.current_dd <= self.max_daily_dd
```

### Recovery Rules
1. 2% DD: Reduce position size by 25%
2. 4% DD: Reduce position size by 50%
3. 6% DD: Stop trading for the day

## Exposure Management

### Position Correlation
```python
def check_correlation(
    positions: List[Position],
    new_symbol: str,
    max_correlation: float
) -> bool:
    """Check if adding new position maintains safe correlation levels."""
    correlations = calculate_correlations(positions, new_symbol)
    return all(c <= max_correlation for c in correlations)
```

### Exposure Limits
```python
EXPOSURE_LIMITS = {
    "single_pair": 0.05,    # 5% of account
    "single_group": 0.15,   # 15% for correlated pairs
    "total": 0.25          # 25% total exposure
}
```

## Stop-Loss Strategy

### Dynamic Stop-Loss
```python
class DynamicStopLoss:
    def __init__(self, atr_multiple: float = 2.0):
        self.atr_multiple = atr_multiple
    
    def calculate_stop(
        self,
        entry_price: float,
        atr: float,
        direction: str
    ) -> float:
        """Calculate dynamic stop-loss based on ATR."""
        distance = atr * self.atr_multiple
        
        if direction == "LONG":
            return entry_price - distance
        return entry_price + distance
```

### Trailing Stop
```python
def update_trailing_stop(
    current_price: float,
    direction: str,
    trail_points: int,
    current_stop: float
) -> float:
    """Update trailing stop based on price movement."""
    if direction == "LONG":
        return max(
            current_stop,
            current_price - trail_points
        )
    return min(
        current_stop,
        current_price + trail_points
    )
```

## Account Protection

### Circuit Breakers
```python
CIRCUIT_BREAKERS = {
    "consecutive_losses": 3,
    "hourly_loss_limit": 4.0,
    "equity_warning": 95.0,  # Percentage of starting balance
    "critical_stop": 90.0    # Percentage of starting balance
}
```

### Recovery Mode
```python
class RecoveryMode:
    def __init__(self):
        self.active = False
        self.trigger_reason = None
        self.start_time = None
        
    def activate(self, reason: str):
        """Activate recovery mode with specific parameters."""
        self.active = True
        self.trigger_reason = reason
        self.start_time = datetime.now()
        
        if reason == "consecutive_losses":
            self.duration = timedelta(hours=12)
            self.position_size_modifier = 0.5
        elif reason == "daily_drawdown":
            self.duration = timedelta(days=1)
            self.position_size_modifier = 0.25
```

## Risk Monitoring

### Real-time Metrics
```python
class RiskMetrics:
    def __init__(self):
        self.open_risk = 0.0
        self.daily_realized = 0.0
        self.max_drawdown = 0.0
        self.win_streak = 0
        self.loss_streak = 0
        
    def update(self, trade_result: TradeResult):
        """Update risk metrics with new trade result."""
        pass
        
    def get_risk_score(self) -> float:
        """Calculate current risk score (0-100)."""
        pass
```

### Alert System
```python
class RiskAlert:
    def __init__(self):
        self.levels = {
            "warning": 70,
            "danger": 85,
            "critical": 95
        }
        
    async def check_alerts(self, metrics: RiskMetrics):
        """Check and send risk alerts."""
        risk_score = metrics.get_risk_score()
        
        for level, threshold in self.levels.items():
            if risk_score >= threshold:
                await self.send_alert(level, metrics)
```

## Performance Analysis

### Risk-Adjusted Returns
```python
def calculate_risk_metrics(trades: List[Trade]) -> Dict:
    """Calculate comprehensive risk-adjusted performance metrics."""
    return {
        "sharpe_ratio": calculate_sharpe_ratio(trades),
        "sortino_ratio": calculate_sortino_ratio(trades),
        "profit_factor": calculate_profit_factor(trades),
        "recovery_factor": calculate_recovery_factor(trades),
        "risk_reward_ratio": calculate_risk_reward_ratio(trades)
    }
```

### Position Quality
```python
def analyze_position_quality(
    trade: Trade,
    market_conditions: MarketConditions
) -> float:
    """
    Score trade quality based on:
    - Entry precision
    - Risk-reward ratio
    - Market conditions
    - Technical confluences
    """
    pass
```

## Risk Reporting

### Daily Report
```python
async def generate_daily_risk_report() -> Report:
    """Generate comprehensive daily risk report."""
    return {
        "balance_change": calculate_daily_change(),
        "max_drawdown": calculate_max_drawdown(),
        "open_exposure": calculate_total_exposure(),
        "risk_metrics": calculate_risk_metrics(),
        "position_quality": analyze_positions(),
        "warnings": generate_risk_warnings()
    }
```

### Weekly Analysis
```python
def analyze_weekly_performance() -> Analysis:
    """Analyze weekly performance and risk patterns."""
    return {
        "profit_loss": calculate_weekly_pnl(),
        "risk_adjustment": suggest_risk_adjustments(),
        "pattern_analysis": analyze_trading_patterns(),
        "improvement_areas": identify_improvement_areas()
    }
```
