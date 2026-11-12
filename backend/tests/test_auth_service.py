"""Isolated tests for authentication and session security."""

import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth_service import (
    create_session,
    get_session_user,
    hash_password,
    revoke_all_user_sessions,
    revoke_session,
    verify_password,
)
from app.database import Base
from app.models import User, UserSession


class TestAuthenticationService(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )
        self.db = self.Session()

        self.user = User(
            email="auth-test@example.test",
            display_name="Authentication Test",
            is_active=True,
            password_hash=hash_password("Test-Password-2026!"),
        )
        self.db.add(self.user)
        self.db.commit()

        self.now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_password_hash_is_not_plain_text(self):
        encoded = hash_password("Strong-Test-Password!")
        self.assertNotEqual(encoded, "Strong-Test-Password!")
        self.assertTrue(verify_password("Strong-Test-Password!", encoded))

    def test_wrong_password_is_rejected(self):
        encoded = hash_password("Strong-Test-Password!")
        self.assertFalse(verify_password("Wrong-Password!", encoded))

    def test_weak_password_is_rejected(self):
        with self.assertRaises(ValueError):
            hash_password("short")

    def test_malformed_hash_is_rejected_safely(self):
        self.assertFalse(verify_password("Some-Password!", "not-a-valid-hash"))

    def test_session_token_is_random_and_only_hash_is_stored(self):
        token, session = create_session(self.db, self.user, now=self.now)
        self.assertGreaterEqual(len(token), 32)
        self.assertNotEqual(session.token_hash, token)
        self.assertEqual(len(session.token_hash), 64)
        self.assertEqual(
            session.token_hash,
            __import__("hashlib").sha256(token.encode()).hexdigest(),
        )

    def test_valid_session_returns_user(self):
        token, _ = create_session(self.db, self.user, now=self.now)
        result = get_session_user(self.db, token, now=self.now)
        self.assertIsNotNone(result)
        self.assertEqual(result[1].id, self.user.id)

    def test_expired_session_is_rejected_and_revoked(self):
        token, session = create_session(
            self.db,
            self.user,
            lifetime=timedelta(hours=1),
            now=self.now,
        )
        result = get_session_user(
            self.db,
            token,
            now=self.now + timedelta(hours=1, seconds=1),
        )
        self.assertIsNone(result)
        self.assertIsNotNone(session.revoked_at)

    def test_revoked_session_is_rejected(self):
        token, _ = create_session(self.db, self.user, now=self.now)
        self.assertTrue(revoke_session(self.db, token, now=self.now))
        self.assertIsNone(get_session_user(self.db, token, now=self.now))

    def test_repeated_revocation_is_safe(self):
        token, _ = create_session(self.db, self.user, now=self.now)
        self.assertTrue(revoke_session(self.db, token, now=self.now))
        self.assertFalse(revoke_session(self.db, token, now=self.now))

    def test_disabled_user_session_is_rejected(self):
        token, session = create_session(self.db, self.user, now=self.now)
        self.user.is_active = False
        self.db.flush()

        self.assertIsNone(get_session_user(self.db, token, now=self.now))
        self.assertIsNotNone(session.revoked_at)

    def test_all_user_sessions_can_be_revoked(self):
        first, _ = create_session(self.db, self.user, now=self.now)
        second, _ = create_session(self.db, self.user, now=self.now)

        count = revoke_all_user_sessions(
            self.db, self.user.id, now=self.now
        )
        self.assertEqual(count, 2)
        self.assertIsNone(get_session_user(self.db, first, now=self.now))
        self.assertIsNone(get_session_user(self.db, second, now=self.now))

    def test_session_lifetime_is_bounded(self):
        with self.assertRaises(ValueError):
            create_session(
                self.db,
                self.user,
                lifetime=timedelta(days=8),
                now=self.now,
            )

    def test_inactive_user_cannot_receive_session(self):
        self.user.is_active = False
        self.db.flush()
        with self.assertRaises(ValueError):
            create_session(self.db, self.user, now=self.now)

    def test_invalid_token_is_rejected(self):
        self.assertIsNone(get_session_user(self.db, "invalid", now=self.now))
        with self.assertRaises(ValueError):
            revoke_session(self.db, "invalid", now=self.now)

    def test_service_does_not_commit(self):
        self.db.commit()
        self.db.begin()

        token, _ = create_session(self.db, self.user, now=self.now)
        self.assertTrue(self.db.in_transaction())

        self.db.rollback()
        self.assertIsNone(get_session_user(self.db, token, now=self.now))

    def test_session_expiry_defaults_to_twelve_hours(self):
        _, session = create_session(self.db, self.user, now=self.now)
        self.assertEqual(
            session.expires_at,
            self.now + timedelta(hours=12),
        )


if __name__ == "__main__":
    unittest.main()
