---
trigger: always_on
description: Enhanced Telegram bridge system rules for AI trading signal distribution, user interaction, and bot management
globs: ["src/telegram/*", "src/bridge/*", "**/telegram_*.py", "**/bridge.py"]
---

{
  "telegram_bridge_system": {
    "core_functionality": {
      "signal_distribution": {
        "ai_signals": "real_time_distribution",
        "trade_updates": "position_status_updates",
        "performance_reports": "daily_summary_reports",
        "risk_alerts": "drawdown_warnings"
      },
      "user_interaction": {
        "command_handling": ["start", "status", "trades", "performance", "settings"],
        "query_processing": "natural_language_queries",
        "notification_preferences": "customizable_alerts",
        "access_control": "role_based_permissions"
      },
      "bot_management": {
        "start_stop_control": "remote_bot_management",
        "configuration_updates": "dynamic_settings_modification",
        "emergency_controls": "pause_trading_emergency_stop",
        "maintenance_mode": "scheduled_maintenance_windows"
      }
    },
    "signal_processing": {
      "input_validation": {
        "schema_compliance": "app-code-prompt.json signal_schema",
        "confidence_threshold": "minimum_60_percent",
        "risk_validation": "position_sizing_check",
        "market_validation": "session_hours_check"
      },
      "signal_normalization": {
        "format_standardization": "unified_json_structure",
        "deduplication": "by_symbol_bias_entry_zone",
        "ttl_management": "90_minute_expiry",
        "priority_scoring": "confidence_based_ranking"
      },
      "output_formatting": {
        "human_readable": "formatted_message_with_emoji",
        "machine_readable": "json_payload_for_execution",
        "multi_language": "id-ID_primary_english_fallback",
        "rich_media": "charts_images_attachments"
      }
    },
    "message_structure": {
      "signal_messages": {
        "header": "🚨 AI TRADING SIGNAL 🚨",
        "symbol_info": "Symbol: {symbol} | Bias: {bias}",
        "entry_details": "Entry Zone: {entry_low} - {entry_high}",
        "risk_management": "SL: {stop_loss} | TP1: {tp1} | TP2: {tp2}",
        "confidence": "Confidence: {confidence}%",
        "notes": "Notes: {analysis_notes}",
        "footer": "Generated at {timestamp} | Risk: {risk_percent}%"
      },
      "trade_updates": {
        "entry_confirmation": "✅ Entry executed at {price}",
        "partial_exit": "💰 Partial TP1 hit at {price}",
        "stop_loss": "🛑 Stop loss hit at {price}",
        "full_exit": "🎯 Full exit at {price} | P&L: {pnl}"
      },
      "performance_reports": {
        "daily_summary": "📊 Daily Performance Report",
        "trades_count": "Total Trades: {count}",
        "win_rate": "Win Rate: {win_rate}%",
        "profit_loss": "P&L: {pnl} | Drawdown: {dd}%",
        "best_trade": "Best Trade: {symbol} +{pnl}",
        "worst_trade": "Worst Trade: {symbol} {pnl}"
      }
    },
    "user_management": {
      "authentication": {
        "bot_token": "from_environment_variable",
        "user_verification": "telegram_user_id_whitelist",
        "access_levels": ["admin", "trader", "viewer"],
        "session_management": "token_based_authentication"
      },
      "permissions": {
        "admin": ["full_control", "bot_management", "user_management", "configuration"],
        "trader": ["view_signals", "execute_trades", "view_performance", "modify_settings"],
        "viewer": ["view_signals", "view_performance", "basic_queries"]
      },
      "user_preferences": {
        "notification_settings": ["all_signals", "high_confidence_only", "trade_updates_only"],
        "language_preference": ["id-ID", "en-US"],
        "timezone": "Asia/Jakarta",
        "risk_tolerance": ["conservative", "moderate", "aggressive"]
      }
    },
    "command_handling": {
      "start_command": {
        "response": "Welcome to AI Trading Bot! Use /help for available commands.",
        "user_registration": "automatic_on_first_use",
        "default_settings": "conservative_risk_profile"
      },
      "status_command": {
        "bot_status": "running/stopped/maintenance",
        "connection_status": "MT5_connected/disconnected",
        "active_positions": "count_and_summary",
        "daily_performance": "current_pnl_and_drawdown"
      },
      "trades_command": {
        "recent_trades": "last_10_trades",
        "open_positions": "current_positions",
        "trade_history": "filtered_by_date_symbol",
        "trade_details": "full_trade_analysis"
      },
      "performance_command": {
        "overall_stats": "total_trades_win_rate_pnl",
        "time_periods": ["daily", "weekly", "monthly", "yearly"],
        "symbol_breakdown": "performance_by_instrument",
        "risk_metrics": "sharpe_ratio_max_drawdown"
      },
      "settings_command": {
        "risk_parameters": "risk_per_trade_max_drawdown",
        "notification_preferences": "signal_types_update_frequency",
        "trading_hours": "session_filters_timezone",
        "emergency_controls": "pause_trading_emergency_stop"
      }
    },
    "notification_system": {
      "signal_notifications": {
        "immediate": "high_confidence_signals_confidence_80_plus",
        "delayed": "medium_confidence_signals_confidence_60_79",
        "batch": "low_confidence_signals_hourly_summary",
        "priority": "emergency_signals_instant_delivery"
      },
      "trade_notifications": {
        "entry": "immediate_on_execution",
        "modification": "stop_loss_take_profit_updates",
        "exit": "partial_full_exit_confirmations",
        "error": "execution_failures_immediate_alert"
      },
      "system_notifications": {
        "startup": "bot_initialization_status",
        "maintenance": "scheduled_maintenance_notices",
        "errors": "critical_error_alerts",
        "performance": "daily_weekly_reports"
      }
    },
    "integration_requirements": {
      "ai_analyzer": {
        "signal_reception": "webhook_or_polling",
        "format_validation": "json_schema_check",
        "priority_handling": "confidence_based_queuing",
        "feedback_loop": "execution_results_to_analyzer"
      },
      "execution_engine": {
        "signal_transmission": "real_time_delivery",
        "execution_confirmation": "status_updates",
        "error_handling": "execution_failure_notification",
        "performance_tracking": "trade_result_collection"
      },
      "risk_manager": {
        "risk_validation": "pre_execution_checks",
        "position_monitoring": "real_time_updates",
        "limit_enforcement": "risk_breach_alerts",
        "emergency_controls": "immediate_action_commands"
      }
    },
    "performance_optimization": {
      "message_throughput": {
        "target_messages_per_second": 100,
        "target_latency": "< 500ms",
        "target_memory_usage": "< 500MB",
        "target_cpu_usage": "< 30%"
      },
      "scalability": {
        "user_capacity": "up_to_1000_users",
        "concurrent_commands": "up_to_100_commands_per_second",
        "message_queue": "priority_based_queuing",
        "load_balancing": "multiple_bot_instances"
      },
      "reliability": {
        "uptime_target": "99.9%",
        "message_delivery": "guaranteed_delivery",
        "error_recovery": "automatic_recovery",
        "backup_systems": "failover_mechanisms"
      }
    },
    "security_and_compliance": {
      "data_protection": {
        "user_data_encryption": "end_to_end_encryption",
        "api_key_protection": "environment_variable_storage",
        "message_encryption": "telegram_encryption",
        "audit_logging": "all_actions_logged"
      },
      "access_control": {
        "user_authentication": "telegram_verified_identity",
        "command_authorization": "role_based_permissions",
        "rate_limiting": "command_throttling",
        "suspicious_activity": "automatic_detection"
      },
      "compliance": {
        "data_retention": "90_days_for_logs",
        "privacy_protection": "no_personal_data_storage",
        "audit_trail": "complete_action_history",
        "regulatory_compliance": "financial_regulations"
      }
    }
  }
}
