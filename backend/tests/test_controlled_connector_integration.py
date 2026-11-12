import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Workspace, User, SearchSource, WorkspaceDomainAllowlist
from app.connectors.base import (
    ConnectorContext,
    ConnectorRecord,
    ControlledNetworkConnector,
)
from app.connectors.registry import ConnectorRegistry
from app.connectors.rate_limit import RateLimiter
from app.connectors.service import collect_from_search_source


FEED_URL = "https://feeds.example.org/rss"


class TestControlledConnector(ControlledNetworkConnector):
    connector_key = "controlled_test"
    source_type = "rss"

    def collect(self, context):
        response = context.fetcher(context.config["feed_url"])
        return [
            ConnectorRecord(
                source_url=FEED_URL,
                title="Controlled feed result",
                excerpt=f"HTTP status: {response['status']}",
            )
        ]


class TestControlledConnectorIntegration(unittest.TestCase):
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
            name="Controlled Test Workspace",
            slug="controlled-test-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.user = User(
            email="controlled@example.org",
            display_name="Controlled Test",
            is_active=True,
        )
        self.db.add_all([self.workspace, self.user])
        self.db.flush()

        self.source = SearchSource(
            workspace_id=self.workspace.id,
            source_key="controlled_test",
            display_name="Controlled RSS",
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

        self.registry = ConnectorRegistry()
        self.registry.register(TestControlledConnector())
        self.limiter = RateLimiter(600)
        self.context = ConnectorContext(
            workspace_id=self.workspace.id,
            query="new businesses",
            location="Barasat",
            config={"feed_url": FEED_URL},
        )

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    @patch("app.connectors.workspace_transport.request_public_https")
    def test_controlled_connector_receives_approved_fetcher(self, transport):
        transport.return_value = {"status": 200, "body": b"<rss/>"}

        result = collect_from_search_source(
            db=self.db,
            source_id=self.source.id,
            context=self.context,
            registry=self.registry,
            rate_limiter=self.limiter,
        )

        self.assertEqual(result["records_seen"], 1)
        self.assertIn("HTTP status: 200", result["records"][0].excerpt)
        transport.assert_called_once()

    @patch("app.connectors.workspace_transport.request_public_https")
    def test_unapproved_feed_is_blocked(self, transport):
        self.source.config_json = {
            "feed_url": "https://other.example.org/rss"
        }
        self.context = ConnectorContext(
            workspace_id=self.workspace.id,
            query="new businesses",
            config={"feed_url": "https://other.example.org/rss"},
        )

        with self.assertRaisesRegex(ValueError, "not actively approved"):
            collect_from_search_source(
                db=self.db,
                source_id=self.source.id,
                context=self.context,
                registry=self.registry,
                rate_limiter=self.limiter,
            )

        transport.assert_not_called()

    def test_controlled_connector_requires_feed_url(self):
        self.source.config_json = {}
        self.db.flush()

        with self.assertRaisesRegex(ValueError, "configured feed_url"):
            collect_from_search_source(
                db=self.db,
                source_id=self.source.id,
                context=self.context,
                registry=self.registry,
                rate_limiter=self.limiter,
            )

    def test_controlled_connector_rejects_non_rss_source(self):
        self.source.source_type = "directory"
        self.db.flush()

        directory_connector = TestControlledConnector()
        directory_connector.source_type = "directory"

        directory_registry = ConnectorRegistry()
        directory_registry.register(directory_connector)

        with self.assertRaisesRegex(ValueError, "RSS and Atom"):
            collect_from_search_source(
                db=self.db,
                source_id=self.source.id,
                context=self.context,
                registry=directory_registry,
                rate_limiter=self.limiter,
            )


if __name__ == "__main__":
    unittest.main()
