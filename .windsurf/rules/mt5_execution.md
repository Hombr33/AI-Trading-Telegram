---
trigger: always_on
description: Enhanced MT5 execution engine rules for automated trading with advanced order management and risk controls
globs: ["src/execution/*", "src/mt5/*", "**/mt5_*.py", "**/executor.py"]
---

{
  "mt5_execution_engine": {
    "connection_management": {
      "connection_settings": {
        "login": "from_environment_variable",
        "password": "from_environment_variable",
        "server": "from_environment_variable",
        "timeout": 30000,
        "retry_attempts": 3,
        "retry_delay_ms": 1000
      },
      "heartbeat_monitoring": {
        "enabled": true,
        "interval_seconds": 60,
        "failure_threshold": 3,
        "auto_reconnect": true,
        "reconnection_strategy": "exponential_backoff"
      },
      "error_handling": {
        "connection_lost": "immediate_reconnect_attempt",
        "authentication_failed": "log_and_alert",
        "server_unavailable": "retry_with_backoff",
        "timeout_error": "retry_with_increased_timeout"
      }
    },
    "order_management": {
      "order_types": {
        "market": {
          "execution": "immediate",
          "slippage_tolerance": 10,
          "use_for": ["emergency_entries", "high_priority_signals"]
        },
        "limit": {
          "execution": "pending",
          "expiration": "GTC",
          "use_for": ["normal_entries", "partial_exits"]
        },
        "stop": {
          "execution": "pending",
          "expiration": "GTC",
          "use_for": ["stop_loss", "trailing_stops"]
        }
      },
      "order_parameters": {
        "magic_number": 1001,
        "comment_format": "AI_SIGNAL_{timestamp}_{symbol}_{bias}",
        "deviation": 10,
        "type_filling": "FOK",
        "type_time": "GTC"
      },
      "position_tracking": {
        "real_time_updates": true,
        "position_history": "90_days",
        "modification_logging": true,
        "partial_close_tracking": true
      }
    },
    "risk_management": {
      "position_sizing": {
        "method": "risk_percent_of_equity_based_on_SL_distance",
        "risk_per_trade_pct": 2.0,
        "max_risk_per_trade_usd": 25,
        "min_position_size": 0.01,
        "max_position_size": 10.0
      },
      "daily_limits": {
        "max_daily_trades": 50,
        "max_daily_drawdown_pct": 6.0,
        "max_daily_loss_usd": 25,
        "target_daily_profit_usd": 50
      },
      "consecutive_loss_management": [
        {"losses": 2, "action": "reduce_size_50_percent", "pause_minutes": 30},
        {"losses": 3, "action": "pause_and_review", "pause_minutes": 120},
        {"losses": 4, "action": "emergency_stop", "pause_minutes": 1440}
      ],
      "circuit_breakers": {
        "max_open_positions": 10,
        "max_correlation_exposure": 0.7,
        "max_sector_exposure": 0.3,
        "emergency_stop_conditions": ["connection_lost", "excessive_errors", "risk_limit_breach"]
      }
    },
    "trade_execution": {
      "entry_execution": {
        "signal_validation": ["schema_check", "confidence_threshold", "risk_validation"],
        "entry_timing": ["market_hours_check", "news_impact_check", "volatility_check"],
        "entry_method": ["limit_preferred", "market_if_urgent", "stop_if_breakout"]
      },
      "exit_management": {
        "stop_loss": {
          "never_widen": true,
          "modification_allowed": "only_tighten",
          "emergency_stop": true
        },
        "take_profit": {
          "partial_tp1": {"close_pct": 0.5, "rr_ratio": 1.5},
          "partial_tp2": {"close_pct": 0.5, "rr_ratio": 3.0},
          "breakeven_move": {"trigger_at_rr": 1.0, "new_sl": "entry_price"}
        },
        "trailing_stop": {
          "enabled": true,
          "start_points": 250,
          "stop_points": 200,
          "step_points": 50,
          "activation_condition": "after_tp1"
        }
      }
    },
    "performance_monitoring": {
      "execution_metrics": {
        "fill_rate": "target > 95%",
        "slippage_average": "target < 5 points",
        "execution_latency": "target < 100ms",
        "order_modification_success": "target > 98%"
      },
      "risk_metrics": {
        "position_correlation": "monitor < 0.7",
        "exposure_concentration": "monitor < 30%",
        "drawdown_tracking": "real_time",
        "risk_adjusted_returns": "calculate_sharpe_ratio"
      },
      "system_health": {
        "connection_stability": "uptime > 99.5%",
        "error_rate": "target < 1%",
        "memory_usage": "target < 1GB",
        "cpu_usage": "target < 50%"
      }
    },
    "integration_requirements": {
      "data_sources": ["MT5_quotes", "MT5_ticks", "MT5_news"],
      "external_systems": ["AI_Analyzer", "Risk_Manager", "Telegram_Bridge"],
      "notification_channels": ["email", "telegram", "webhook"],
      "logging_systems": ["structured_logs", "performance_metrics", "audit_trail"]
    },
    "compliance_and_audit": {
      "trade_logging": {
        "all_orders": true,
        "all_modifications": true,
        "all_executions": true,
        "retention_period": "7_years"
      },
      "audit_trail": {
        "user_actions": true,
        "system_decisions": true,
        "risk_checks": true,
        "compliance_validation": true
      },
      "reporting": {
        "daily_summary": true,
        "risk_report": true,
        "performance_analysis": true,
        "compliance_check": true
      }
    }
  }
}
