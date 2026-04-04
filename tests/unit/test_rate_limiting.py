"""Tests for rate limiting logic in email and WhatsApp blueprints."""

import time


class TestEmailRateLimit:
    def setup_method(self):
        """Reset rate limit store before each test."""
        from blueprints.email import _rate_limit_store

        _rate_limit_store.clear()

    def test_allows_under_limit(self):
        from blueprints.email import _check_rate_limit, RATE_LIMIT_MAX

        for _ in range(RATE_LIMIT_MAX):
            assert _check_rate_limit("sender@test.com") is True

    def test_blocks_at_limit(self):
        from blueprints.email import _check_rate_limit, RATE_LIMIT_MAX

        for _ in range(RATE_LIMIT_MAX):
            _check_rate_limit("sender@test.com")

        assert _check_rate_limit("sender@test.com") is False

    def test_different_senders_independent(self):
        from blueprints.email import _check_rate_limit, RATE_LIMIT_MAX

        for _ in range(RATE_LIMIT_MAX):
            _check_rate_limit("user1@test.com")

        # user1 is at limit, but user2 should be fine
        assert _check_rate_limit("user1@test.com") is False
        assert _check_rate_limit("user2@test.com") is True

    def test_window_expiry(self):
        from blueprints.email import (
            _check_rate_limit,
            _rate_limit_store,
            RATE_LIMIT_MAX,
        )

        # Fill up the rate limit with timestamps in the past
        past = time.monotonic() - 999  # Well beyond any window
        _rate_limit_store["old@test.com"] = [past] * RATE_LIMIT_MAX

        # Should be allowed because all timestamps are expired
        assert _check_rate_limit("old@test.com") is True


class TestWhatsAppRateLimit:
    def setup_method(self):
        """Reset rate limit store before each test."""
        from blueprints.whatsapp import _rate_limit_store

        _rate_limit_store.clear()

    def test_allows_under_limit(self):
        from blueprints.whatsapp import _check_rate_limit, RATE_LIMIT_MAX

        for _ in range(RATE_LIMIT_MAX):
            assert _check_rate_limit("whatsapp:+1234567890") is True

    def test_blocks_at_limit(self):
        from blueprints.whatsapp import _check_rate_limit, RATE_LIMIT_MAX

        for _ in range(RATE_LIMIT_MAX):
            _check_rate_limit("whatsapp:+1234567890")

        assert _check_rate_limit("whatsapp:+1234567890") is False

    def test_different_numbers_independent(self):
        from blueprints.whatsapp import _check_rate_limit, RATE_LIMIT_MAX

        for _ in range(RATE_LIMIT_MAX):
            _check_rate_limit("whatsapp:+1111111111")

        assert _check_rate_limit("whatsapp:+1111111111") is False
        assert _check_rate_limit("whatsapp:+2222222222") is True

    def test_window_expiry(self):
        from blueprints.whatsapp import (
            _check_rate_limit,
            _rate_limit_store,
            RATE_LIMIT_MAX,
        )

        past = time.monotonic() - 999
        _rate_limit_store["whatsapp:+9999999999"] = [past] * RATE_LIMIT_MAX

        assert _check_rate_limit("whatsapp:+9999999999") is True
