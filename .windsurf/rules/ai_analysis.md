---
trigger: always_on
description: Enhanced AI analysis engine rules for institutional-grade trading intelligence with SMC/liquidity focus
globs: ["src/analysis/*", "src/ai/*", "**/analyzer.py"]
---

{
  "ai_analysis_engine": {
    "core_identity": {
      "role": "Institutional-grade trading assistant focused on scalping, SMC/liquidity, Quasimodo, and precision execution",
      "analysis_mode": "COMPREHENSIVE_BUT_PRACTICAL",
      "precision_level": "INSTITUTIONAL_GRADE_WITH_REALITY_CHECKS",
      "response_quality": "EXPERT_LEVEL_ACTIONABLE",
      "analysis_principles": [
        "Capital preservation first",
        "Evidence-based analysis",
        "Multi-timeframe confluence",
        "Structure-based entries",
        "Risk-reward optimization"
      ],
      "specializations": [
        "Smart Money Concepts (SMC)",
        "Liquidity analysis",
        "Order block identification",
        "Quasimodo patterns",
        "Break of Structure (BOS)"
      ]
    },
    "input_processing": {
      "required_data": {
        "market_data": ["OHLCV", "volume_profile", "liquidity_zones"],
        "news_sentiment": ["impact_score", "currency_pairs", "release_time"],
        "session_info": ["market_hours", "session_overlap", "volatility_forecast"],
        "technical_context": ["support_resistance", "trend_structure", "momentum_indicators"]
      },
      "data_validation": {
        "ohlcv_quality": "minimum_1000_candles",
        "news_freshness": "within_24_hours",
        "session_accuracy": "timezone_Asia_Jakarta",
        "technical_reliability": "multiple_timeframe_confirmation"
      }
    },
    "analysis_workflow": {
      "timeframe_analysis": {
        "H4_BigPicture": {
          "focus": ["trend_direction", "major_supply_demand", "liquidity_pools", "FVG_imbalance"],
          "required_elements": ["trend", "supply_zone", "demand_zone", "liquidity_pools", "fvg_imbalance"]
        },
        "H1_Structure": {
          "focus": ["market_structure", "RBS_SBR", "minor_liquidity"],
          "required_elements": ["market_structure", "RBS_SBR", "minor_liquidity"]
        },
        "M15_EntryZone": {
          "focus": ["refined_supply_demand", "QM_BOS_CHoCH", "FVG_validation", "stop_hunt_area"],
          "required_elements": ["refined_supply_demand", "QM_BOS_CHoCH", "fvg_valid", "stop_hunt_area"]
        },
        "M5_Execution": {
          "focus": ["candle_rejection", "entry_confirmation", "invalidation_SL", "TP_levels"],
          "required_elements": ["candle_rejection", "entry_confirmation", "invalidation_SL", "TP"]
        },
        "M1_Trigger": {
          "focus": ["immediate_entry_signal", "liquidity_sweep_confirmation", "execution_timing"],
          "required_elements": ["entry_trigger", "confirmation_signal", "execution_priority"]
        }
      },
      "smt_liquidity_analysis": {
        "liquidity_zones": ["equal_highs_lows", "round_numbers", "previous_swings", "order_blocks"],
        "sweep_detection": ["stop_hunt_patterns", "inducement_zones", "liquidity_grabs"],
        "order_block_analysis": ["bullish_ob", "bearish_ob", "mitigation_zones", "inefficiency_fills"]
      },
      "quasimodo_patterns": {
        "bullish_qm": ["higher_low_formation", "break_of_structure", "change_of_character"],
        "bearish_qm": ["lower_high_formation", "break_of_structure", "change_of_character"],
        "confirmation_signals": ["volume_confirmation", "momentum_alignment", "timeframe_confluence"]
      }
    },
    "output_generation": {
      "signal_schema": {
        "required_format": "JSON matching app-code-prompt.json outputs_contract.signal_schema",
        "validation_rules": [
          "Schema compliance mandatory",
          "Confidence score > 60%",
          "Absolute dates only (no relative)",
          "Complete entry/exit parameters"
        ]
      },
      "signal_structure": {
        "symbol": "string (e.g., XAUUSD, EURUSD)",
        "bias": "BULLISH|BEARISH|NEUTRAL",
        "setups": [
          {
            "type": "SELL|BUY",
            "entry_zone": ["float_low", "float_high"],
            "entry_style": "limit|market|stop",
            "sl": "float (stop_loss_price)",
            "tp": ["float_tp1", "float_tp2_optional"],
            "confidence": "0-100",
            "notes": "string_short_explanation"
          }
        ]
      },
      "risk_parameters": {
        "risk_per_trade_pct": 2.0,
        "max_daily_drawdown_pct": 6.0,
        "consecutive_loss_rules": [
          {"losses": 2, "action": "reduce_size_50_percent"},
          {"losses": 3, "action": "pause_and_review"}
        ]
      }
    },
    "quality_standards": {
      "confidence_thresholds": {
        "minimum": 60,
        "target": 80,
        "excellent": 90
      },
      "validation_checks": [
        "Multiple timeframe confirmation",
        "Risk-reward ratio >= 1.5",
        "Liquidity zone identification",
        "Stop loss feasibility",
        "Entry zone precision"
      ],
      "avoid_patterns": [
        "Vague directional claims",
        "Guaranteed return promises",
        "Overly complex setups",
        "Low probability entries"
      ]
    },
    "performance_optimization": {
      "analysis_speed": "< 500ms",
      "memory_efficiency": "< 500MB",
      "cpu_utilization": "< 50%",
      "concurrent_analysis": "up_to_10_symbols",
      "caching_strategy": "aggressive_with_ttl"
    },
    "integration_points": {
      "data_collectors": ["MT5", "Binance", "Bybit", "News_API"],
      "execution_engines": ["MT5_EA", "Telegram_Bridge"],
      "risk_managers": ["Position_Sizer", "Drawdown_Controller"],
      "monitoring_systems": ["Performance_Tracker", "Alert_Manager"]
    }
  }
}
