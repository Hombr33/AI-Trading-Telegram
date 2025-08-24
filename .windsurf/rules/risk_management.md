---
trigger: always_on
description: Enhanced risk management system rules for AI trading bot with advanced position sizing, drawdown controls, and risk monitoring
globs: ["src/risk/*", "src/management/*", "**/risk_*.py", "**/manager.py"]
---

{
  "risk_management_system": {
    "core_principles": {
      "capital_preservation": {
        "primary_objective": true,
        "risk_hierarchy": [
          "Preserve capital",
          "Manage drawdown",
          "Optimize returns",
          "Scale positions"
        ],
        "protection_mechanisms": [
          "Stop-loss enforcement",
          "Position sizing limits",
          "Drawdown controls",
          "Correlation management"
        ]
      },
      "risk_limits": {
        "per_trade": {
          "max_percentage": 2.0,
          "max_amount_usd": 25.0,
          "scaling_rules": {
            "account_size_breaks": [300, 500, 1000],
            "risk_percentages": [2.0, 1.5, 1.0]
          }
        },
        "daily": {
          "max_drawdown_pct": 6.0,
          "warning_threshold_pct": 4.0,
          "max_trades": 50,
          "cooldown_minutes": 60
        },
        "correlation": {
          "max_correlation": 0.70,
          "position_limits": {
            "high_correlation": 2,
            "medium_correlation": 4,
            "low_correlation": 8
          }
        }
      },
      "market_conditions": {
        "volatility_adjustment": {
          "high_volatility": "reduce_position_size_50_percent",
          "extreme_volatility": "no_new_positions"
        },
        "liquidity_controls": {
          "low_liquidity": "reduce_position_size",
          "spreads_threshold": "max_5_points"
        },
        "session_rules": {
          "asian": "reduced_risk_50_percent",
          "london": "normal_risk",
          "new_york": "normal_risk",
          "session_overlap": "increased_monitoring"
        }
      }
    },
    "position_sizing": {
      "calculation_method": "risk_percent_of_equity_based_on_SL_distance",
      "formula": "position_size = (equity * risk_percent) / (stop_loss_distance * point_value)",
      "risk_parameters": {
        "risk_per_trade_pct": 2.0,
        "max_risk_per_trade_usd": 25,
        "min_position_size": 0.01,
        "max_position_size": 10.0,
        "position_size_rounding": "down_to_nearest_0.01"
      },
      "stop_loss_validation": {
        "minimum_distance": "10_points",
        "maximum_distance": "500_points",
        "atr_based_validation": "stop_loss_should_be_1_to_3_atr",
        "support_resistance_validation": "stop_loss_should_be_beyond_key_levels"
      },
      "dynamic_adjustment": {
        "equity_based_scaling": "position_size_scales_with_equity_growth",
        "volatility_adjustment": "reduce_size_in_high_volatility",
        "correlation_adjustment": "reduce_size_for_correlated_positions",
        "session_adjustment": "reduce_size_during_news_events"
      }
    },
    "daily_risk_limits": {
      "drawdown_controls": {
        "warning_level": "3_percent_drawdown",
        "reduction_level": "4_percent_drawdown",
        "pause_level": "5_percent_drawdown",
        "emergency_stop": "6_percent_drawdown"
      },
      "trade_limits": {
        "max_daily_trades": 50,
        "max_daily_loss_usd": 25,
        "target_daily_profit_usd": 50,
        "profit_taking_levels": ["25_usd", "40_usd", "50_usd"]
      },
      "session_management": {
        "london_session": "normal_risk_parameters",
        "new_york_session": "normal_risk_parameters",
        "asian_session": "reduced_risk_parameters",
        "news_events": "minimal_risk_parameters"
      }
    },
    "consecutive_loss_management": {
      "progressive_reduction": [
        {
          "losses": 2,
          "action": "reduce_size_50_percent",
          "pause_minutes": 30,
          "risk_per_trade_pct": 1.0
        },
        {
          "losses": 3,
          "action": "pause_and_review",
          "pause_minutes": 120,
          "risk_per_trade_pct": 0.5
        },
        {
          "losses": 4,
          "action": "emergency_stop",
          "pause_minutes": 1440,
          "risk_per_trade_pct": 0.0
        }
      ],
      "recovery_conditions": {
        "winning_trade": "reset_consecutive_loss_count",
        "profit_target": "achieve_25_usd_daily_profit",
        "time_based": "24_hours_without_trading",
        "manual_reset": "admin_override_required"
      }
    },
    "correlation_risk_management": {
      "correlation_thresholds": {
        "high_correlation": "above_70_percent",
        "medium_correlation": "40_to_70_percent",
        "low_correlation": "below_40_percent"
      },
      "position_limits": {
        "high_correlation": "maximum_2_positions",
        "medium_correlation": "maximum_4_positions",
        "low_correlation": "maximum_8_positions"
      },
      "correlation_calculation": {
        "timeframe": "rolling_20_period_correlation",
        "update_frequency": "every_5_minutes",
        "correlation_pairs": ["EURUSD_GBPUSD", "XAUUSD_USDJPY", "USDCAD_USDJPY"],
        "dynamic_adjustment": "real_time_correlation_monitoring"
      }
    },
    "volatility_risk_management": {
      "volatility_measurement": {
        "atr_calculation": "14_period_average_true_range",
        "volatility_thresholds": ["low", "normal", "high", "extreme"],
        "update_frequency": "every_candle_close",
        "multi_timeframe": ["M15", "H1", "H4"]
      },
      "volatility_adjustments": {
        "low_volatility": "normal_position_size",
        "normal_volatility": "normal_position_size",
        "high_volatility": "reduce_position_size_25_percent",
        "extreme_volatility": "reduce_position_size_50_percent"
      },
      "volatility_filters": {
        "news_events": "avoid_trading_during_high_impact_news",
        "economic_releases": "reduce_risk_30_minutes_before_after",
        "central_bank_events": "minimal_risk_during_announcements",
        "market_holidays": "reduced_risk_during_low_liquidity"
      }
    },
    "liquidity_risk_management": {
      "liquidity_assessment": {
        "bid_ask_spread": "maximum_5_pip_spread",
        "market_depth": "minimum_100_lot_depth",
        "volume_profile": "adequate_volume_for_position_size",
        "session_liquidity": "prefer_london_ny_overlap"
      },
      "liquidity_filters": {
        "thin_markets": "avoid_trading_during_low_liquidity",
        "gap_risk": "avoid_trading_before_major_news",
        "slippage_risk": "maximum_10_point_slippage_tolerance",
        "execution_risk": "prefer_limit_orders_over_market"
      }
    },
    "emergency_risk_controls": {
      "circuit_breakers": {
        "connection_loss": "immediate_pause_trading",
        "excessive_errors": "pause_trading_after_5_errors",
        "risk_limit_breach": "immediate_close_all_positions",
        "system_failure": "emergency_stop_all_operations"
      },
      "emergency_procedures": {
        "position_closing": "close_all_positions_immediately",
        "order_cancellation": "cancel_all_pending_orders",
        "system_shutdown": "graceful_shutdown_with_notification",
        "manual_override": "admin_emergency_controls"
      }
    },
    "risk_monitoring": {
      "real_time_metrics": {
        "current_drawdown": "real_time_calculation",
        "open_risk": "sum_of_all_position_risk",
        "correlation_exposure": "current_correlation_matrix",
        "volatility_exposure": "current_volatility_levels"
      },
      "risk_alerts": {
        "drawdown_warnings": "at_3_percent_4_percent_5_percent",
        "correlation_alerts": "when_correlation_exceeds_70_percent",
        "volatility_alerts": "when_volatility_exceeds_normal_range",
        "position_alerts": "when_approaching_position_limits"
      },
      "risk_reporting": {
        "daily_risk_report": "end_of_day_summary",
        "weekly_risk_analysis": "trend_analysis_and_recommendations",
        "monthly_risk_review": "comprehensive_risk_assessment",
        "ad_hoc_reports": "on_demand_risk_analysis"
      }
    },
    "performance_metrics": {
      "risk_adjusted_returns": {
        "sharpe_ratio": "target_above_1.0",
        "sortino_ratio": "target_above_1.5",
        "calmar_ratio": "target_above_2.0",
        "max_drawdown": "target_below_5_percent"
      },
      "risk_efficiency": {
        "risk_per_trade": "average_risk_per_trade",
        "risk_reward_ratio": "average_risk_reward_ratio",
        "win_rate": "percentage_of_winning_trades",
        "profit_factor": "gross_profit_gross_loss_ratio"
      }
    },
    "compliance_and_audit": {
      "risk_logging": {
        "all_risk_decisions": "log_every_risk_decision",
        "position_sizing_calculations": "log_all_calculations",
        "limit_breaches": "log_all_limit_violations",
        "emergency_actions": "log_all_emergency_procedures"
      },
      "audit_trail": {
        "risk_parameter_changes": "log_all_parameter_modifications",
        "override_actions": "log_all_manual_overrides",
        "system_decisions": "log_all_automated_decisions",
        "compliance_checks": "log_all_compliance_validations"
      }
    }
  }
}
