---
trigger: always_on
description: Enhanced security system rules for comprehensive trading system protection, including API security, authentication, encryption, and audit trails
globs: ["src/security/*", "src/auth/*", "**/security.py", "**/auth.py"]
---

{
  "security_system": {
    "api_security": {
      "key_management": {
        "storage": {
          "primary": "HashiCorp Vault",
          "fallback": "encrypted environment variables"
        },
        "rotation": {
          "frequency": "90 days",
          "emergency": "on_compromise_detection"
        },
        "access_control": {
          "principle": "least_privilege",
          "rotation_access": "security_admin_only"
        }
      },
      "rate_limiting": {
        "global": {
          "rate": "1000/minute",
          "burst": 50
        },
        "per_user": {
          "rate": "100/minute",
          "burst": 10
        },
        "per_ip": {
          "rate": "200/minute",
          "burst": 20
        }
      }
    },
    "authentication": {
      "methods": {
        "jwt": {
          "algorithm": "RS256",
          "expiry": "1h",
          "refresh": "7d"
        },
        "api_key": {
          "format": "UUID-v4",
          "expiry": "90d"
        },
        "oauth2": {
          "providers": ["google", "github"],
          "scope": "minimal_required_only"
        }
      },
      "mfa": {
        "required_for": ["admin", "trader"],
        "methods": ["TOTP", "backup_codes"],
        "grace_period": "1h"
      }
    },
    "encryption": {
      "data_at_rest": {
        "algorithm": "AES-256-GCM",
        "key_rotation": "yearly",
        "scope": ["user_data", "trade_secrets"]
      },
      "data_in_transit": {
        "protocol": "TLS_1.3",
        "minimum_strength": "128_bit",
        "perfect_forward_secrecy": true
      }
    },
    "audit_system": {
      "logging": {
        "events": {
          "authentication": {
            "success": "info",
            "failure": "warning"
          },
          "authorization": {
            "success": "info",
            "failure": "warning"
          },
          "data_access": {
            "read": "info",
            "write": "info",
            "delete": "warning"
          }
        },
        "retention": {
          "auth_logs": "1 year",
          "access_logs": "2 years",
          "security_events": "5 years"
        }
      },
      "alerts": {
        "critical": {
          "events": [
            "multiple_auth_failures",
            "unusual_access_patterns",
            "configuration_changes"
          ],
          "notification": ["security_team", "admin"]
        },
        "high": {
          "events": [
            "new_ip_access",
            "off_hours_login",
            "elevated_privilege_use"
          ],
          "notification": ["security_team"]
        }
      }
    },
    "compliance": {
      "data_protection": {
        "pii": {
          "encryption": "required",
          "masking": "display_last_4_only",
          "access_log": "all_queries"
        },
        "trading_data": {
          "encryption": "required",
          "backup": "daily",
          "retention": "7 years"
        }
      },
      "access_control": {
        "rbac": {
          "roles": ["admin", "trader", "viewer"],
          "permissions": "explicit_grant_only",
          "review": "quarterly"
        },
        "session": {
          "timeout": "12h",
          "concurrent": "max_2",
          "ip_binding": true
        }
      }
    }
  }
}
