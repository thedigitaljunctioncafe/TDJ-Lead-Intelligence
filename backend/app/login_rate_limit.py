import hashlib
import threading
import time
from collections import defaultdict, deque


class LoginRateLimiter:
    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 900,
        clock=None,
    ):
        if not isinstance(max_attempts, int) or max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer.")

        if not isinstance(window_seconds, int) or window_seconds < 1:
            raise ValueError("window_seconds must be a positive integer.")

        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._clock = clock or time.monotonic
        self._attempts = defaultdict(deque)
        self._lock = threading.Lock()

    @staticmethod
    def _key(ip_address: str, email: str) -> str:
        if not isinstance(ip_address, str) or not ip_address.strip():
            raise ValueError("A valid IP address is required.")

        if not isinstance(email, str) or not email.strip():
            raise ValueError("A valid email is required.")

        value = f"{ip_address.strip().lower()}:{email.strip().lower()}"
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def is_allowed(self, ip_address: str, email: str) -> bool:
        key = self._key(ip_address, email)
        now = self._clock()

        with self._lock:
            attempts = self._attempts[key]

            while attempts and now - attempts[0] >= self.window_seconds:
                attempts.popleft()

            if not attempts:
                self._attempts.pop(key, None)
                return True

            return len(attempts) < self.max_attempts

    def record_failure(self, ip_address: str, email: str) -> None:
        key = self._key(ip_address, email)
        now = self._clock()

        with self._lock:
            attempts = self._attempts[key]

            while attempts and now - attempts[0] >= self.window_seconds:
                attempts.popleft()

            attempts.append(now)

    def record_success(self, ip_address: str, email: str) -> None:
        key = self._key(ip_address, email)

        with self._lock:
            self._attempts.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._attempts.clear()


login_rate_limiter = LoginRateLimiter()
