import unittest

from fastapi import HTTPException
from starlette.requests import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth_dependencies import (
    SESSION_COOKIE_NAME,
    get_current_user,
    get_workspace_membership,
    require_workspace_roles,
)
from app.auth_service import create_session, hash_password
from app.database import Base
from app.models import User, Workspace, WorkspaceMembership


class TestAuthenticationDependencies(unittest.TestCase):

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

        self.workspace = Workspace(
            name="Primary Workspace",
            slug="primary-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.foreign_workspace = Workspace(
            name="Foreign Workspace",
            slug="foreign-workspace",
            workspace_type="organization",
            is_active=True,
        )

        self.user = User(
            email="dependency-test@example.test",
            display_name="Dependency Test",
            password_hash=hash_password("Dependency-Test-2026!"),
            is_active=True,
        )

        self.db.add_all([
            self.workspace,
            self.foreign_workspace,
            self.user,
        ])
        self.db.flush()

        self.membership = WorkspaceMembership(
            workspace_id=self.workspace.id,
            user_id=self.user.id,
            role="owner",
        )
        self.db.add(self.membership)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def make_request(self, token=None):
        headers = []

        if token is not None:
            headers.append((
                b"cookie",
                f"{SESSION_COOKIE_NAME}={token}".encode("ascii"),
            ))

        return Request({
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": headers,
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 50000),
            "scheme": "http",
        })

    def test_missing_cookie_requires_authentication(self):
        with self.assertRaises(HTTPException) as context:
            get_current_user(self.make_request(), self.db)

        self.assertEqual(context.exception.status_code, 401)

    def test_invalid_session_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            get_current_user(self.make_request("invalid-token"), self.db)

        self.assertEqual(context.exception.status_code, 401)

    def test_valid_session_returns_user(self):
        token, _ = create_session(self.db, self.user)
        self.db.commit()

        result = get_current_user(self.make_request(token), self.db)

        self.assertEqual(result.id, self.user.id)

    def test_workspace_member_is_authorized(self):
        membership, workspace = get_workspace_membership(
            self.db,
            self.user,
            self.workspace.id,
        )

        self.assertEqual(membership.role, "owner")
        self.assertEqual(workspace.id, self.workspace.id)

    def test_cross_workspace_access_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            get_workspace_membership(
                self.db,
                self.user,
                self.foreign_workspace.id,
            )

        self.assertEqual(context.exception.status_code, 403)

    def test_inactive_workspace_is_rejected(self):
        self.workspace.is_active = False
        self.db.commit()

        with self.assertRaises(HTTPException) as context:
            get_workspace_membership(
                self.db,
                self.user,
                self.workspace.id,
            )

        self.assertEqual(context.exception.status_code, 404)

    def test_owner_role_is_authorized(self):
        require_workspace_roles(self.membership, {"owner", "admin"})

    def test_member_cannot_use_owner_only_permission(self):
        self.membership.role = "member"

        with self.assertRaises(HTTPException) as context:
            require_workspace_roles(self.membership, {"owner", "admin"})

        self.assertEqual(context.exception.status_code, 403)

    def test_invalid_role_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            require_workspace_roles(self.membership, {"superuser"})


if __name__ == "__main__":
    unittest.main()
