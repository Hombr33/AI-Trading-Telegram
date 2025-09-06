"""
Configuration validation system for execution module.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass
from enum import Enum
import re

from .platform_compatibility import get_compatibility_manager
from ..core.logging import get_logger

logger = get_logger(__name__)


class ValidationLevel(Enum):
    """Configuration validation levels."""

    STRICT = "strict"  # All validations must pass
    MODERATE = "moderate"  # Critical validations must pass, warnings for others
    LENIENT = "lenient"  # Only basic validations, mostly warnings


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    platform: str

    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0


class ConfigurationValidator:
    """Validates execution platform configurations."""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        self.validation_level = validation_level
        self._compatibility_manager = get_compatibility_manager()
        self._platform_schemas = self._initialize_schemas()

    def _initialize_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Initialize validation schemas for different platforms."""
        return {
            "binance": {
                "required": ["api_key", "secret_key", "enabled"],
                "optional": ["sandbox", "testnet", "timeout", "max_retries"],
                "types": {
                    "api_key": str,
                    "secret_key": str,
                    "enabled": bool,
                    "sandbox": bool,
                    "testnet": bool,
                    "timeout": (int, float),
                    "max_retries": int,
                },
                "constraints": {
                    "api_key": {"min_length": 10, "pattern": r"^[A-Za-z0-9]+$"},
                    "secret_key": {"min_length": 10, "pattern": r"^[A-Za-z0-9]+$"},
                    "timeout": {"min": 1, "max": 300},
                    "max_retries": {"min": 1, "max": 10},
                },
            },
            "bybit": {
                "required": ["api_key", "secret_key", "enabled"],
                "optional": ["testnet", "timeout", "max_retries"],
                "types": {
                    "api_key": str,
                    "secret_key": str,
                    "enabled": bool,
                    "testnet": bool,
                    "timeout": (int, float),
                    "max_retries": int,
                },
                "constraints": {
                    "api_key": {"min_length": 10},
                    "secret_key": {"min_length": 10},
                    "timeout": {"min": 1, "max": 300},
                    "max_retries": {"min": 1, "max": 10},
                },
            },
            "bitget": {
                "required": ["api_key", "secret_key", "passphrase", "enabled"],
                "optional": ["sandbox", "timeout", "max_retries"],
                "types": {
                    "api_key": str,
                    "secret_key": str,
                    "passphrase": str,
                    "enabled": bool,
                    "sandbox": bool,
                    "timeout": (int, float),
                    "max_retries": int,
                },
                "constraints": {
                    "api_key": {"min_length": 10},
                    "secret_key": {"min_length": 10},
                    "passphrase": {"min_length": 1},
                    "timeout": {"min": 1, "max": 300},
                    "max_retries": {"min": 1, "max": 10},
                },
            },
            "mt5": {
                "required": ["enabled"],
                "optional": ["login", "password", "server", "timeout", "max_retries"],
                "types": {
                    "enabled": bool,
                    "login": int,
                    "password": str,
                    "server": str,
                    "timeout": (int, float),
                    "max_retries": int,
                },
                "constraints": {
                    "login": {"min": 1},
                    "password": {"min_length": 1},
                    "server": {"pattern": r"^[A-Za-z0-9.-]+$"},
                    "timeout": {"min": 1, "max": 300},
                    "max_retries": {"min": 1, "max": 10},
                },
                "platform_requirements": ["windows"],
            },
            "aiomql": {
                "required": ["enabled"],
                "optional": ["login", "password", "server", "timeout", "max_retries"],
                "types": {
                    "enabled": bool,
                    "login": int,
                    "password": str,
                    "server": str,
                    "timeout": (int, float),
                    "max_retries": int,
                },
                "constraints": {
                    "login": {"min": 1},
                    "password": {"min_length": 1},
                    "server": {"pattern": r"^[A-Za-z0-9.-]+$"},
                    "timeout": {"min": 1, "max": 300},
                    "max_retries": {"min": 1, "max": 10},
                },
                "platform_requirements": ["windows"],
            },
            "demo": {
                "required": ["enabled"],
                "optional": ["initial_balance", "latency_ms", "failure_rate"],
                "types": {
                    "enabled": bool,
                    "initial_balance": (int, float),
                    "latency_ms": (int, float),
                    "failure_rate": (int, float),
                },
                "constraints": {
                    "initial_balance": {"min": 1000, "max": 10000000},
                    "latency_ms": {"min": 0, "max": 5000},
                    "failure_rate": {"min": 0, "max": 1},
                },
            },
            "paper": {
                "required": ["enabled"],
                "optional": [
                    "initial_balance",
                    "trading_fees",
                    "slippage",
                    "use_live_data",
                ],
                "types": {
                    "enabled": bool,
                    "initial_balance": (int, float),
                    "trading_fees": (int, float),
                    "slippage": (int, float),
                    "use_live_data": bool,
                },
                "constraints": {
                    "initial_balance": {"min": 1000, "max": 10000000},
                    "trading_fees": {"min": 0, "max": 0.1},
                    "slippage": {"min": 0, "max": 0.01},
                },
            },
        }

    def validate_platform_config(
        self, platform: str, config: Dict[str, Any]
    ) -> ValidationResult:
        """Validate configuration for a specific platform."""
        errors = []
        warnings = []

        # Check if platform is supported
        if not self._compatibility_manager.is_platform_available(platform):
            unavailable_platforms = (
                self._compatibility_manager.get_unavailable_platforms()
            )
            reason = unavailable_platforms.get(platform, "Unknown platform")
            errors.append(f"Platform '{platform}' is not available: {reason}")

            # Suggest alternatives
            alternatives = self._compatibility_manager.get_cross_platform_alternatives(
                platform
            )
            if alternatives:
                warnings.append(
                    f"Consider using alternative platforms: {', '.join(alternatives)}"
                )

        # Get platform schema
        schema = self._platform_schemas.get(platform)
        if not schema:
            if self.validation_level == ValidationLevel.STRICT:
                errors.append(f"No validation schema found for platform '{platform}'")
            else:
                warnings.append(
                    f"No validation schema found for platform '{platform}' - using basic validation"
                )
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                platform=platform,
            )

        # Validate required fields
        for field in schema.get("required", []):
            if field not in config:
                errors.append(
                    f"Missing required field '{field}' for platform '{platform}'"
                )
            elif config[field] is None:
                errors.append(
                    f"Required field '{field}' cannot be None for platform '{platform}'"
                )

        # Validate field types and constraints
        all_fields = schema.get("required", []) + schema.get("optional", [])
        for field in all_fields:
            if field in config:
                self._validate_field(
                    platform, field, config[field], schema, errors, warnings
                )

        # Check for unknown fields
        known_fields = set(all_fields)
        config_fields = set(config.keys())
        unknown_fields = config_fields - known_fields

        if unknown_fields:
            if self.validation_level == ValidationLevel.STRICT:
                errors.extend(
                    [
                        f"Unknown field '{field}' for platform '{platform}'"
                        for field in unknown_fields
                    ]
                )
            else:
                warnings.extend(
                    [
                        f"Unknown field '{field}' for platform '{platform}'"
                        for field in unknown_fields
                    ]
                )

        # Platform-specific validations
        platform_errors, platform_warnings = self._validate_platform_specific(
            platform, config, schema
        )
        errors.extend(platform_errors)
        warnings.extend(platform_warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            platform=platform,
        )

    def _validate_field(
        self,
        platform: str,
        field: str,
        value: Any,
        schema: Dict[str, Any],
        errors: List[str],
        warnings: List[str],
    ) -> None:
        """Validate a specific field value."""

        # Type validation
        expected_types = schema.get("types", {}).get(field)
        if expected_types:
            if not isinstance(expected_types, tuple):
                expected_types = (expected_types,)

            if not isinstance(value, expected_types):
                expected_type_names = [t.__name__ for t in expected_types]
                actual_type_name = type(value).__name__
                errors.append(
                    f"Field '{field}' for platform '{platform}' must be of type "
                    f"{' or '.join(expected_type_names)}, got {actual_type_name}"
                )
                return

        # Constraint validation
        constraints = schema.get("constraints", {}).get(field, {})

        # String constraints
        if isinstance(value, str):
            if "min_length" in constraints and len(value) < constraints["min_length"]:
                errors.append(
                    f"Field '{field}' for platform '{platform}' is too short (minimum {constraints['min_length']} characters)"
                )

            if "max_length" in constraints and len(value) > constraints["max_length"]:
                errors.append(
                    f"Field '{field}' for platform '{platform}' is too long (maximum {constraints['max_length']} characters)"
                )

            if "pattern" in constraints:
                pattern = constraints["pattern"]
                if not re.match(pattern, value):
                    errors.append(
                        f"Field '{field}' for platform '{platform}' doesn't match required pattern"
                    )

        # Numeric constraints
        if isinstance(value, (int, float)):
            if "min" in constraints and value < constraints["min"]:
                errors.append(
                    f"Field '{field}' for platform '{platform}' is too small (minimum {constraints['min']})"
                )

            if "max" in constraints and value > constraints["max"]:
                errors.append(
                    f"Field '{field}' for platform '{platform}' is too large (maximum {constraints['max']})"
                )

        # List constraints
        if isinstance(value, list):
            if "min_items" in constraints and len(value) < constraints["min_items"]:
                errors.append(
                    f"Field '{field}' for platform '{platform}' has too few items (minimum {constraints['min_items']})"
                )

            if "max_items" in constraints and len(value) > constraints["max_items"]:
                errors.append(
                    f"Field '{field}' for platform '{platform}' has too many items (maximum {constraints['max_items']})"
                )

    def _validate_platform_specific(
        self, platform: str, config: Dict[str, Any], schema: Dict[str, Any]
    ) -> tuple[List[str], List[str]]:
        """Perform platform-specific validations."""
        errors = []
        warnings = []

        # Check platform OS requirements
        platform_requirements = schema.get("platform_requirements", [])
        if platform_requirements:
            current_os = self._compatibility_manager._current_os.value
            if current_os not in platform_requirements:
                errors.append(
                    f"Platform '{platform}' requires {' or '.join(platform_requirements)} but running on {current_os}"
                )

        # Crypto exchange specific validations
        if platform in ["binance", "bybit", "bitget"]:
            if config.get("enabled", False):
                # Check for demo/testnet warnings in production
                if config.get("testnet", False) or config.get("sandbox", False):
                    warnings.append(
                        f"Platform '{platform}' is configured for testnet/sandbox mode"
                    )

                # Validate API credentials format (basic check)
                api_key = config.get("api_key", "")
                if api_key and len(api_key) < 20:
                    warnings.append(
                        f"API key for '{platform}' seems too short - verify it's correct"
                    )

        # MT5 specific validations
        if platform in ["mt5", "aiomql"]:
            if config.get("enabled", False):
                if not config.get("login") and not config.get("password"):
                    warnings.append(
                        f"Platform '{platform}' is enabled but no login credentials provided"
                    )

                if config.get("server") and not config.get("server").endswith(".com"):
                    warnings.append(
                        f"Server name for '{platform}' doesn't look like a valid MT5 server"
                    )

        return errors, warnings

    def validate_all_platforms(
        self, platforms_config: Dict[str, Dict[str, Any]]
    ) -> Dict[str, ValidationResult]:
        """Validate configuration for all platforms."""
        results = {}

        for platform, config in platforms_config.items():
            results[platform] = self.validate_platform_config(platform, config)

        return results

    def get_validation_summary(
        self, results: Dict[str, ValidationResult]
    ) -> Dict[str, Any]:
        """Get summary of validation results."""
        total_platforms = len(results)
        valid_platforms = sum(1 for result in results.values() if result.is_valid)
        total_errors = sum(len(result.errors) for result in results.values())
        total_warnings = sum(len(result.warnings) for result in results.values())

        invalid_platforms = [
            platform for platform, result in results.items() if not result.is_valid
        ]

        return {
            "total_platforms": total_platforms,
            "valid_platforms": valid_platforms,
            "invalid_platforms": len(invalid_platforms),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "validation_level": self.validation_level.value,
            "invalid_platform_names": invalid_platforms,
            "overall_valid": total_errors == 0,
        }

    def suggest_fixes(self, result: ValidationResult) -> List[str]:
        """Suggest fixes for validation errors."""
        suggestions = []

        for error in result.errors:
            if "Missing required field" in error:
                field = error.split("'")[1]
                suggestions.append(f"Add required field '{field}' to configuration")

            elif "not available" in error and "Platform" in error:
                alternatives = (
                    self._compatibility_manager.get_cross_platform_alternatives(
                        result.platform
                    )
                )
                if alternatives:
                    suggestions.append(f"Use alternative platform: {alternatives[0]}")
                else:
                    suggestions.append(
                        "This platform is not supported on your operating system"
                    )

            elif "doesn't match required pattern" in error:
                field = error.split("'")[1]
                suggestions.append(
                    f"Check format of field '{field}' - it may contain invalid characters"
                )

            elif "too short" in error or "too long" in error:
                field = error.split("'")[1]
                suggestions.append(
                    f"Adjust length of field '{field}' to meet requirements"
                )

        return suggestions


def validate_execution_config(
    config: Dict[str, Any], validation_level: ValidationLevel = ValidationLevel.MODERATE
) -> Dict[str, ValidationResult]:
    """Convenience function to validate execution configuration."""
    validator = ConfigurationValidator(validation_level)
    return validator.validate_all_platforms(config)
