import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    Workspace,
    User,
    WorkspaceDomainAllowlist,
    SearchJob,
    SearchJobSource,
    SearchSource,
    DiscoveryRun,
    SourceRecord,
    IntelligenceResult,
)
from app.connectors.base import (
    ConnectorRecord,
    ControlledNetworkConnector,
)
from app.connectors.registry import ConnectorRegistry
from app.connectors.rate_limit import RateLimiter
from app.connectors.execution import execute_discovery_job
from app.connectors import workspace_transport


FEED_URL = "https://feeds.example.org/rss"


class ExecutionTestConnector(ControlledNetworkConnector):
    connector_key = "execution_controlled"
    source_type = "rss"

    def collect(self, context):
        response = context.fetcher(context.config["feed_url"])
        return [
            ConnectorRecord(
                source_url=FEED_URL,
                title="New business discovered through controlled feed",
                excerpt=(
                    "A new retail shop has opened in Barasat. "
                    f"Feed response status: {response['status']}"
                ),
                external_id="controlled-execution-001",
                attribution="Controlled execution test feed",
            )
        ]


class TestControlledExecution(unittest.TestCase):
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
            name="Execution Workspace",
            slug="execution-workspace-controlled",
            workspace_type="organization",
            is_active=True,
        )
        self.user = User(
            email="execution-controlled@example.org",
            display_name="Execution Test",
            is_active=True,
        )
        self.db.add_all([self.workspace, self.user])
        self.db.flush()

        self.job = SearchJob(
            workspace_id=self.workspace.id,
            query="new retail shops",
            location="Barasat",
            status="queued",
        )
        self.source = SearchSource(
            workspace_id=self.workspace.id,
            source_key="execution_controlled",
            display_name="Controlled RSS Execution Source",
            source_type="rss",
            access_policy="public_only",
            enabled=True,
            config_json={"feed_url": FEED_URL},
        )
        self.db.add_all([self.job, self.source])
        self.db.flush()

        self.db.add_all([
            SearchJobSource(
                search_job_id=self.job.id,
                search_source_id=self.source.id,
            ),
            WorkspaceDomainAllowlist(
                workspace_id=self.workspace.id,
                domain="feeds.example.org",
                is_active=True,
                approved_by_user_id=self.user.id,
            ),
        ])
        self.db.commit()

        self.registry = ConnectorRegistry()
        self.registry.register(ExecutionTestConnector())
        self.limiter = RateLimiter(600)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    @patch.object(workspace_transport, "request_public_https")
    def test_full_execution_uses_controlled_transport(self, transport):
        transport.return_value = {
            "status": 200,
            "body": b"<rss><channel></channel></rss>",
        }

        result = execute_discovery_job(
            db=self.db,
            search_job_id=self.job.id,
            registry=self.registry,
            rate_limiter=self.limiter,
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["records_seen"], 1)
        self.assertEqual(result["records_created"], 1)
        self.assertEqual(result["records_analyzed"], 1)

        self.assertEqual(self.db.query(SourceRecord).count(), 1)
        self.assertGreater(
            self.db.query(IntelligenceResult).count(),
            0,
        )
        self.assertEqual(self.db.query(DiscoveryRun).count(), 1)
        transport.assert_called_once()

    @patch.object(workspace_transport, "request_public_https")
    def test_unapproved_domain_fails_execution_safely(self, transport):
        self.source.config_json = {
            "feed_url": "https://unapproved.example.org/rss"
        }
        self.db.flush()

        result = execute_discovery_job(
            db=self.db,
            search_job_id=self.job.id,
            registry=self.registry,
            rate_limiter=self.limiter,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["records_created"], 0)
        self.assertEqual(self.db.query(SourceRecord).count(), 0)
        self.assertIn("ValueError", result["error_summary"])
        self.assertNotIn("unapproved.example.org", result["error_summary"])
        transport.assert_not_called()


if __name__ == "__main__":
    unittest.main()
