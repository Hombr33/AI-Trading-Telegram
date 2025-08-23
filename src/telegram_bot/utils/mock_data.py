"""Mock data utilities for Telegram bot."""

from typing import Dict, List, Any
from datetime import datetime, timezone, timedelta
import random
import sys


def get_system_status() -> Dict[str, Any]:
    """Get mock system status data."""
    return {
        "status": "Online",
        "bot_status": "Online",
        "mt5_connection": "Connected",
        "connection": "Connected",
        "ai_analyzer": "Active",
        "risk_manager": "Active",
        "last_update": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        "last_updated": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        "uptime": "5d 12h 34m",
        "cpu_usage": 35.5,
        "memory_usage": 42.8,
        "daily_drawdown": 1.8,
        "total_positions": 3,
        "open_positions": 3,
        "active_positions": 3,
        "active_trades": 2,
        "pending_orders": 2,
        "pending_signals": 1,
        "active_strategies": 2,
    }


def get_risk_metrics() -> Dict[str, Any]:
    """Get mock risk metrics data."""
    return {
        "drawdown": 0.05,
        "max_drawdown": 0.15,
        "daily_var": 150.0,
        "daily_var_pct": 0.03,
        "margin_level": 85.5,
        "exposure": 0.25,
        "max_exposure": 0.50,
        "largest_position": 1000.0,
        "largest_position_pct": 0.20,
        "position_correlation": 0.15,
        "market_volatility": 0.18,
        "correlation_to_spx": 0.35,
        "correlation_to_btc": 0.25,
        "risk_rating": "Moderate"
    }

def get_performance() -> Dict[str, Any]:
    """Get mock performance data."""
    return {
        "total_profit": 1250.50,
        "daily_profit": 125.30,
        "weekly_profit": 450.75,
        "monthly_profit": 1250.50,
        "today_profit": 125.30,
        "week_profit": 450.75,
        "month_profit": 1250.50,
        "today_trades": 5,
        "week_trades": 18,
        "month_trades": 45,
        "win_rate": 0.65,
        "profit_factor": 1.85,
        "sharpe_ratio": 1.32,
        "avg_winner": 50.25,
        "avg_loser": -30.15,
        "avg_trade": 14.71,
        "largest_winner": 250.00,
        "largest_loser": -150.00,
        "best_trade": 250.00,
        "worst_trade": -150.00,
        "total_trades": 85,
        "winning_trades": 55,
        "losing_trades": 30,
        "avg_holding_time": "4h 23m"
    }

def get_system_info() -> Dict[str, Any]:
    """Get mock system info data."""
    return {
        "cpu_usage": 35.5,
        "memory_usage": 42.8,
        "disk_usage": 68.2,
        "network_latency": 15,
        "uptime": "5d 12h 34m",
        "last_backup": "2025-08-22 15:30:00",
        "errors_24h": 2,
        "warnings_24h": 5
    }


def get_trading_journal() -> List[Dict[str, Any]]:
    """Get mock trading journal data."""
    return [
        {
            "id": 1,
            "symbol": "EURUSD",
            "type": "BUY",
            "entry": 1.08743,
            "exit": 1.08921,
            "profit": 17.8,
            "date": "2025-08-23 15:30:00"
        },
        {
            "id": 2,
            "symbol": "GBPUSD",
            "type": "SELL",
            "entry": 1.27432,
            "exit": 1.27321,
            "profit": 16.65,
            "date": "2025-08-23 14:45:00"
        }
    ]


def get_mock_signals() -> List[Dict[str, Any]]:
    """Get mock trading signals data."""
    return [
        {
            "symbol": "EURUSD",
            "direction": "BUY",
            "entry_price": 1.08743,
            "target_price": 1.08950,
            "stop_loss": 1.08600,
            "strength": 0.82,
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=15)).strftime("%H:%M:%S"),
            "timeframe": "H1",
            "confidence": 85.5
        },
        {
            "symbol": "GBPUSD",
            "direction": "SELL",
            "entry_price": 1.27432,
            "target_price": 1.27200,
            "stop_loss": 1.27550,
            "strength": 0.75,
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=25)).strftime("%H:%M:%S"),
            "timeframe": "H4",
            "confidence": 78.2
        },
        {
            "symbol": "USDJPY",
            "direction": "BUY",
            "entry_price": 149.213,
            "target_price": 149.450,
            "stop_loss": 149.000,
            "strength": 0.68,
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=35)).strftime("%H:%M:%S"),
            "timeframe": "H1",
            "confidence": 72.8
        }
    ]


