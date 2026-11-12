"""Thread-safe per-source request rate limiter."""

import threading
import time


class RateLimiter:
    def __init__(self, requests_per_minute: float = 30):
        if isinstance(requests_per_minute, bool) or not isinstance(requests_per_minute, (int, float)):
            raise TypeError("requests_per_minute must be a number")
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be greater than zero")

        self.interval = 60.0 / float(requests_per_minute)
        self._next_allowed: dict[str, float] = {}
        self._lock = threading.Lock()

    def acquire(self, source_key: str) -> float:
        """Wait for permission and return the seconds waited."""
        if not isinstance(source_key, str) or not source_key.strip():
            raise ValueError("source_key must be a non-empty string")

        with self._lock:
            now = time.monotonic()
            scheduled = max(now, self._next_allowed.get(source_key, now))
            delay = max(0.0, scheduled - now)
            self._next_allowed[source_key] = scheduled + self.interval

        if delay:
            time.sleep(delay)

        return delay

    def reset(self, source_key: str | None = None) -> None:
        with self._lock:
            if source_key is None:
                self._next_allowed.clear()
            else:
                self._next_allowed.pop(source_key, None)
