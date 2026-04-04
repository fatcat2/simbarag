"""Tests for encryption/decryption in blueprints/email/crypto_service.py."""

import os
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet


# Generate a valid key for testing
TEST_FERNET_KEY = Fernet.generate_key().decode()


class TestEncryptedTextField:
    @pytest.fixture
    def field(self):
        with patch.dict(os.environ, {"FERNET_KEY": TEST_FERNET_KEY}):
            from blueprints.email.crypto_service import EncryptedTextField

            return EncryptedTextField()

    def test_encrypt_decrypt_roundtrip(self, field):
        original = "my secret password"
        encrypted = field.to_db_value(original, None)
        decrypted = field.to_python_value(encrypted)
        assert decrypted == original
        assert encrypted != original

    def test_none_passthrough(self, field):
        assert field.to_db_value(None, None) is None
        assert field.to_python_value(None) is None

    def test_unicode_roundtrip(self, field):
        original = "Hello 世界 🐱"
        encrypted = field.to_db_value(original, None)
        decrypted = field.to_python_value(encrypted)
        assert decrypted == original

    def test_empty_string_roundtrip(self, field):
        encrypted = field.to_db_value("", None)
        decrypted = field.to_python_value(encrypted)
        assert decrypted == ""

    def test_long_text_roundtrip(self, field):
        original = "x" * 10000
        encrypted = field.to_db_value(original, None)
        decrypted = field.to_python_value(encrypted)
        assert decrypted == original

    def test_different_encryptions_differ(self, field):
        """Fernet includes a timestamp, so two encryptions of the same value differ."""
        e1 = field.to_db_value("same", None)
        e2 = field.to_db_value("same", None)
        assert e1 != e2  # Different ciphertexts
        assert field.to_python_value(e1) == field.to_python_value(e2) == "same"

    def test_wrong_key_fails(self, field):
        encrypted = field.to_db_value("secret", None)

        # Create a field with a different key
        other_key = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"FERNET_KEY": other_key}):
            from blueprints.email.crypto_service import EncryptedTextField

            other_field = EncryptedTextField()

        with pytest.raises(Exception):
            other_field.to_python_value(encrypted)


class TestValidateFernetKey:
    def test_valid_key(self):
        with patch.dict(os.environ, {"FERNET_KEY": TEST_FERNET_KEY}):
            from blueprints.email.crypto_service import validate_fernet_key

            validate_fernet_key()  # Should not raise

    def test_missing_key(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("FERNET_KEY", None)
            from blueprints.email.crypto_service import validate_fernet_key

            with pytest.raises(ValueError, match="not set"):
                validate_fernet_key()

    def test_invalid_key(self):
        with patch.dict(os.environ, {"FERNET_KEY": "not-a-valid-key"}):
            from blueprints.email.crypto_service import validate_fernet_key

            with pytest.raises(ValueError, match="validation failed"):
                validate_fernet_key()
