import socket
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    SearchSource,
    User,
    Workspace,
    WorkspaceDomainAllowlist,
    WorkspaceMembership,
)
from app.connectors.workspace_transport import request_search_source_https


FEED_URL = "https://feeds.example.org/rss"


def public_resolver(host, port, type):
    return [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))
    ]


class TestWorkspaceTransport(unittest.TestCase):
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
            name="Transport Workspace",
            slug="transport-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.user = User(
            email="transport@example.org",
            display_name="Transport Admin",
            is_active=True,
        )
        self.db.add_all([self.workspace, self.user])
        self.db.flush()

        self.db.add(
            WorkspaceMembership(
                workspace_id=self.workspace.id,
                user_id=self.user.id,
                role="owner",
            )
        )

        self.source = SearchSource(
            workspace_id=self.workspace.id,
            source_key="approved_feed",
            display_name="Approved Feed",
            source_type="rss",
            access_policy="public_only",
            enabled=True,
            config_json={"feed_url": FEED_URL},
        )
        self.db.add(self.source)
        self.db.add(
            WorkspaceDomainAllowlist(
                workspace_id=self.workspace.id,
                domain="feeds.example.org",
                is_active=True,
                approved_by_user_id=self.user.id,
            )
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    @patch("app.connectors.workspace_transport.request_public_https")
    def test_approved_feed_uses_pinned_transport(self, transport):
        transport.return_value = {"status": 200, "body": b"<rss/>"}

        result = request_search_source_https(
            self.db,
            self.source.id,
            FEED_URL,
            resolver=public_resolver,
        )

        self.assertEqual(result["status"], 200)
        transport.assert_called_once_with(
            FEED_URL,
            ["feeds.example.org"],
            resolver=public_resolver,
            timeout=10,
            max_response_bytes=2_000_000,
        )

    @patch("app.connectors.workspace_transport.request_public_https")
    def test_unapproved_domain_is_rejected_before_transport(self, transport):
        unapproved_url = "https://other.example.org/rss"
        self.source.config_json = {"feed_url": unapproved_url}
        self.db.flush()

        with self.assertRaisesRegex(ValueError, "not actively approved"):
            request_search_source_https(
                self.db,
                self.source.id,
                unapproved_url,
                resolver=public_resolver,
            )
        transport.assert_not_called()

    @patch("app.connectors.workspace_transport.request_public_https")
    def test_revoked_domain_is_rejected(self, transport):
        entry = self.db.query(WorkspaceDomainAllowlist).one()
        entry.is_active = False
        self.db.flush()

        with self.assertRaisesRegex(ValueError, "not actively approved"):
            request_search_source_https(
                self.db,
                self.source.id,
                FEED_URL,
                resolver=public_resolver,
            )
        transport.assert_not_called()

    @patch("app.connectors.workspace_transport.request_public_https")
    def test_disabled_source_is_rejected(self, transport):
        self.source.enabled = False
        self.db.flush()

        with self.assertRaisesRegex(ValueError, "disabled"):
            request_search_source_https(self.db, self.source.id, FEED_URL)
        transport.assert_not_called()

    @patch("app.connectors.workspace_transport.request_public_https")
    def test_non_public_source_is_rejected(self, transport):
        self.source.access_policy = "authenticated"
        self.db.flush()

        with self.assertRaisesRegex(ValueError, "public_only"):
            request_search_source_https(self.db, self.source.id, FEED_URL)
        transport.assert_not_called()

    @patch("app.connectors.workspace_transport.request_public_https")
    def test_unconfigured_feed_is_rejected(self, transport):
        self.source.config_json = {}
        self.db.flush()

        with self.assertRaisesRegex(ValueError, "configured feed_url"):
            request_search_source_https(self.db, self.source.id, FEED_URL)
        transport.assert_not_called()

    @patch("app.connectors.workspace_transport.request_public_https")
    def test_url_must_match_exact_configured_feed(self, transport):
        with self.assertRaisesRegex(ValueError, "does not match"):
            request_search_source_https(
                self.db,
                self.source.id,
                "https://feeds.example.org/another-path",
            )
        transport.assert_not_called()

    @patch("app.connectors.workspace_transport.request_public_https")
    def test_non_rss_source_type_is_rejected(self, transport):
        self.source.source_type = "directory"
        self.db.flush()

        with self.assertRaisesRegex(ValueError, "RSS and Atom"):
            request_search_source_https(self.db, self.source.id, FEED_URL)
        transport.assert_not_called()

    @patch("app.connectors.workspace_transport.request_public_https")
    def test_inactive_workspace_is_rejected(self, transport):
        self.workspace.is_active = False
        self.db.flush()

        with self.assertRaisesRegex(ValueError, "inactive"):
            request_search_source_https(self.db, self.source.id, FEED_URL)
        transport.assert_not_called()

    @patch("app.connectors.workspace_transport.request_public_https")
    def test_transport_does_not_commit_database_changes(self, transport):
        transport.return_value = {"status": 200, "body": b"<rss/>"}
        self.db.commit()
        self.db.begin()

        request_search_source_https(
            self.db,
            self.source.id,
            FEED_URL,
            resolver=public_resolver,
        )

        self.assertTrue(self.db.in_transaction())
        self.db.rollback()


if __name__ == "__main__":
    unittest.main()
