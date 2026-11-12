import os
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth_dependencies import get_db
from app.auth_routes import router
from app.auth_service import hash_password
from app.database import Base
from app.login_rate_limit import login_rate_limiter
from app.models import User, Workspace, WorkspaceMembership, UserSession


class AuthRoutesTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.TestSession = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )
        Base.metadata.create_all(self.engine)

        self.db = self.TestSession()

        self.workspace = Workspace(
            name="Test Workspace",
            slug="test-workspace",
            workspace_type="business",
            is_active=True,
        )
        self.user = User(
            email="owner@example.com",
            display_name="Test Owner",
            is_active=True,
            password_hash=hash_password("Correct-Test-Password-2026!"),
        )

        self.db.add_all([self.workspace, self.user])
        self.db.flush()

        self.membership = WorkspaceMembership(
            workspace_id=self.workspace.id,
            user_id=self.user.id,
            role="owner",
        )
        self.db.add(self.membership)
        self.db.commit()

        self.user_id = self.user.id
        self.workspace_id = self.workspace.id

        self.app = FastAPI()
        self.app.include_router(router)

        def override_get_db():
            session = self.TestSession()
            try:
                yield session
            finally:
                session.close()

        self.app.dependency_overrides[get_db] = override_get_db

        login_rate_limiter.clear()
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        login_rate_limiter.clear()

    def login(self, email="owner@example.com",
              password="Correct-Test-Password-2026!"):
        return self.client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )

    def test_valid_login_creates_server_side_session(self):
        response = self.login()

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["authenticated"])
        self.assertEqual(body["user"]["email"], "owner@example.com")
        self.assertEqual(body["user"]["memberships"][0]["role"], "owner")

        cookie = response.cookies.get("tdj_session")
        self.assertTrue(cookie)
        self.assertNotEqual(cookie, "")

        with self.TestSession() as db:
            session = db.scalar(
                select(UserSession).where(UserSession.user_id == self.user_id)
            )
            self.assertIsNotNone(session)
            self.assertNotEqual(session.token_hash, cookie)

        cookie_header = response.headers.get("set-cookie", "").lower()
        self.assertIn("httponly", cookie_header)
        self.assertIn("samesite=lax", cookie_header)
        self.assertIn("path=/", cookie_header)

    def test_wrong_password_returns_generic_401(self):
        response = self.login(password="Wrong-Password-2026!")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid email or password.")
        self.assertNotIn("tdj_session", response.cookies)

    def test_unknown_email_returns_same_generic_401(self):
        response = self.login(
            email="unknown@example.com",
            password="Wrong-Password-2026!",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid email or password.")

    def test_sixth_failed_attempt_is_rate_limited(self):
        for _ in range(5):
            response = self.login(password="Wrong-Password-2026!")
            self.assertEqual(response.status_code, 401)

        response = self.login(password="Wrong-Password-2026!")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers.get("retry-after"), "900")

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.db.commit()

        response = self.login()
        self.assertEqual(response.status_code, 401)

    def test_me_without_cookie_returns_401(self):
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_me_with_valid_session_returns_user(self):
        login_response = self.login()
        self.assertEqual(login_response.status_code, 200)

        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["authenticated"])
        self.assertEqual(response.json()["user"]["id"], self.user_id)

    def test_logout_revokes_session_and_clears_cookie(self):
        login_response = self.login()
        token = login_response.cookies.get("tdj_session")
        self.assertTrue(token)

        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 200)

        with self.TestSession() as db:
            session = db.scalar(
                select(UserSession).where(UserSession.user_id == self.user_id)
            )
            self.assertIsNotNone(session.revoked_at)

        me_response = self.client.get("/api/auth/me")
        self.assertEqual(me_response.status_code, 401)

        delete_cookie = response.headers.get("set-cookie", "").lower()
        self.assertIn("tdj_session", delete_cookie)
        self.assertIn("max-age=0", delete_cookie)

    def test_logout_with_invalid_cookie_is_safe(self):
        self.client.cookies.set("tdj_session", "invalid-session-token")

        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "max-age=0",
            response.headers.get("set-cookie", "").lower(),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
