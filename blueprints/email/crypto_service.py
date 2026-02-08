"""
Encryption service for email credentials.

Provides transparent Fernet encryption for sensitive fields in the database.
"""

import os
from cryptography.fernet import Fernet
from tortoise import fields


class EncryptedTextField(fields.TextField):
    """
    Custom Tortoise ORM field that transparently encrypts/decrypts text values.

    Uses Fernet symmetric encryption with a key from FERNET_KEY environment variable.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load encryption key from environment
        key = os.getenv("FERNET_KEY")
        if not key:
            raise ValueError(
                "FERNET_KEY environment variable required for encrypted fields. "
                'Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        try:
            self.fernet = Fernet(key.encode())
        except Exception as e:
            raise ValueError(f"Invalid FERNET_KEY format: {e}")

    def to_db_value(self, value: str, instance) -> str:
        """Encrypt value before storing in database."""
        if value is None:
            return None
        # Encrypt and return as URL-safe base64 string
        return self.fernet.encrypt(value.encode()).decode()

    def to_python_value(self, value: str) -> str:
        """Decrypt value when loading from database."""
        if value is None:
            return None
        # Decrypt Fernet token
        return self.fernet.decrypt(value.encode()).decode()


def validate_fernet_key():
    """
    Validate that FERNET_KEY is set and functional.

    Raises:
        ValueError: If key is missing or invalid
    """
    key = os.getenv("FERNET_KEY")
    if not key:
        raise ValueError("FERNET_KEY environment variable not set")

    try:
        f = Fernet(key.encode())
        # Test encryption/decryption cycle
        test_value = b"test_encryption"
        encrypted = f.encrypt(test_value)
        decrypted = f.decrypt(encrypted)
        if decrypted != test_value:
            raise ValueError("Encryption/decryption test failed")
    except Exception as e:
        raise ValueError(f"FERNET_KEY validation failed: {e}")
