"""
Unit tests for the security module.
"""

import pytest
import hashlib
from unittest.mock import patch, Mock
from src.core.security import (
    verify_bridge_token,
    hash_password,
    verify_password,
    generate_secure_token,
    sanitize_input,
    validate_symbol,
    validate_price,
    validate_volume,
)


class TestSecurityFunctions:
    """Test cases for security utility functions."""

    def test_generate_secure_token(self):
        """Test secure token generation."""
        token = generate_secure_token()
        assert token is not None
        assert len(token) > 0

        # Test custom length
        token_32 = generate_secure_token(32)
        token_16 = generate_secure_token(16)

        assert len(token_32) != len(token_16)

        # Test uniqueness
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        assert token1 != token2

    @patch("src.core.security.bcrypt")
    def test_hash_password_with_bcrypt(self, mock_bcrypt):
        """Test password hashing with bcrypt available."""
        mock_bcrypt.gensalt.return_value = b"salt"
        mock_bcrypt.hashpw.return_value = b"hashed_password"

        with patch("src.core.security.BCRYPT_AVAILABLE", True):
            result = hash_password("test_password")

            mock_bcrypt.gensalt.assert_called_once()
            mock_bcrypt.hashpw.assert_called_once()
            assert result == "hashed_password"

    def test_hash_password_without_bcrypt(self):
        """Test password hashing without bcrypt (fallback)."""
        with patch("src.core.security.BCRYPT_AVAILABLE", False):
            result = hash_password("test_password")

            # Should use SHA-256 fallback
            expected = hashlib.sha256("test_password".encode()).hexdigest()
            assert result == expected

    @patch("src.core.security.bcrypt")
    def test_verify_password_with_bcrypt(self, mock_bcrypt):
        """Test password verification with bcrypt."""
        mock_bcrypt.checkpw.return_value = True

        with patch("src.core.security.BCRYPT_AVAILABLE", True):
            result = verify_password("test_password", "$2b$12$hashed")

            mock_bcrypt.checkpw.assert_called_once()
            assert result == True

    def test_verify_password_sha256_fallback(self):
        """Test password verification with SHA-256 fallback."""
        password = "test_password"
        hashed = hashlib.sha256(password.encode()).hexdigest()

        with patch("src.core.security.BCRYPT_AVAILABLE", False):
            result = verify_password(password, hashed)
            assert result == True

            # Test wrong password
            result = verify_password("wrong_password", hashed)
            assert result == False

    @patch("src.core.config.config")
    @patch("src.core.security.os.getenv")
    def test_verify_bridge_token(self, mock_getenv, mock_config):
        """Test bridge token verification."""
        mock_bridge = Mock()
        mock_bridge.token_env_key = "TEST_TOKEN"
        mock_config.bridge = mock_bridge

        # Test valid token
        mock_getenv.return_value = "valid_token"
        result = verify_bridge_token("valid_token")
        assert result == True

        # Test invalid token
        result = verify_bridge_token("invalid_token")
        assert result == False

        # Test missing environment token
        mock_getenv.return_value = None
        result = verify_bridge_token("any_token")
        assert result == False

    def test_sanitize_input(self):
        """Test input sanitization."""
        # Test normal input
        result = sanitize_input("normal_text")
        assert result == "normal_text"

        # Test input with dangerous characters
        dangerous_input = "<script>alert('xss')</script>"
        result = sanitize_input(dangerous_input)
        assert "<" not in result
        assert ">" not in result
        assert "script" in result  # Content should remain but tags removed

        # Test input with various dangerous characters
        input_with_chars = "test'\"&;(){}[]"
        result = sanitize_input(input_with_chars)
        assert "'" not in result
        assert '"' not in result
        assert "&" not in result or "&amp;" in result  # HTML escaped

    def test_validate_symbol(self):
        """Test trading symbol validation."""
        # Valid symbols
        assert validate_symbol("EURUSD") == True
        assert validate_symbol("BTCUSDT") == True
        assert validate_symbol("XAUUSD") == True
        assert validate_symbol("SPX500") == True

        # Invalid symbols
        assert validate_symbol("") == False
        assert validate_symbol(None) == False
        assert validate_symbol("EUR/USD") == False  # Contains slash
        assert validate_symbol("eur-usd") == False  # Contains dash
        assert validate_symbol("A" * 25) == False  # Too long
        assert validate_symbol("SYMBOL@") == False  # Invalid character

    def test_validate_price(self):
        """Test price validation."""
        # Valid prices
        assert validate_price(1.0) == True
        assert validate_price(100.50) == True
        assert validate_price(0.001) == True
        assert validate_price(999999) == True

        # Invalid prices
        assert validate_price(0) == False
        assert validate_price(-1.0) == False
        assert validate_price(1000001) == False  # Too high
        assert validate_price("100") == False  # String
        assert validate_price(None) == False

    def test_validate_volume(self):
        """Test volume validation."""
        # Valid volumes
        assert validate_volume(0.01) == True
        assert validate_volume(1.0) == True
        assert validate_volume(100.0) == True
        assert validate_volume(999.99) == True

        # Invalid volumes
        assert validate_volume(0) == False
        assert validate_volume(-1.0) == False
        assert validate_volume(1001) == False  # Too high
        assert validate_volume("10") == False  # String
        assert validate_volume(None) == False


class TestSecurityEdgeCases:
    """Test edge cases and error conditions."""

    def test_hash_password_empty_string(self):
        """Test hashing empty password."""
        result = hash_password("")
        assert result is not None
        assert len(result) > 0

    def test_sanitize_input_empty_string(self):
        """Test sanitizing empty input."""
        result = sanitize_input("")
        assert result == ""

    def test_validate_symbol_edge_cases(self):
        """Test symbol validation edge cases."""
        # Exactly at length limit
        assert validate_symbol("A" * 20) == True
        assert validate_symbol("A" * 21) == False

        # Mixed case
        assert validate_symbol("EurUsd") == True
        assert validate_symbol("eurusd") == True

    def test_validate_price_edge_cases(self):
        """Test price validation edge cases."""
        # Exactly at limits
        assert validate_price(0.000001) == True
        assert validate_price(1000000) == True
        assert validate_price(1000000.1) == False

    def test_validate_volume_edge_cases(self):
        """Test volume validation edge cases."""
        # Exactly at limits
        assert validate_volume(0.000001) == True
        assert validate_volume(1000) == True
        assert validate_volume(1000.1) == False


if __name__ == "__main__":
    pytest.main([__file__])
