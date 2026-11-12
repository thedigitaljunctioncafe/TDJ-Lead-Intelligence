import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import IntelligenceResult, Workspace
from app.intelligence_pipeline import analyze_and_persist_text


class TestIntelligencePipeline(unittest.TestCase):

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
            name="Pipeline Test Workspace",
            slug="pipeline-test-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.db.add(self.workspace)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_analyzes_and_persists_real_text(self):
        result = analyze_and_persist_text(
            db=self.db,
            text=(
                "I opened a new retail shop. "
                "I need GST registration and a website."
            ),
            workspace_id=self.workspace.id,
        )

        self.assertIn("analysis", result)
        self.assertIn("persistence", result)
        self.assertIn("summary", result)

        self.assertGreater(
            result["summary"]["discovery_count"], 0
        )
        self.assertGreater(
            result["summary"]["confirmed_intent_count"], 0
        )
        self.assertGreater(
            result["persistence"]["total"], 0
        )

        rows = self.db.scalars(
            select(IntelligenceResult)
        ).all()

        self.assertEqual(
            len(rows), result["persistence"]["total"]
        )

    def test_no_match_text_returns_empty_results(self):
        result = analyze_and_persist_text(
            db=self.db,
            text="The sky is clear today.",
            workspace_id=self.workspace.id,
        )

        self.assertEqual(result["summary"]["discovery_count"], 0)
        self.assertEqual(
            result["summary"]["confirmed_intent_count"], 0
        )
        self.assertEqual(
            result["summary"]["potential_opportunity_count"], 0
        )
        self.assertEqual(result["persistence"]["total"], 0)

    def test_empty_text_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-empty string"):
            analyze_and_persist_text(
                db=self.db,
                text="   ",
                workspace_id=self.workspace.id,
            )

    def test_invalid_workspace_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Workspace does not exist"):
            analyze_and_persist_text(
                db=self.db,
                text="I opened a new retail shop.",
                workspace_id="00000000-0000-4000-8000-999999999999",
            )

    def test_pipeline_does_not_commit_transaction(self):
        analyze_and_persist_text(
            db=self.db,
            text="I opened a new retail shop and need GST registration.",
            workspace_id=self.workspace.id,
        )

        self.assertTrue(self.db.in_transaction())

        self.db.rollback()

        rows = self.db.scalars(
            select(IntelligenceResult)
        ).all()

        self.assertEqual(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
