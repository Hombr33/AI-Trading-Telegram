"""YAML configuration loader utility."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from src.core.logging import get_logger

logger = get_logger(__name__)


def load_yaml_config(config_path: str) -> Optional[Dict[str, Any]]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Configuration dictionary or None if failed to load.
    """
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return None

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        logger.info(f"Successfully loaded configuration from {config_path}")
        return config

    except Exception as e:
        logger.error(f"Failed to load configuration from {config_path}: {e}")
        return None


def get_mt5_config_from_yaml() -> Dict[str, Any]:
    """Get MT5 configuration from YAML file.

    Returns:
        MT5 configuration dictionary.
    """
    # Try to load from settings.yaml
    config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
    config = load_yaml_config(str(config_path))

    if not config:
        return {}

    # Extract MT5 configuration
    mt5_config = config.get("metatrader5", {})

    # Map YAML keys to our config format
    mapped_config = {}
    if "login" in mt5_config:
        mapped_config["login"] = mt5_config["login"]
    if "password" in mt5_config:
        mapped_config["password"] = mt5_config["password"]
    if "server" in mt5_config:
        mapped_config["server"] = mt5_config["server"]
    if "broker_name" in mt5_config:
        mapped_config["broker_name"] = mt5_config["broker_name"]
    if "timeout" in mt5_config:
        mapped_config["timeout"] = mt5_config["timeout"]

    return mapped_config


def get_openai_config_from_yaml() -> Dict[str, Any]:
    """Get OpenAI configuration from YAML file.

    Returns:
        OpenAI configuration dictionary.
    """
    config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
    config = load_yaml_config(str(config_path))

    if not config:
        return {}

    # Extract OpenAI configuration
    openai_config = config.get("openai", {})

    return openai_config
