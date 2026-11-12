import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    User,
    Workspace,
    WorkspaceMembership,
    WorkspaceDomainAllowlist,
)
from app.domain_allowlist_service import (
    approve_domain,
    revoke_domain,
    list_approved_domains,
    normalize_domain,
)


class DomainAllowlistServiceTests(unittest.TestCase):
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
            name="Test Workspace",
            slug="allowlist-test",
            is_active=True,
        )
        self.other_workspace = Workspace(
            name="Other Workspace",
            slug="allowlist-other",
            is_active=True,
        )
        self.owner = User(
            email="owner@allowlist.test",
            display_name="Owner",
            is_active=True,
        )
        self.member = User(
            email="member@allowlist.test",
            display_name="Member",
            is_active=True,
        )

        self.db.add_all([
            self.workspace, self.other_workspace, self.owner, self.member
        ])
        self.db.flush()

        self.db.add_all([
            WorkspaceMembership(
                workspace_id=self.workspace.id,
                user_id=self.owner.id,
                role="owner",
            ),
            WorkspaceMembership(
                workspace_id=self.workspace.id,
                user_id=self.member.id,
                role="member",
            ),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_normalizes_case_and_trailing_dot(self):
        self.assertEqual(
            normalize_domain("  Feeds.Example.ORG. "),
            "feeds.example.org",
        )

    def test_normalizes_international_domain(self):
        result = normalize_domain("b\u00fccher.de")
        self.assertEqual(result, "xn--bcher-kva.de")

    def test_rejects_url_and_path(self):
        for value in [
            "https://feeds.example.org",
            "feeds.example.org/path",
            "feeds.example.org:443",
            "*.example.org",
        ]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_domain(value)

    def test_rejects_local_reserved_and_ip_domains(self):
        for value in [
            "localhost",
            "host.local",
            "host.internal",
            "host.example",
            "192.168.1.1",
            "127.0.0.1",
        ]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_domain(value)

    def test_rejects_invalid_dns_labels(self):
        for value in [
            "-bad.example.org",
            "bad-.example.org",
            "bad..example.org",
            "bad_label.example.org",
            "a" * 64 + ".org",
        ]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_domain(value)

    def test_owner_can_approve_domain(self):
        entry = approve_domain(
            self.db, self.workspace.id, "FEEDS.Example.org",
            self.owner.id,
        )
        self.db.commit()

        self.assertEqual(entry.domain, "feeds.example.org")
        self.assertTrue(entry.is_active)
        self.assertEqual(entry.approved_by_user_id, self.owner.id)

    def test_admin_can_approve_domain(self):
        admin = User(
            email="admin@allowlist.test",
            display_name="Admin",
            is_active=True,
        )
        self.db.add(admin)
        self.db.flush()
        self.db.add(WorkspaceMembership(
            workspace_id=self.workspace.id,
            user_id=admin.id,
            role="admin",
        ))
        self.db.flush()

        entry = approve_domain(
            self.db, self.workspace.id, "feeds.example.org", admin.id
        )
        self.assertTrue(entry.is_active)

    def test_member_cannot_approve_domain(self):
        with self.assertRaises(PermissionError):
            approve_domain(
                self.db, self.workspace.id,
                "feeds.example.org", self.member.id,
            )

    def test_domain_approval_is_idempotent(self):
        first = approve_domain(
            self.db, self.workspace.id,
            "feeds.example.org", self.owner.id,
        )
        second = approve_domain(
            self.db, self.workspace.id,
            "FEEDS.EXAMPLE.ORG", self.owner.id,
        )

        self.assertEqual(first.id, second.id)
        count = self.db.scalar(
            select(WorkspaceDomainAllowlist).where(
                WorkspaceDomainAllowlist.workspace_id == self.workspace.id
            )
        )
        self.assertEqual(count.id, first.id)

    def test_revoked_domain_can_be_reactivated(self):
        entry = approve_domain(
            self.db, self.workspace.id,
            "feeds.example.org", self.owner.id,
        )
        revoke_domain(
            self.db, self.workspace.id,
            "feeds.example.org", self.owner.id,
        )
        self.assertFalse(entry.is_active)
        self.assertIsNotNone(entry.revoked_at)

        reactivated = approve_domain(
            self.db, self.workspace.id,
            "feeds.example.org", self.owner.id,
        )
        self.assertEqual(entry.id, reactivated.id)
        self.assertTrue(reactivated.is_active)
        self.assertIsNone(reactivated.revoked_at)

    def test_revoke_requires_admin(self):
        approve_domain(
            self.db, self.workspace.id,
            "feeds.example.org", self.owner.id,
        )
        with self.assertRaises(PermissionError):
            revoke_domain(
                self.db, self.workspace.id,
                "feeds.example.org", self.member.id,
            )

    def test_workspace_isolation(self):
        approve_domain(
            self.db, self.workspace.id,
            "feeds.example.org", self.owner.id,
        )
        with self.assertRaises(PermissionError):
            revoke_domain(
                self.db, self.other_workspace.id,
                "feeds.example.org", self.owner.id,
            )

    def test_member_can_list_only_active_workspace_domains(self):
        approve_domain(
            self.db, self.workspace.id,
            "active.example.org", self.owner.id,
        )
        approve_domain(
            self.db, self.workspace.id,
            "revoked.example.org", self.owner.id,
        )
        revoke_domain(
            self.db, self.workspace.id,
            "revoked.example.org", self.owner.id,
        )

        results = list_approved_domains(
            self.db, self.workspace.id, self.member.id
        )
        self.assertEqual([item.domain for item in results], ["active.example.org"])

    def test_other_workspace_member_cannot_list_domains(self):
        with self.assertRaises(PermissionError):
            list_approved_domains(
                self.db, self.other_workspace.id, self.owner.id
            )

    def test_inactive_user_cannot_approve(self):
        self.owner.is_active = False
        self.db.flush()
        with self.assertRaises(PermissionError):
            approve_domain(
                self.db, self.workspace.id,
                "feeds.example.org", self.owner.id,
            )

    def test_approval_does_not_commit_transaction(self):
        approve_domain(
            self.db, self.workspace.id,
            "feeds.example.org", self.owner.id,
        )
        self.db.rollback()

        result = self.db.scalar(
            select(WorkspaceDomainAllowlist).where(
                WorkspaceDomainAllowlist.workspace_id == self.workspace.id
            )
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