def get_mock_positions() -> List[Dict[str, Any]]:
    """Get mock positions data."""
    return [
        {
            "symbol": "EURUSD",
            "type": "BUY",
            "volume": 0.1,
            "price_open": 1.08743,
            "price_current": 1.08821,
            "sl": 1.08600,
            "tp": 1.08950,
            "profit": 7.8,
            "profit_pct": 0.072,
            "swap": -0.85,
            "time": (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "comment": "AI Signal #1234"
        },
        {
            "symbol": "GBPUSD",
            "type": "SELL",
            "volume": 0.15,
            "price_open": 1.27432,
            "price_current": 1.27321,
            "sl": 1.27550,
            "tp": 1.27200,
            "profit": 16.65,
            "profit_pct": 0.087,
            "swap": 1.25,
            "time": (datetime.now(timezone.utc) - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
            "comment": "AI Signal #1235"
        }
    ]


def get_mock_orders() -> List[Dict[str, Any]]:
    """Get mock pending orders data."""
    return [
        {
            "symbol": "USDJPY",
            "type": "BUY_LIMIT",
            "volume": 0.2,
            "price": 149.000,
            "sl": 148.750,
            "tp": 149.300,
            "order_type": "Buy Limit",
            "status": "Pending",
            "time": (datetime.now(timezone.utc) - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
            "comment": "AI Signal #1236"
        },
        {
            "symbol": "XAUUSD", 
            "type": "SELL_STOP",
            "volume": 0.05,
            "price": 2025.50,
            "sl": 2035.00,
            "tp": 2015.00,
            "order_type": "Sell Stop",
            "status": "Pending",
            "time": (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
            "comment": "AI Signal #1237"
        }
    ]


def get_mock_system_status() -> Dict[str, Any]:
    """Get mock system status data."""
    return {
        "status": "Online",
        "bot_status": "Online",
        "mt5_connection": "Mock Mode",
        "connection": "Mock Mode",
        "ai_analyzer": "Active",
        "risk_manager": "Active",
        "last_update": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        "last_updated": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        "uptime": "5h 23m",
        "cpu_usage": 35.5,
        "memory_usage": 42.8,
        "daily_drawdown": 1.8,
        "total_positions": 2,
        "open_positions": 2,
        "active_positions": 2,
        "active_trades": 2,
        "pending_orders": 1,
        "pending_signals": 1,
        "active_strategies": 2,
        "errors_24h": 0,
        "warnings_24h": 2
    }


def get_mock_risk_metrics() -> Dict[str, Any]:
    """Get mock risk metrics data."""
    return {
        "drawdown": 0.018,
        "max_drawdown": 0.035,
        "daily_var": 125.50,
        "daily_var_pct": 0.025,
        "margin_level": 325.8,
        "exposure": 0.15,
        "max_exposure": 0.50,
        "largest_position": 850.0,
        "largest_position_pct": 0.085,
        "position_correlation": 0.12,
        "market_volatility": 0.16,
        "correlation_to_spx": 0.28,
        "correlation_to_btc": 0.15,
        "risk_rating": "Low",
        "risk_score": 3.2,
        "portfolio_beta": 0.85
    }


def get_market_analysis() -> Dict[str, Any]:
    """Get mock market analysis data."""
    return {
        "trend": "Bullish",
        "strength": 0.75,
        "volatility": "Medium",
        "recommendation": "Buy",
        "confidence": 0.82,
        "support_levels": [1.0850, 1.0825],
        "resistance_levels": [1.0900, 1.0925],
        "signals": [
            {"type": "MA Cross", "direction": "Up", "timeframe": "H1"},
            {"type": "RSI", "value": 62, "interpretation": "Bullish"}
        ]
    }


def get_mock_performance() -> Dict[str, Any]:
    """Get mock performance data.
    
    Returns:
        Dict: Mock performance data.
    """
    return {
        "win_rate": 68.5,
        "profit_factor": 1.85,
        "risk_reward_ratio": 1.65,
        "max_drawdown": 7.2,
        "sharpe_ratio": 1.32,
        "total_trades": 124,
        "profitable_trades": 85,
        "losing_trades": 39,
    }


def get_mock_account_info() -> Dict[str, Any]:
    """Get mock account information.
    
    Returns:
        Dict: Mock account information.
    """
    return {
        "balance": 10245.75,
        "equity": 10321.43,
        "margin": 1532.21,
        "free_margin": 8789.22,
        "margin_level": 673.65,
        "leverage": 100,
        "currency": "USD",
        "name": "Demo Account",
        "server": "MetaQuotes-Demo",
        "profit": 75.68,
        "profit_loss": 75.68,  # Added for compatibility
        "open_positions": 3,
        "pending_orders": 2,
        "total_profit": 1250.50,  # Added for performance command
    }


def get_mock_system_info() -> Dict[str, Any]:
    """Get mock system information.
    
    Returns:
        Dict: Mock system information.
    """
    return {
        "cpu_usage": random.uniform(10, 50),
        "memory_usage": random.uniform(20, 70),
        "disk_usage": random.uniform(30, 80),
        "uptime": str(timedelta(hours=random.randint(24, 720))),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "processes": random.randint(5, 15),
    }


def get_recent_signals() -> List[Dict[str, Any]]:
    """Get recent signals data.
    
    Returns:
        List[Dict]: Recent signals data.
    """
    return get_mock_signals()


def get_trading_journal() -> List[Dict[str, Any]]:
    """Get trading journal data.
    
    Returns:
        List[Dict]: Trading journal data.
    """
    return [
        {
            "symbol": "EURUSD",
            "type": "BUY",
            "volume": 0.1,
            "price_open": 1.08743,
            "price_close": 1.08921,
            "profit": 17.8,
            "profit_pct": 0.16,
            "duration": "3h 15m",
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "symbol": "GBPUSD",
            "type": "SELL",
            "volume": 0.15,
            "price_open": 1.27432,
            "price_close": 1.27321,
            "profit": 16.65,
            "profit_pct": 0.09,
            "duration": "2h 30m",
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "symbol": "USDJPY",
            "type": "BUY",
            "volume": 0.2,
            "price_open": 149.213,
            "price_close": 148.932,
            "profit": -37.4,
            "profit_pct": -0.19,
            "duration": "4h 45m",
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
        }
    ]


def get_market_analysis() -> Dict[str, Any]:
    """Get market analysis data.
    
    Returns:
        Dict: Market analysis data.
    """
    return {
        "market_sentiment": "Bullish",
        "volatility_index": 15.7,
        "trend_strength": 0.75,
        "key_assets": [
            {
                "symbol": "EURUSD",
                "price": 1.0892,
                "change": 0.15,
                "trend": "bullish",
                "support": 1.0850,
                "resistance": 1.0920
            },
            {
                "symbol": "GBPUSD",
                "price": 1.2735,
                "change": -0.08,
                "trend": "bearish",
                "support": 1.2700,
                "resistance": 1.2780
            },
            {
                "symbol": "USDJPY",
                "price": 148.95,
                "change": -0.12,
                "trend": "bearish",
                "support": 148.50,
                "resistance": 149.30
            }
        ],
        "market_events": [
            "Fed rate decision expected tomorrow",
            "ECB policy statement released yesterday"
        ]
    }


def get_all_mock_data() -> Dict[str, Any]:
    """Get all mock data.
    
    Returns:
        Dict: All mock data.
    """
    return {
        "system_status": get_mock_system_status(),
        "positions": get_mock_positions(),
        "orders": get_mock_orders(),
        "signals": get_mock_signals(),
        "risk_metrics": get_mock_risk_metrics(),
        "performance": get_mock_performance(),
        "account_info": get_mock_account_info(),
        "system_info": get_mock_system_info(),
        "trading_journal": get_trading_journal(),
        "market_analysis": get_market_analysis(),
    }