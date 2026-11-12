import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.connectors import ConnectorRecord
from app.connectors.persistence import persist_connector_records
from app.database import Base
from app.models import DiscoveryRun, SearchJob, SearchSource, SourceRecord, Workspace


class TestConnectorPersistence(unittest.TestCase):

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
            name="Persistence Workspace",
            slug="persistence-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.other_workspace = Workspace(
            name="Other Persistence Workspace",
            slug="other-persistence-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.db.add_all([self.workspace, self.other_workspace])
        self.db.flush()

        self.source = SearchSource(
            workspace_id=self.workspace.id,
            source_key="test_public",
            display_name="Test Public Source",
            source_type="rss",
            access_policy="public_only",
            enabled=True,
            config_json={},
        )
        self.db.add(self.source)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def make_record(self, **kwargs):
        values = {
            "source_url": "https://example.test/business/1",
            "title": "New Business",
            "excerpt": "A new shop opened in Barasat.",
            "attribution": "Example public source",
            "raw_data": {"category": "retail"},
        }
        values.update(kwargs)
        return ConnectorRecord(**values)

    def persist(self, records, **kwargs):
        args = {
            "db": self.db,
            "records": records,
            "workspace_id": self.workspace.id,
            "search_source_id": self.source.id,
        }
        args.update(kwargs)
        return persist_connector_records(**args)

    def test_persists_source_record(self):
        result = self.persist([self.make_record()])
        self.assertEqual(result["created"], 1)

        row = self.db.scalar(select(SourceRecord))
        self.assertEqual(row.workspace_id, self.workspace.id)
        self.assertEqual(row.title, "New Business")
        self.assertEqual(row.attribution, "Example public source")
        self.assertEqual(row.raw_data_json["category"], "retail")

    def test_duplicate_is_skipped(self):
        record = self.make_record()
        first = self.persist([record])
        second = self.persist([record])

        self.assertEqual(first["created"], 1)
        self.assertEqual(second["created"], 0)
        self.assertEqual(second["duplicates_skipped"], 1)
        self.assertEqual(len(self.db.scalars(select(SourceRecord)).all()), 1)

    def test_url_fragment_does_not_create_duplicate(self):
        first = self.make_record(
            source_url="https://example.test/business/1#section"
        )
        second = self.make_record(
            source_url="https://EXAMPLE.test/business/1"
        )
        self.persist([first])
        result = self.persist([second])
        self.assertEqual(result["duplicates_skipped"], 1)

    def test_different_content_is_preserved(self):
        first = self.make_record()
        second = self.make_record(excerpt="A different public description.")
        result = self.persist([first, second])
        self.assertEqual(result["created"], 2)

    def test_cross_workspace_source_rejected(self):
        other_source = SearchSource(
            workspace_id=self.other_workspace.id,
            source_key="other_public",
            display_name="Other Public Source",
            source_type="rss",
            access_policy="public_only",
            enabled=True,
            config_json={},
        )
        self.db.add(other_source)
        self.db.flush()

        with self.assertRaisesRegex(ValueError, "different workspace"):
            self.persist(
                [self.make_record()],
                search_source_id=other_source.id,
            )

    def test_missing_source_rejected(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.persist(
                [self.make_record()],
                search_source_id="missing-source",
            )

    def test_invalid_record_list_rejected(self):
        with self.assertRaises(TypeError):
            self.persist(["not-a-record"])

    def test_non_json_raw_data_rejected(self):
        record = self.make_record(raw_data={"invalid": object()})
        with self.assertRaisesRegex(ValueError, "JSON-compatible"):
            self.persist([record])

    def test_oversized_raw_data_rejected(self):
        record = self.make_record(raw_data={"large": "x" * 50001})
        with self.assertRaisesRegex(ValueError, "50000 bytes"):
            self.persist([record])

    def test_collection_does_not_commit(self):
        self.db.commit()
        self.db.begin()
        self.persist([self.make_record()])
        self.assertTrue(self.db.in_transaction())
        self.db.rollback()

        rows = self.db.scalars(select(SourceRecord)).all()
        self.assertEqual(len(rows), 0)

    def test_empty_batch_is_valid(self):
        result = self.persist([])
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["total_received"], 0)


    def test_duplicate_within_same_batch_is_skipped(self):
        record = self.make_record()
        result = self.persist([record, record])

        self.assertEqual(result["created"], 1)
        self.assertEqual(result["duplicates_skipped"], 1)
        self.assertEqual(len(self.db.scalars(select(SourceRecord)).all()), 1)

    def test_discovery_run_with_cross_workspace_job_rejected(self):
        other_job = SearchJob(
            workspace_id=self.other_workspace.id,
            query="Other workspace query",
            location="Barasat",
            status="queued",
        )
        self.db.add(other_job)
        self.db.flush()

        run = DiscoveryRun(
            workspace_id=self.workspace.id,
            search_job_id=other_job.id,
            status="pending",
        )
        self.db.add(run)
        self.db.flush()

        with self.assertRaisesRegex(ValueError, "different workspace"):
            self.persist(
                [self.make_record()],
                discovery_run_id=run.id,
            )

    def test_invalid_later_record_adds_no_partial_rows(self):
        valid = self.make_record()
        invalid = self.make_record(
            source_url="https://example.test/business/2",
            raw_data={"invalid": object()},
        )

        with self.assertRaisesRegex(ValueError, "JSON-compatible"):
            self.persist([valid, invalid])

        pending_records = [
            item for item in self.db.new
            if isinstance(item, SourceRecord)
        ]
        self.assertEqual(pending_records, [])


if __name__ == "__main__":
    unittest.main()
