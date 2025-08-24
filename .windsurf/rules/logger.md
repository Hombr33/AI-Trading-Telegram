---
trigger: always_on
description: Enhanced logging system rules for comprehensive trading system monitoring, audit trails, and performance tracking
globs: ["src/logging/*", "src/monitoring/*", "**/logger.py", "**/monitor.py"]
---

{
  "logging_system": {
    "log_categories": {
      "trade_logs": {
        "levels": ["info", "warning", "error", "critical"],
        "fields": {
          "timestamp": "ISO8601",
          "trade_id": "UUID",
          "action": "entry|exit|modify",
          "details": "Dict[str, Any]",
          "user_id": "Optional[UUID]"
        },
        "retention": "90 days"
      },
      "system_logs": {
        "levels": ["debug", "info", "warning", "error", "critical"],
        "fields": {
          "timestamp": "ISO8601",
          "component": "str",
          "action": "str",
          "status": "success|failure",
          "details": "Dict[str, Any]"
        },
        "retention": "30 days"
      },
      "audit_logs": {
        "levels": ["info", "warning", "error"],
        "fields": {
          "timestamp": "ISO8601",
          "user_id": "UUID",
          "action": "str",
          "resource": "str",
          "changes": "Dict[str, Any]"
        },
        "retention": "365 days"
      },
      "ai_decision_logs": {
        "levels": ["info", "warning"],
        "fields": {
          "timestamp": "ISO8601",
          "analysis_id": "UUID",
          "confidence": "float",
          "decision": "Dict[str, Any]",
          "context": "Dict[str, Any]"
        },
        "retention": "180 days"
      }
    },
    "storage_configuration": {
      "primary_storage": {
        "type": "PostgreSQL",
        "connection_pool": 10,
        "batch_size": 100,
        "write_timeout": "1s"
      },
      "cache_layer": {
        "type": "Redis",
        "ttl": "24h",
        "max_size": "1GB"
      },
      "archive_storage": {
        "type": "S3",
        "bucket": "trading-logs-archive",
        "compression": "gzip"
      }
    },
    "monitoring_rules": {
      "performance_metrics": {
        "collection_interval": "1m",
        "aggregation_window": "5m",
        "retention_period": "90d"
      },
      "health_checks": {
        "check_interval": "1m",
        "timeout": "5s",
        "alert_threshold": "3_failures"
      },
      "alerts": {
        "error_rate": {
          "threshold": "1%",
          "window": "5m",
          "channels": ["telegram", "email"]
        },
        "latency": {
          "threshold": "100ms",
          "window": "1m",
          "channels": ["telegram"]
        }
      }
    },
    "compliance_rules": {
      "pii_handling": {
        "mask_sensitive_data": true,
        "excluded_fields": ["user_id", "email"],
        "encryption": "AES-256"
      },
      "audit_requirements": {
        "track_all_changes": true,
        "user_tracking": true,
        "immutable_logs": true
      },
      "retention_policy": {
        "trade_data": "7 years",
        "user_data": "5 years",
        "system_logs": "1 year"
      }
    }
  }
}
}
