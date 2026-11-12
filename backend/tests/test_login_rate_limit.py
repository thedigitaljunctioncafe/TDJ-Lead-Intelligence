import unittest

from app.login_rate_limit import LoginRateLimiter


class FakeClock:
    def __init__(self):
        self.value = 1000.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class TestLoginRateLimiter(unittest.TestCase):

    def setUp(self):
        self.clock = FakeClock()
        self.limiter = LoginRateLimiter(
            max_attempts=5,
            window_seconds=900,
            clock=self.clock,
        )
        self.ip = "192.0.2.10"
        self.email = "owner@example.test"

    def test_first_five_attempts_are_allowed(self):
        for _ in range(5):
            self.assertTrue(self.limiter.is_allowed(self.ip, self.email))
            self.limiter.record_failure(self.ip, self.email)

    def test_sixth_attempt_is_blocked(self):
        for _ in range(5):
            self.limiter.record_failure(self.ip, self.email)

        self.assertFalse(self.limiter.is_allowed(self.ip, self.email))

    def test_attempts_are_allowed_after_window_expires(self):
        for _ in range(5):
            self.limiter.record_failure(self.ip, self.email)

        self.clock.advance(901)

        self.assertTrue(self.limiter.is_allowed(self.ip, self.email))

    def test_different_ip_has_separate_counter(self):
        for _ in range(5):
            self.limiter.record_failure(self.ip, self.email)

        self.assertTrue(
            self.limiter.is_allowed("192.0.2.11", self.email)
        )

    def test_different_email_has_separate_counter(self):
        for _ in range(5):
            self.limiter.record_failure(self.ip, self.email)

        self.assertTrue(
            self.limiter.is_allowed(self.ip, "another@example.test")
        )

    def test_success_resets_counter(self):
        for _ in range(5):
            self.limiter.record_failure(self.ip, self.email)

        self.assertFalse(self.limiter.is_allowed(self.ip, self.email))

        self.limiter.record_success(self.ip, self.email)

        self.assertTrue(self.limiter.is_allowed(self.ip, self.email))

    def test_clear_resets_all_counters(self):
        for _ in range(5):
            self.limiter.record_failure(self.ip, self.email)

        self.limiter.clear()

        self.assertTrue(self.limiter.is_allowed(self.ip, self.email))

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            self.limiter.is_allowed("", self.email)

        with self.assertRaises(ValueError):
            self.limiter.record_failure(self.ip, "")

        with self.assertRaises(ValueError):
            LoginRateLimiter(max_attempts=0)

        with self.assertRaises(ValueError):
            LoginRateLimiter(window_seconds=0)


if __name__ == "__main__":
    unittest.main()
