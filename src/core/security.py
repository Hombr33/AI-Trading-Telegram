"""
Security utilities for the AI Trading Bot system.
"""

import hashlib
import hmac
import os

try:
    import bcrypt

    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False


def verify_bridge_token(token: str) -> bool:
    """Verify bridge authentication token."""
    from .config import config

    expected_token = os.getenv(config.bridge.token_env_key)

    if not expected_token:
        return False

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(token, expected_token)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt (secure) or SHA-256 (fallback)."""
    if BCRYPT_AVAILABLE:
        # Use bcrypt for secure password hashing
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        # Fallback to SHA-256 (less secure, but better than plain text)
        # Note: bcrypt should be installed in production environments
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            "bcrypt not available, using SHA-256 fallback. Install bcrypt for production use."
        )
        return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    if BCRYPT_AVAILABLE and hashed.startswith("$2b$"):
        # bcrypt hash verification
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    else:
        # SHA-256 fallback verification
        return hash_password(password) == hashed


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    import secrets

    return secrets.token_urlsafe(length)


def sanitize_input(input_string: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    import html

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&", ";", "(", ")", "{", "}", "[", "]"]
    sanitized = input_string

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    # HTML escape remaining content
    return html.escape(sanitized)


def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol format."""
    if not symbol or len(symbol) > 20:
        return False

    # Allow alphanumeric characters and common trading symbols
    allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    return all(c in allowed_chars for c in symbol.upper())


def validate_price(price: float) -> bool:
    """Validate price values."""
    if not isinstance(price, (int, float)):
        return False

    if price <= 0:
        return False

    if price > 1000000:  # Reasonable upper limit
        return False

    return True


def validate_volume(volume: float) -> bool:
    """Validate volume values."""
    if not isinstance(volume, (int, float)):
        return False

    if volume <= 0:
        return False

    if volume > 1000:  # Reasonable upper limit
        return False

    return True
