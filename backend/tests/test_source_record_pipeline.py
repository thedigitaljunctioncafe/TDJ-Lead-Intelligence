import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import IntelligenceResult, SourceRecord, Workspace
from app.source_record_pipeline import analyze_source_record


class TestSourceRecordPipeline(unittest.TestCase):

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
            name="Source Test Workspace",
            slug="source-test-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.other_workspace = Workspace(
            name="Other Source Workspace",
            slug="other-source-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.db.add_all([self.workspace, self.other_workspace])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def make_source(self, workspace, excerpt):
        source = SourceRecord(
            workspace_id=workspace.id,
            source_url="https://example.test/source",
            content_hash="a" * 64,
            raw_excerpt=excerpt,
        )
        self.db.add(source)
        self.db.flush()
        return source

    def test_analyzes_and_persists_source_record(self):
        source = self.make_source(
            self.workspace,
            "I opened a new retail shop and need GST registration.",
        )

        result = analyze_source_record(
            self.db, source.id, self.workspace.id
        )

        self.assertEqual(result["source_record_id"], source.id)
        self.assertGreater(result["persistence"]["total"], 0)

        rows = self.db.scalars(
            select(IntelligenceResult).where(
                IntelligenceResult.source_record_id == source.id
            )
        ).all()

        self.assertGreater(len(rows), 0)
        self.assertTrue(
            all(row.workspace_id == self.workspace.id for row in rows)
        )

    def test_source_record_discovery_run_and_entity_are_forwarded(self):
        source = self.make_source(
            self.workspace,
            "I opened a new retail shop and need GST registration.",
        )

        result = analyze_source_record(
            self.db, source.id, self.workspace.id
        )

        rows = self.db.scalars(
            select(IntelligenceResult).where(
                IntelligenceResult.source_record_id == source.id
            )
        ).all()

        self.assertTrue(rows)
        self.assertTrue(
            all(row.discovery_run_id == source.discovery_run_id for row in rows)
        )
        self.assertTrue(
            all(row.entity_id == source.entity_id for row in rows)
        )

    def test_cross_workspace_source_is_rejected(self):
        source = self.make_source(
            self.other_workspace,
            "I need GST registration.",
        )

        with self.assertRaisesRegex(
            ValueError, "different workspace"
        ):
            analyze_source_record(
                self.db, source.id, self.workspace.id
            )

    def test_missing_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            analyze_source_record(
                self.db,
                "00000000-0000-4000-8000-999999999999",
                self.workspace.id,
            )

    def test_empty_excerpt_is_rejected(self):
        source = self.make_source(self.workspace, "   ")

        with self.assertRaisesRegex(ValueError, "raw_excerpt"):
            analyze_source_record(
                self.db, source.id, self.workspace.id
            )

    def test_source_pipeline_does_not_commit(self):
        source = self.make_source(
            self.workspace,
            "I opened a new retail shop and need GST registration.",
        )
        self.db.commit()

        analyze_source_record(
            self.db, source.id, self.workspace.id
        )

        self.assertTrue(self.db.in_transaction())
        self.db.rollback()

        rows = self.db.scalars(
            select(IntelligenceResult).where(
                IntelligenceResult.source_record_id == source.id
            )
        ).all()

        self.assertEqual(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
