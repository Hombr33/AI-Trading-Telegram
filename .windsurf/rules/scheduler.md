---
trigger: always_on
description: Enhanced scheduler system rules for automated trading cycles, session management, and task orchestration
globs: ["src/scheduler/*", "src/automation/*", "**/scheduler.py", "**/automation.py"]
---

{
  "scheduler_system": {
    "analysis_cycles": {
      "market_analysis": {
        "frequency": "every_5_minutes",
        "active_sessions": ["London", "New_York", "Overlap"],
        "timeframes": ["H4", "H1", "M15", "M5", "M1"]
      },
      "position_check": {
        "frequency": "every_1_minute",
        "tasks": ["update_positions", "check_targets", "validate_risk"]
      },
      "system_health": {
        "frequency": "every_15_minutes",
        "checks": ["api_connectivity", "mt5_connection", "memory_usage"]
      }
    },
    "session_management": {
      "trading_sessions": {
        "London": {
          "start": "07:00 UTC",
          "end": "16:00 UTC",
          "risk_profile": "normal"
        },
        "New_York": {
          "start": "12:00 UTC",
          "end": "21:00 UTC",
          "risk_profile": "normal"
        },
        "Asian": {
          "start": "23:00 UTC",
          "end": "08:00 UTC",
          "risk_profile": "reduced"
        }
      },
      "session_filters": {
        "avoid_high_impact_news": {
          "before_minutes": 30,
          "after_minutes": 30,
          "action": "close_positions"
        },
        "prefer_london_ny_overlap": {
          "start": "12:00 UTC",
          "end": "16:00 UTC",
          "risk_profile": "aggressive"
        }
      }
    },
    "task_orchestration": {
      "priority_levels": {
        "critical": {
          "max_delay_ms": 100,
          "retry_attempts": 3
        },
        "high": {
          "max_delay_ms": 500,
          "retry_attempts": 2
        },
        "normal": {
          "max_delay_ms": 1000,
          "retry_attempts": 1
        }
      },
      "error_handling": {
        "retry_strategy": "exponential_backoff",
        "max_retries": 3,
        "alert_threshold": "3_failures"
      }
    }
  }
}
