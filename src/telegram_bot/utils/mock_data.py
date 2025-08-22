"""Mock data utilities for Telegram bot."""

from typing import Dict, List, Any
from datetime import datetime, timezone, timedelta
import random


def get_mock_system_status() -> Dict[str, Any]:
    """Get mock system status data.
    
    Returns:
        Dict: Mock system status data.
    """
    return {
        "bot_status": "Online",
        "mt5_connection": "Connected",
        "ai_analyzer": "Active",
        "risk_manager": "Active",
        "last_update": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
    }


def get_mock_positions() -> List[Dict[str, Any]]:
    """Get mock positions data.
    
    Returns:
        List[Dict]: Mock positions data.
    """
    return [
        {
            "symbol": "EURUSD",
            "type": "BUY",
            "volume": 0.1,
            "price_open": 1.08743,
            "price_current": 1.08921,
            "profit": 17.8,
            "time": (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
        },
        {
            "symbol": "GBPUSD",
            "type": "SELL",
            "volume": 0.15,
            "price_open": 1.27432,
            "price_current": 1.27321,
            "profit": 16.65,
            "time": (datetime.now(timezone.utc) - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
        },
        {
            "symbol": "USDJPY",
            "type": "BUY",
            "volume": 0.2,
            "price_open": 149.213,
            "price_current": 148.932,
            "profit": -37.4,
            "time": (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
        },
    ]


def get_mock_orders() -> List[Dict[str, Any]]:
    """Get mock orders data.
    
    Returns:
        List[Dict]: Mock orders data.
    """
    return [
        {
            "symbol": "XAUUSD",
            "type": "BUY_LIMIT",
            "volume": 0.05,
            "price": 1932.45,
            "time": (datetime.now(timezone.utc) - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
        },
        {
            "symbol": "EURUSD",
            "type": "SELL_STOP",
            "volume": 0.1,
            "price": 1.08213,
            "time": (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
        },
    ]


def get_mock_signals() -> List[Dict[str, Any]]:
    """Get mock signals data.
    
    Returns:
        List[Dict]: Mock signals data.
    """
    return [
        {
            "symbol": "EURUSD",
            "direction": "BUY",
            "strength": 0.85,
            "entry_price": 1.08650,
            "target_price": 1.09100,
            "stop_loss": 1.08400,
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
        },
        {
            "symbol": "GBPJPY",
            "direction": "SELL",
            "strength": 0.72,
            "entry_price": 190.450,
            "target_price": 189.800,
            "stop_loss": 190.800,
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
        },
    ]


def get_mock_risk_metrics() -> Dict[str, Any]:
    """Get mock risk metrics data.
    
    Returns:
        Dict: Mock risk metrics data.
    """
    return {
        "margin_used_pct": 32.5,
        "daily_drawdown": 1.8,
        "exposure_level": 45.2,
        "open_positions": 3,
        "total_position_value": 12450.75,
        "max_drawdown": 5.2,
        "current_drawdown": 1.8,
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
    }