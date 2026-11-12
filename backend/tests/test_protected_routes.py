import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.auth_service import hash_password
from app.login_rate_limit import login_rate_limiter
from app.models import (
    Base,
    User,
    Workspace,
    WorkspaceMembership,
    SearchJob,
)


class ProtectedAPITests(unittest.TestCase):
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

        self.workspace_a = Workspace(
            name="Workspace A",
            slug="workspace-a",
            workspace_type="organization",
            is_active=True,
        )
        self.workspace_b = Workspace(
            name="Workspace B",
            slug="workspace-b",
            workspace_type="organization",
            is_active=True,
        )

        self.owner = User(
            email="owner@test.example",
            display_name="Owner",
            is_active=True,
            password_hash=hash_password("Owner-Test-Password-2026!"),
        )
        self.member = User(
            email="member@test.example",
            display_name="Member",
            is_active=True,
            password_hash=hash_password("Member-Test-Password-2026!"),
        )

        self.db.add_all([
            self.workspace_a,
            self.workspace_b,
            self.owner,
            self.member,
        ])
        self.db.flush()

        self.db.add_all([
            WorkspaceMembership(
                workspace_id=self.workspace_a.id,
                user_id=self.owner.id,
                role="owner",
            ),
            WorkspaceMembership(
                workspace_id=self.workspace_a.id,
                user_id=self.member.id,
                role="member",
            ),
        ])

        self.job_a = SearchJob(
            workspace_id=self.workspace_a.id,
            query="Workspace A search",
            location="Barasat",
            status="queued",
        )
        self.job_b = SearchJob(
            workspace_id=self.workspace_b.id,
            query="Workspace B private search",
            location="Kolkata",
            status="queued",
        )
        self.db.add_all([self.job_a, self.job_b])
        self.db.commit()

        self.workspace_a_id = self.workspace_a.id
        self.workspace_b_id = self.workspace_b.id
        self.owner_id = self.owner.id

        def override_get_db():
            session = self.TestSession()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_get_db
        login_rate_limiter.clear()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        login_rate_limiter.clear()

    def login(self, email, password):
        return self.client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )

    def test_workspace_list_contains_only_memberships(self):
        response = self.login(
            "owner@test.example",
            "Owner-Test-Password-2026!",
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/workspaces")
        self.assertEqual(response.status_code, 200)

        workspace_ids = {item["id"] for item in response.json()}
        self.assertEqual(workspace_ids, {self.workspace_a_id})

    def test_search_jobs_are_workspace_scoped(self):
        self.login("owner@test.example", "Owner-Test-Password-2026!")

        response = self.client.get(
            "/api/search-jobs",
            params={"workspace_id": self.workspace_a_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(
            response.json()[0]["query"],
            "Workspace A search",
        )

    def test_cross_workspace_search_read_is_rejected(self):
        self.login("owner@test.example", "Owner-Test-Password-2026!")

        response = self.client.get(
            "/api/search-jobs",
            params={"workspace_id": self.workspace_b_id},
        )
        self.assertEqual(response.status_code, 403)

    def test_cross_workspace_search_creation_is_rejected(self):
        self.login("owner@test.example", "Owner-Test-Password-2026!")

        response = self.client.post(
            "/api/search-jobs",
            json={
                "query": "Unauthorized workspace search",
                "location": "Kolkata",
                "workspace_id": self.workspace_b_id,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_created_job_records_requesting_user(self):
        self.login("owner@test.example", "Owner-Test-Password-2026!")

        response = self.client.post(
            "/api/search-jobs",
            json={
                "query": "New authorized search",
                "location": "Barasat",
                "workspace_id": self.workspace_a_id,
            },
        )

        self.assertEqual(response.status_code, 201)

        with self.TestSession() as db:
            job = db.scalar(
                select(SearchJob).where(
                    SearchJob.query == "New authorized search"
                )
            )
            self.assertIsNotNone(job)
            self.assertEqual(job.requested_by_user_id, self.owner_id)

    def test_member_cannot_access_admin_summary(self):
        self.login("member@test.example", "Member-Test-Password-2026!")

        response = self.client.get(
            "/api/admin/database-summary",
            params={"workspace_id": self.workspace_a_id},
        )
        self.assertEqual(response.status_code, 403)

    def test_owner_summary_is_workspace_scoped(self):
        self.login("owner@test.example", "Owner-Test-Password-2026!")

        response = self.client.get(
            "/api/admin/database-summary",
            params={"workspace_id": self.workspace_a_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["workspace_count"], 1)
        self.assertEqual(response.json()["search_job_count"], 1)


def tearDownModule():
    from app.database import engine as application_engine
    application_engine.dispose()


if __name__ == "__main__":
    unittest.main(verbosity=2)
