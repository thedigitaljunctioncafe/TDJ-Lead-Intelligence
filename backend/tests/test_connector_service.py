import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.connectors import (
    ConnectorContext,
    ConnectorRecord,
    ConnectorRegistry,
    RateLimiter,
    SourceConnector,
)
from app.connectors.service import collect_from_search_source
from app.database import Base
from app.models import SearchSource, Workspace


class ExampleConnector(SourceConnector):
    connector_key = "example_public"
    source_type = "mock"

    def collect(self, context):
        return [
            ConnectorRecord(
                source_url=f"https://example.test/item/{i}",
                title=f"Item {i}",
                excerpt=f"Public listing for {context.query}",
            )
            for i in range(5)
        ]


class UncontrolledRSSConnector(ExampleConnector):
    connector_key = "uncontrolled_rss"
    source_type = "rss"


class WrongTypeConnector(ExampleConnector):
    source_type = "directory"


class InvalidOutputConnector(SourceConnector):
    connector_key = "invalid_output"
    source_type = "mock"

    def collect(self, context):
        return ["not-a-ConnectorRecord"]


class TestConnectorService(unittest.TestCase):

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
            name="Connector Workspace",
            slug="connector-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.other_workspace = Workspace(
            name="Other Connector Workspace",
            slug="other-connector-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.db.add_all([self.workspace, self.other_workspace])
        self.db.flush()

        self.source = SearchSource(
            workspace_id=self.workspace.id,
            source_key="example_public",
            display_name="Example Public Source",
            source_type="mock",
            access_policy="public_only",
            enabled=True,
            config_json={},
        )
        self.db.add(self.source)
        self.db.commit()

        self.registry = ConnectorRegistry()
        self.registry.register(ExampleConnector())
        self.limiter = RateLimiter(600)
        self.context = ConnectorContext(
            workspace_id=self.workspace.id,
            query="new retail shops",
            location="Barasat",
        )

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def collect(self, **kwargs):
        arguments = {
            "db": self.db,
            "source_id": self.source.id,
            "context": self.context,
            "registry": self.registry,
            "rate_limiter": self.limiter,
        }
        arguments.update(kwargs)
        return collect_from_search_source(**arguments)

    def test_collects_registered_public_source(self):
        result = self.collect()
        self.assertEqual(result["source_id"], self.source.id)
        self.assertEqual(result["records_seen"], 5)
        self.assertTrue(
            all(isinstance(item, ConnectorRecord) for item in result["records"])
        )

    def test_uncontrolled_rss_connector_is_rejected(self):
        source = SearchSource(
            workspace_id=self.workspace.id,
            source_key="uncontrolled_rss",
            display_name="Uncontrolled RSS",
            source_type="rss",
            access_policy="public_only",
            enabled=True,
            config_json={},
        )
        self.db.add(source)
        self.db.flush()

        registry = ConnectorRegistry()
        registry.register(UncontrolledRSSConnector())

        with self.assertRaisesRegex(ValueError, "mock sources"):
            self.collect(source_id=source.id, registry=registry)

    def test_record_limit_is_respected(self):
        result = self.collect(max_records=2)
        self.assertEqual(result["records_seen"], 2)

    def test_disabled_source_is_rejected(self):
        self.source.enabled = False
        self.db.flush()
        with self.assertRaisesRegex(ValueError, "disabled"):
            self.collect()

    def test_private_policy_is_rejected(self):
        self.source.access_policy = "authenticated"
        self.db.flush()
        with self.assertRaisesRegex(ValueError, "public_only"):
            self.collect()

    def test_cross_workspace_source_is_rejected(self):
        context = ConnectorContext(
            workspace_id=self.other_workspace.id,
            query="new shops",
        )
        with self.assertRaisesRegex(ValueError, "different workspace"):
            self.collect(context=context)

    def test_missing_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.collect(source_id="missing-source")

    def test_unregistered_connector_is_rejected(self):
        self.source.source_key = "not_registered"
        self.db.flush()
        with self.assertRaisesRegex(KeyError, "not_registered"):
            self.collect()

    def test_connector_type_mismatch_is_rejected(self):
        registry = ConnectorRegistry()
        registry.register(WrongTypeConnector())
        with self.assertRaisesRegex(ValueError, "source_type"):
            self.collect(registry=registry)

    def test_invalid_connector_output_is_rejected(self):
        source = SearchSource(
            workspace_id=self.workspace.id,
            source_key="invalid_output",
            display_name="Invalid Output",
            source_type="mock",
            access_policy="public_only",
            enabled=True,
            config_json={},
        )
        self.db.add(source)
        self.db.flush()

        registry = ConnectorRegistry()
        registry.register(InvalidOutputConnector())

        with self.assertRaisesRegex(TypeError, "invalid record"):
            self.collect(source_id=source.id, registry=registry)

    def test_record_limit_validation(self):
        with self.assertRaises(ValueError):
            self.collect(max_records=0)
        with self.assertRaises(ValueError):
            self.collect(max_records=501)

    def test_collection_does_not_commit(self):
        self.db.commit()

        # Explicitly begin a transaction so a commit by the service
        # would be observable in this test.
        self.db.begin()
        self.assertTrue(self.db.in_transaction())

        self.collect()

        self.assertTrue(self.db.in_transaction())
        self.db.rollback()


if __name__ == "__main__":
    unittest.main()
