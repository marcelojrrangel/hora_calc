import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import TypeVar

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 15 * 60

T = TypeVar("T")


class RateLimiter:
    """In-memory sliding-window rate limiter keyed by client IP."""

    def __init__(self, max_attempts: int = MAX_ATTEMPTS, window_seconds: int = WINDOW_SECONDS):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._store: dict[str, list[datetime]] = {}
        self._lock = threading.Lock()

    def _now(self) -> datetime:
        return datetime.now()

    def record_attempt(self, key: str) -> None:
        now = self._now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        with self._lock:
            attempts = self._store.get(key, [])
            attempts = [t for t in attempts if t > cutoff]
            attempts.append(now)
            self._store[key] = attempts

    def reset(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def reset_all(self) -> None:
        with self._lock:
            self._store.clear()

    def is_limited(self, key: str) -> bool:
        now = self._now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        with self._lock:
            attempts = self._store.get(key, [])
            attempts = [t for t in attempts if t > cutoff]
            self._store[key] = attempts
            return len(attempts) >= self.max_attempts

    def retry_after(self, key: str) -> int:
        """Return remaining seconds until the oldest attempt expires."""
        now = self._now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        with self._lock:
            attempts = self._store.get(key, [])
            attempts = [t for t in attempts if t > cutoff]
            if not attempts:
                return 0
            oldest = min(attempts)
            return max(0, int((oldest + timedelta(seconds=self.window_seconds) - now).total_seconds()) + 1)

    def attempt_count(self, key: str) -> int:
        now = self._now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        with self._lock:
            attempts = self._store.get(key, [])
            attempts = [t for t in attempts if t > cutoff]
            self._store[key] = attempts
            return len(attempts)


# Global instance used by the application.
login_rate_limiter = RateLimiter()


def run_synchronized(lock: threading.Lock, fn: Callable[[], T]) -> T:
    """Small helper for callers that need a guaranteed atomic read+write."""
    with lock:
        return fn()
