"""Tests for email helper functions in blueprints/email/helpers.py."""

from blueprints.email.helpers import generate_email_token, get_user_email_address


class TestGenerateEmailToken:
    def test_returns_16_char_hex(self):
        token = generate_email_token("user-123", "my-secret")
        assert len(token) == 16
        assert all(c in "0123456789abcdef" for c in token)

    def test_deterministic(self):
        t1 = generate_email_token("user-123", "my-secret")
        t2 = generate_email_token("user-123", "my-secret")
        assert t1 == t2

    def test_different_users_different_tokens(self):
        t1 = generate_email_token("user-1", "secret")
        t2 = generate_email_token("user-2", "secret")
        assert t1 != t2

    def test_different_secrets_different_tokens(self):
        t1 = generate_email_token("user-1", "secret-a")
        t2 = generate_email_token("user-1", "secret-b")
        assert t1 != t2


class TestGetUserEmailAddress:
    def test_formats_correctly(self):
        addr = get_user_email_address("abc123", "example.com")
        assert addr == "ask+abc123@example.com"

    def test_preserves_token(self):
        token = "deadbeef12345678"
        addr = get_user_email_address(token, "mail.test.org")
        assert token in addr
        assert addr.startswith("ask+")
        assert "@mail.test.org" in addr
