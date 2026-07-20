from datetime import datetime, timedelta

import pytest

from app.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_empty_limiter_is_not_limited(self):
        limiter = RateLimiter(max_attempts=5, window_seconds=900)
        assert limiter.is_limited("127.0.0.1") is False
        assert limiter.attempt_count("127.0.0.1") == 0

    def test_records_attempts(self):
        limiter = RateLimiter(max_attempts=5, window_seconds=900)
        for _ in range(3):
            limiter.record_attempt("127.0.0.1")
        assert limiter.attempt_count("127.0.0.1") == 3
        assert limiter.is_limited("127.0.0.1") is False

    def test_limits_after_max_attempts(self):
        limiter = RateLimiter(max_attempts=5, window_seconds=900)
        for _ in range(5):
            limiter.record_attempt("127.0.0.1")
        assert limiter.is_limited("127.0.0.1") is True

    def test_reset_clears_attempts(self):
        limiter = RateLimiter(max_attempts=5, window_seconds=900)
        for _ in range(5):
            limiter.record_attempt("127.0.0.1")
        limiter.reset("127.0.0.1")
        assert limiter.is_limited("127.0.0.1") is False
        assert limiter.attempt_count("127.0.0.1") == 0

    def test_windows_expire_older_attempts(self):
        limiter = RateLimiter(max_attempts=5, window_seconds=60)

        now = datetime.now()
        old = now - timedelta(seconds=120)
        limiter._store["127.0.0.1"] = [old]
        assert limiter.attempt_count("127.0.0.1") == 0

    def test_retry_after_returns_positive_when_limited(self):
        limiter = RateLimiter(max_attempts=2, window_seconds=60)
        limiter.record_attempt("127.0.0.1")
        limiter.record_attempt("127.0.0.1")
        assert limiter.is_limited("127.0.0.1") is True
        assert limiter.retry_after("127.0.0.1") > 0

    def test_retry_after_returns_zero_when_not_limited(self):
        limiter = RateLimiter(max_attempts=5, window_seconds=900)
        assert limiter.retry_after("127.0.0.1") == 0

    def test_keys_are_isolated(self):
        limiter = RateLimiter(max_attempts=5, window_seconds=900)
        for _ in range(5):
            limiter.record_attempt("127.0.0.1")
        assert limiter.is_limited("127.0.0.2") is False

    def test_record_attempt_while_limited(self):
        limiter = RateLimiter(max_attempts=2, window_seconds=60)
        limiter.record_attempt("127.0.0.1")
        limiter.record_attempt("127.0.0.1")
        assert limiter.is_limited("127.0.0.1") is True
        limiter.record_attempt("127.0.0.1")
        assert limiter.is_limited("127.0.0.1") is True
