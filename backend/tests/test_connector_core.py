import unittest
from datetime import datetime, timezone

from app.connectors import (
    ConnectorContext,
    ConnectorRecord,
    ConnectorRegistry,
    RateLimiter,
    SourceConnector,
)


class ExampleConnector(SourceConnector):
    connector_key = "example_public"
    source_type = "test"

    def collect(self, context):
        return [
            ConnectorRecord(
                source_url="https://example.test/business/1",
                title="Example Business",
                excerpt=f"Search: {context.query}",
                attribution="Example public source",
            )
        ]


class TestConnectorCore(unittest.TestCase):

    def test_valid_context(self):
        context = ConnectorContext("workspace-1", "new shops", "Barasat")
        self.assertEqual(context.query, "new shops")

    def test_empty_workspace_rejected(self):
        with self.assertRaises(ValueError):
            ConnectorContext("", "new shops")

    def test_empty_query_rejected(self):
        with self.assertRaises(ValueError):
            ConnectorContext("workspace-1", " ")

    def test_valid_record(self):
        record = ConnectorRecord(
            source_url="https://example.test/item",
            title="Example",
            published_at=datetime.now(timezone.utc),
        )
        self.assertEqual(record.title, "Example")

    def test_invalid_record_url_rejected(self):
        with self.assertRaises(ValueError):
            ConnectorRecord(source_url="javascript:alert(1)")

    def test_record_excerpt_limit(self):
        with self.assertRaises(ValueError):
            ConnectorRecord(
                source_url="https://example.test",
                excerpt="x" * 20001,
            )

    def test_registry_register_and_get(self):
        registry = ConnectorRegistry()
        connector = ExampleConnector()
        registry.register(connector)
        self.assertIs(registry.get("example_public"), connector)

    def test_registry_duplicate_rejected(self):
        registry = ConnectorRegistry()
        registry.register(ExampleConnector())
        with self.assertRaises(ValueError):
            registry.register(ExampleConnector())

    def test_connector_collect_contract(self):
        connector = ExampleConnector()
        context = ConnectorContext("workspace-1", "GST registration")
        records = list(connector.collect(context))
        self.assertEqual(len(records), 1)
        self.assertIn("GST registration", records[0].excerpt)

    def test_rate_limiter_validation_and_reset(self):
        limiter = RateLimiter(60)
        self.assertEqual(limiter.acquire("example"), 0.0)
        limiter.reset("example")
        self.assertEqual(limiter.acquire("example"), 0.0)
        with self.assertRaises(ValueError):
            RateLimiter(0)


if __name__ == "__main__":
    unittest.main()
