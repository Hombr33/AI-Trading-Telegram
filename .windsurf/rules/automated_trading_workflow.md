---
trigger: always_on
description: Advanced automated trading workflow rules for EA integration, OpenAI analysis, and trade management
globs:
---

{
  "automated_trading_workflow": {
    "core_workflow": {
      "screenshot_analysis_cycle": {
        "frequency": "every_5_minutes_during_active_sessions",
        "timeframes": ["H4", "H1", "M15", "M5", "M1"],
        "symbols": ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD"],
        "trigger_conditions": [
          "candle_close",
          "high_impact_news_30min_before",
          "session_overlap_start",
          "volatility_spike_detection"
        ]
      },
      "ai_analysis_pipeline": {
        "input": "EA_screenshot_with_market_context",
        "processing": "OpenAI_analysis_with_app_code_prompt",
        "output": "JSON_signal_with_execution_parameters",
        "validation": "schema_compliance_confidence_threshold_60"
      },
      "execution_flow": {
        "signal_reception": "validate_and_normalize",
        "risk_check": "position_sizing_correlation_validation",
        "execution": "MT4_MT5_order_placement",
        "management": "position_monitoring_modification",
        "journaling": "trade_logging_performance_tracking"
      }
    },
    "ea_integration": {
      "screenshot_capture": {
        "chart_settings": {
          "template": "SMC_Liquidity_Template",
          "indicators": ["ATR", "Volume_Profile", "Support_Resistance_Levels"],
          "timeframes": ["H4", "H1", "M15", "M5", "M1"],
          "chart_type": "candlestick_with_volume"
        },
        "capture_timing": {
          "scheduled": "every_5_minutes",
          "event_based": "candle_close_news_release_volatility_spike",
          "manual_trigger": "admin_override_emergency_analysis"
        },
        "image_quality": {
          "resolution": "1920x1080_minimum",
          "format": "PNG_with_compression",
          "naming": "symbol_timeframe_timestamp.png"
        }
      },
      "api_communication": {
        "endpoint": "POST /api/v1/market-analysis/screenshot",
        "payload": {
          "symbol": "string",
          "timeframe": "string",
          "timestamp": "ISO_8601",
          "image_data": "base64_encoded_screenshot",
          "market_context": {
            "current_price": "float",
            "session": "string",
            "volatility_level": "string",
            "news_impact": "string"
          }
        },
        "response_handling": {
          "success": "receive_signal_and_execute",
          "failure": "retry_with_exponential_backoff",
          "timeout": "skip_cycle_log_error"
        }
      },
      "signal_execution": {
        "signal_reception": "webhook_or_polling",
        "validation": "schema_check_confidence_threshold",
        "execution": "immediate_order_placement",
        "confirmation": "position_verification_logging"
      }
    },
    "openai_integration": {
      "prompt_engineering": {
        "base_prompt": "app-code-prompt.json",
        "context_enrichment": {
          "screenshot_analysis": "visual_pattern_recognition",
          "market_context": "session_volatility_news_impact",
          "historical_context": "recent_price_action_liquidity_zones"
        },
        "output_requirements": {
          "format": "JSON_signal_schema_compliance",
          "confidence": "minimum_60_percent",
          "validation": "entry_sl_tp_feasibility_check"
        }
      },
      "analysis_workflow": {
        "image_processing": "screenshot_to_market_analysis",
        "pattern_recognition": "SMC_liquidity_quasimodo_detection",
        "signal_generation": "entry_zone_sl_tp_calculation",
        "confidence_scoring": "multi_factor_analysis_validation"
      },
      "response_handling": {
        "success": "signal_forwarding_to_execution",
        "low_confidence": "log_and_skip_execution",
        "invalid_signal": "error_logging_and_retry",
        "timeout": "fallback_to_previous_analysis"
      }
    },
    "position_management": {
      "entry_execution": {
        "order_types": {
          "preferred": "limit_orders_for_better_fills",
          "fallback": "market_orders_for_urgent_entries",
          "breakout": "stop_orders_for_breakout_confirmation"
        },
        "position_sizing": "risk_percent_of_equity_based_on_SL_distance",
        "entry_timing": "immediate_on_signal_confirmation"
      },
      "active_management": {
        "stop_loss": {
          "never_widen": true,
          "modification": "only_tighten_based_on_structure",
          "breakeven": "move_to_entry_at_R1_achievement"
        },
        "take_profit": {
          "partial_tp1": {"close_pct": 0.5, "rr_ratio": 1.5},
          "partial_tp2": {"close_pct": 0.5, "rr_ratio": 3.0},
          "trailing_stop": {"enabled": true, "start_points": 250, "step_points": 50}
        },
        "correlation_management": "maximum_70_percent_correlation_exposure"
      },
      "exit_strategy": {
        "stop_loss": "immediate_execution_on_breach",
        "take_profit": "partial_exits_at_targets_full_exit_at_final",
        "time_based": "close_positions_before_session_end",
        "news_based": "reduce_exposure_during_high_impact_events"
      }
    },
    "trading_journal": {
      "entry_logging": {
        "timestamp": "ISO_8601_format",
        "signal_source": "OpenAI_analysis_id",
        "entry_parameters": "symbol_timeframe_entry_price_sl_tp",
        "market_context": "session_volatility_news_impact",
        "confidence_score": "AI_confidence_percentage"
      },
      "position_tracking": {
        "real_time_updates": "price_movement_pnl_calculation",
        "modification_log": "sl_tp_changes_reasoning",
        "exit_logging": "exit_price_pnl_realized_reason"
      },
      "performance_analysis": {
        "daily_summary": "trades_count_win_rate_pnl_drawdown",
        "weekly_analysis": "strategy_performance_risk_metrics",
        "monthly_review": "system_optimization_rule_adjustments"
      }
    },
    "telegram_integration": {
      "signal_distribution": {
        "immediate": "high_confidence_signals_80_plus",
        "delayed": "medium_confidence_signals_60_79",
        "batch": "low_confidence_signals_hourly_summary"
      },
      "position_updates": {
        "entry_confirmation": "position_opened_details",
        "modification_alerts": "sl_tp_changes",
        "exit_notifications": "position_closed_pnl_result",
        "risk_alerts": "drawdown_warnings_correlation_breaches"
      },
      "performance_reports": {
        "daily_summary": "end_of_day_performance",
        "weekly_analysis": "strategy_performance_review",
        "monthly_report": "system_optimization_recommendations"
      }
    },
    "system_monitoring": {
      "health_checks": {
        "ea_connection": "screenshot_capture_success_rate",
        "openai_api": "response_time_success_rate",
        "mt5_connection": "order_execution_success_rate",
        "database": "write_read_performance"
      },
      "performance_metrics": {
        "signal_generation": "time_from_screenshot_to_signal",
        "execution_latency": "time_from_signal_to_order",
        "system_uptime": "continuous_operation_percentage",
        "error_rates": "failed_operations_per_total"
      },
      "alerting": {
        "critical": "system_failure_connection_loss",
        "warning": "high_error_rate_performance_degradation",
        "info": "daily_summary_weekly_reports"
      }
    },
    "risk_management": {
      "position_limits": {
        "max_open_positions": 10,
        "max_risk_per_trade_pct": 2.0,
        "max_daily_drawdown_pct": 6.0,
        "max_daily_loss_usd": 25
      },
      "consecutive_loss_management": [
        {"losses": 2, "action": "reduce_size_50_percent", "pause_minutes": 30},
        {"losses": 3, "action": "pause_and_review", "pause_minutes": 120},
        {"losses": 4, "action": "emergency_stop", "pause_minutes": 1440}
      ],
      "session_filters": {
        "avoid_high_impact_news": "30_minutes_before_after",
        "prefer_london_ny_overlap": "highest_liquidity_periods",
        "reduce_risk_asian_session": "lower_volatility_periods"
      }
    }
  }
}