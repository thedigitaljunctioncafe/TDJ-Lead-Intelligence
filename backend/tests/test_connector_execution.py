import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.connectors import ConnectorContext, ConnectorRecord, ConnectorRegistry, RateLimiter, SourceConnector
from app.connectors.execution import execute_discovery_job
from app.database import Base
from app.models import (
    Workspace,
    SearchSource,
    SearchJob,
    SearchJobSource,
    DiscoveryRun,
    SourceRecord,
    IntelligenceResult,
)


class CafeConnector(SourceConnector):
    connector_key = "mock_cafe"
    source_type = "mock"

    def collect(self, context):
        return [
            ConnectorRecord(
                source_url="https://example.test/new-cafe",
                title="New cafe opened in Barasat",
                excerpt="A new cafe has opened in Barasat. The owner needs GST registration.",
                external_id="cafe-001",
                attribution="Mock public test source",
            )
        ]


class FailingConnector(SourceConnector):
    connector_key = "mock_failure"
    source_type = "mock"

    def collect(self, context):
        raise RuntimeError("Mock connector failure")


class TestConnectorExecution(unittest.TestCase):
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
            name="Execution Test Workspace",
            slug="execution-test-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.db.add(self.workspace)
        self.db.flush()

        self.job = SearchJob(
            workspace_id=self.workspace.id,
            query="new cafe Barasat",
            location="Barasat",
            status="queued",
        )
        self.db.add(self.job)

        self.good_source = SearchSource(
            workspace_id=self.workspace.id,
            source_key="mock_cafe",
            display_name="Mock Cafe Source",
            source_type="mock",
            access_policy="public_only",
            enabled=True,
            config_json={"test_setting": "preserved"},
        )
        self.db.add(self.good_source)
        self.db.flush()

        self.db.add(
            SearchJobSource(
                search_job_id=self.job.id,
                search_source_id=self.good_source.id,
            )
        )
        self.db.commit()

        self.registry = ConnectorRegistry()
        self.registry.register(CafeConnector())
        self.registry.register(FailingConnector())
        self.limiter = RateLimiter(600)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def add_failing_source(self):
        source = SearchSource(
            workspace_id=self.workspace.id,
            source_key="mock_failure",
            display_name="Mock Failing Source",
            source_type="mock",
            access_policy="public_only",
            enabled=True,
            config_json={},
        )
        self.db.add(source)
        self.db.flush()
        self.db.add(
            SearchJobSource(
                search_job_id=self.job.id,
                search_source_id=source.id,
            )
        )
        self.db.flush()
        return source

    def test_successful_execution_persists_and_analyzes_record(self):
        result = execute_discovery_job(
            self.db, self.job.id, self.registry, self.limiter
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["records_seen"], 1)
        self.assertEqual(result["records_created"], 1)
        self.assertEqual(result["records_analyzed"], 1)

        self.assertEqual(self.db.query(SourceRecord).count(), 1)
        self.assertGreater(self.db.query(IntelligenceResult).count(), 0)
        self.assertEqual(self.db.query(DiscoveryRun).count(), 1)

    def test_duplicate_record_is_not_analyzed_twice(self):
        first = execute_discovery_job(
            self.db, self.job.id, self.registry, self.limiter
        )
        self.db.commit()

        second = execute_discovery_job(
            self.db, self.job.id, self.registry, self.limiter
        )

        self.assertEqual(first["records_created"], 1)
        self.assertEqual(second["records_created"], 0)
        self.assertEqual(second["records_analyzed"], 0)
        self.assertEqual(self.db.query(SourceRecord).count(), 1)

    def test_one_source_failure_produces_partial_result(self):
        self.add_failing_source()

        result = execute_discovery_job(
            self.db, self.job.id, self.registry, self.limiter
        )

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["records_created"], 1)
        self.assertTrue(result["error_summary"])
        self.assertEqual(self.db.query(SourceRecord).count(), 1)

    def test_execution_does_not_commit_transaction(self):
        self.db.commit()
        self.db.begin()

        result = execute_discovery_job(
            self.db, self.job.id, self.registry, self.limiter
        )

        self.assertEqual(result["records_created"], 1)
        self.assertTrue(self.db.in_transaction())

        self.db.rollback()
        self.assertEqual(self.db.query(SourceRecord).count(), 0)

    def test_error_summary_does_not_expose_raw_exception_message(self):
        self.add_failing_source()

        result = execute_discovery_job(
            self.db, self.job.id, self.registry, self.limiter
        )

        self.assertIn("RuntimeError", result["error_summary"])
        self.assertNotIn("Mock connector failure", result["error_summary"])
        self.assertIn("source processing failed", result["error_summary"])

    def test_records_seen_is_counted_when_analysis_fails(self):
        from unittest.mock import patch

        with patch(
            "app.connectors.execution.analyze_source_record",
            side_effect=RuntimeError("private diagnostic"),
        ):
            result = execute_discovery_job(
                self.db, self.job.id, self.registry, self.limiter
            )

        self.assertEqual(result["records_seen"], 1)
        self.assertEqual(result["records_created"], 0)
        self.assertEqual(result["records_analyzed"], 0)
        self.assertNotIn("private diagnostic", result["error_summary"])

    def test_job_without_sources_is_rejected(self):
        empty_job = SearchJob(
            workspace_id=self.workspace.id,
            query="new shops",
            location="Barasat",
            status="queued",
        )
        self.db.add(empty_job)
        self.db.flush()

        with self.assertRaises(ValueError):
            execute_discovery_job(
                self.db, empty_job.id, self.registry, self.limiter
            )

        self.assertEqual(
            self.db.query(DiscoveryRun)
            .filter_by(search_job_id=empty_job.id)
            .count(),
            0,
        )


if __name__ == "__main__":
    unittest.main()
