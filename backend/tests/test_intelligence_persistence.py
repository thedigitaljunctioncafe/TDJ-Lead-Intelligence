import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    DiscoveryRun,
    Entity,
    IntelligenceResult,
    Lead,
    SearchJob,
    SourceRecord,
    Workspace,
)
from app.intelligence_persistence import save_intelligence_results


class TestIntelligencePersistence(unittest.TestCase):

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
            slug="test-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.other_workspace = Workspace(
            name="Other Workspace",
            slug="other-workspace",
            workspace_type="organization",
            is_active=True,
        )
        self.db.add_all([self.workspace, self.other_workspace])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def _make_source_record(self, workspace, suffix):
        record = SourceRecord(
            workspace_id=workspace.id,
            source_url=f"https://example.test/{suffix}",
            content_hash=(suffix.encode("utf-8").hex() * 4)[:64],
        )
        self.db.add(record)
        self.db.flush()
        return record

    def _make_entity(self, workspace, suffix):
        entity = Entity(
            workspace_id=workspace.id,
            entity_type="business",
            canonical_name=f"Test Business {suffix}",
            normalized_name=f"test-business-{suffix}",
        )
        self.db.add(entity)
        self.db.flush()
        return entity

    def _make_discovery_run(self, workspace, job_workspace=None):
        job_workspace = job_workspace or workspace
        job = SearchJob(
            workspace_id=job_workspace.id,
            query="test discovery",
        )
        self.db.add(job)
        self.db.flush()

        run = DiscoveryRun(
            workspace_id=workspace.id,
            search_job_id=job.id,
        )
        self.db.add(run)
        self.db.flush()
        return run

    def _make_lead(self, workspace, entity_id=None, source_record_id=None):
        lead = Lead(
            workspace_id=workspace.id,
            entity_id=entity_id,
            primary_source_record_id=source_record_id,
            lead_type="business",
            title="Test Lead",
        )
        self.db.add(lead)
        self.db.flush()
        return lead

    def sample_analysis(self):
        return {
            "discovery_signals": [
                {
                    "signal_type": "business_discovery",
                    "discovery_code": "new_retail_shop",
                    "label": "New Retail Shop",
                    "evidence_type": "keyword_signal",
                    "matched_keywords": ["new retail shop"],
                }
            ],
            "confirmed_service_intents": [
                {
                    "service_code": "GST",
                    "relevance_score": 95,
                    "confidence": "keyword_signal",
                    "matched_rules": ["gst_intent"],
                    "matched_keywords": ["need gst"],
                    "match_reason": "Explicit GST request",
                    "intent_type": "confirmed_service_intent",
                }
            ],
            "potential_opportunities": [
                {
                    "service_code": "WEBSITE",
                    "opportunity_type": "potential_opportunity",
                    "confirmed_intent": False,
                    "based_on_discovery": ["new_retail_shop"],
                    "reasons": ["New business may need a website"],
                }
            ],
        }

    def test_saves_all_three_result_types(self):
        result = save_intelligence_results(
            self.db,
            self.sample_analysis(),
            workspace_id=self.workspace.id,
            engine_version="test-1",
        )

        self.assertEqual(result["created"], 3)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["total"], 3)

        rows = self.db.scalars(
            select(IntelligenceResult)
        ).all()

        self.assertEqual(len(rows), 3)
        self.assertEqual(
            {row.result_type for row in rows},
            {
                "discovery_signal",
                "confirmed_service_intent",
                "potential_opportunity",
            },
        )

    def test_potential_opportunity_never_claims_confirmed_intent(self):
        save_intelligence_results(
            self.db,
            self.sample_analysis(),
            workspace_id=self.workspace.id,
            engine_version="test-1",
        )

        opportunity = self.db.scalar(
            select(IntelligenceResult).where(
                IntelligenceResult.result_type == "potential_opportunity"
            )
        )

        self.assertIsNotNone(opportunity)
        self.assertIs(
            opportunity.result_payload["confirmed_intent"], False
        )

    def test_repeated_save_does_not_create_duplicates(self):
        analysis = self.sample_analysis()

        first = save_intelligence_results(
            self.db, analysis,
            workspace_id=self.workspace.id,
            engine_version="test-1",
        )
        second = save_intelligence_results(
            self.db, analysis,
            workspace_id=self.workspace.id,
            engine_version="test-1",
        )

        self.assertEqual(first["created"], 3)
        self.assertEqual(second["created"], 0)
        self.assertEqual(second["updated"], 3)

        count = self.db.scalar(
            select(IntelligenceResult).count()
        ) if False else len(
            self.db.scalars(select(IntelligenceResult)).all()
        )
        self.assertEqual(count, 3)

    def test_workspace_results_are_isolated(self):
        analysis = self.sample_analysis()

        save_intelligence_results(
            self.db, analysis,
            workspace_id=self.workspace.id,
            engine_version="test-1",
        )
        save_intelligence_results(
            self.db, analysis,
            workspace_id=self.other_workspace.id,
            engine_version="test-1",
        )

        rows = self.db.scalars(
            select(IntelligenceResult)
        ).all()

        self.assertEqual(len(rows), 6)
        self.assertEqual(
            {row.workspace_id for row in rows},
            {self.workspace.id, self.other_workspace.id},
        )

    def test_empty_analysis_saves_nothing(self):
        result = save_intelligence_results(
            self.db,
            {},
            workspace_id=self.workspace.id,
            engine_version="test-1",
        )

        self.assertEqual(result["created"], 0)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["total"], 0)

    def test_invalid_analysis_is_rejected(self):
        with self.assertRaises((TypeError, ValueError)):
            save_intelligence_results(
                self.db,
                {"confirmed_service_intents": "not-a-list"},
                workspace_id=self.workspace.id,
                engine_version="test-1",
            )

    def test_invalid_workspace_is_rejected(self):
        with self.assertRaises((TypeError, ValueError)):
            save_intelligence_results(
                self.db,
                self.sample_analysis(),
                workspace_id="invalid-workspace-id",
                engine_version="test-1",
            )

    def test_service_does_not_commit_caller_transaction(self):
        save_intelligence_results(
            self.db,
            self.sample_analysis(),
            workspace_id=self.workspace.id,
            engine_version="test-1",
        )

        self.db.rollback()

        rows = self.db.scalars(
            select(IntelligenceResult)
        ).all()

        self.assertEqual(rows, [])


    def test_same_discovery_from_different_sources_is_preserved(self):
        source_a = self._make_source_record(self.workspace, "source-A")
        source_b = self._make_source_record(self.workspace, "source-B")

        first = save_intelligence_results(
            self.db,
            self.sample_analysis(),
            workspace_id=self.workspace.id,
            source_record_id=source_a.id,
            engine_version="test-1",
        )

        second = save_intelligence_results(
            self.db,
            self.sample_analysis(),
            workspace_id=self.workspace.id,
            source_record_id=source_b.id,
            engine_version="test-1",
        )

        self.assertEqual(first["created"], 3)
        self.assertEqual(second["created"], 3)

        rows = self.db.scalars(
            select(IntelligenceResult).where(
                IntelligenceResult.result_type == "discovery_signal"
            )
        ).all()

        self.assertEqual(len(rows), 2)
        self.assertEqual(
            {row.source_record_id for row in rows},
            {source_a.id, source_b.id},
        )

    def test_same_source_repeated_discovery_updates_existing_record(self):
        source = self._make_source_record(self.workspace, "repeat-source")

        first = save_intelligence_results(
            self.db,
            self.sample_analysis(),
            workspace_id=self.workspace.id,
            source_record_id=source.id,
            engine_version="test-1",
        )

        second = save_intelligence_results(
            self.db,
            self.sample_analysis(),
            workspace_id=self.workspace.id,
            source_record_id=source.id,
            engine_version="test-2",
        )

        self.assertEqual(first["created"], 3)
        self.assertEqual(second["created"], 0)
        self.assertEqual(second["updated"], 3)
        self.assertEqual(second["total"], 3)

        rows = self.db.scalars(
            select(IntelligenceResult)
        ).all()

        self.assertEqual(len(rows), 3)
        self.assertTrue(
            all(row.engine_version == "test-2" for row in rows)
        )


    def test_cross_workspace_source_record_is_rejected(self):
        source = self._make_source_record(self.other_workspace, "foreign-source")

        with self.assertRaisesRegex(ValueError, "different workspace"):
            save_intelligence_results(
                self.db, self.sample_analysis(),
                workspace_id=self.workspace.id,
                source_record_id=source.id,
            )

    def test_cross_workspace_entity_is_rejected(self):
        entity = self._make_entity(self.other_workspace, "foreign")

        with self.assertRaisesRegex(ValueError, "different workspace"):
            save_intelligence_results(
                self.db, self.sample_analysis(),
                workspace_id=self.workspace.id,
                entity_id=entity.id,
            )

    def test_cross_workspace_lead_is_rejected(self):
        lead = self._make_lead(self.other_workspace)

        with self.assertRaisesRegex(ValueError, "different workspace"):
            save_intelligence_results(
                self.db, self.sample_analysis(),
                workspace_id=self.workspace.id,
                lead_id=lead.id,
            )

    def test_cross_workspace_discovery_run_is_rejected(self):
        run = self._make_discovery_run(self.other_workspace)

        with self.assertRaisesRegex(ValueError, "different workspace"):
            save_intelligence_results(
                self.db, self.sample_analysis(),
                workspace_id=self.workspace.id,
                discovery_run_id=run.id,
            )

    def test_discovery_run_with_foreign_search_job_is_rejected(self):
        run = self._make_discovery_run(
            self.workspace,
            job_workspace=self.other_workspace,
        )

        with self.assertRaisesRegex(ValueError, "DiscoveryRun.search_job_id"):
            save_intelligence_results(
                self.db, self.sample_analysis(),
                workspace_id=self.workspace.id,
                discovery_run_id=run.id,
            )

    def test_source_record_with_foreign_entity_is_rejected(self):
        entity = self._make_entity(self.other_workspace, "foreign-source-entity")
        source = SourceRecord(
            workspace_id=self.workspace.id,
            entity_id=entity.id,
            source_url="https://example.test/foreign-entity",
            content_hash="a" * 64,
        )
        self.db.add(source)
        self.db.flush()

        with self.assertRaisesRegex(ValueError, "SourceRecord.entity_id"):
            save_intelligence_results(
                self.db, self.sample_analysis(),
                workspace_id=self.workspace.id,
                source_record_id=source.id,
            )

    def test_lead_with_foreign_entity_is_rejected(self):
        entity = self._make_entity(self.other_workspace, "foreign-lead-entity")
        lead = self._make_lead(self.workspace, entity_id=entity.id)

        with self.assertRaisesRegex(ValueError, "Lead.entity_id"):
            save_intelligence_results(
                self.db, self.sample_analysis(),
                workspace_id=self.workspace.id,
                lead_id=lead.id,
            )

    def test_lead_with_foreign_primary_source_is_rejected(self):
        source = self._make_source_record(
            self.other_workspace, "foreign-lead-source"
        )
        lead = self._make_lead(
            self.workspace, source_record_id=source.id
        )

        with self.assertRaisesRegex(
            ValueError, "Lead.primary_source_record_id"
        ):
            save_intelligence_results(
                self.db, self.sample_analysis(),
                workspace_id=self.workspace.id,
                lead_id=lead.id,
            )

    def test_missing_source_record_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "source_record_id does not exist"):
            save_intelligence_results(
                self.db, self.sample_analysis(),
                workspace_id=self.workspace.id,
                source_record_id="00000000-0000-4000-8000-000000000099",
            )

    def test_lead_and_source_entity_mismatch_is_rejected(self):
        lead_entity = self._make_entity(self.workspace, "lead-entity")
        source_entity = self._make_entity(self.workspace, "source-entity")
        source = self._make_source_record(self.workspace, "mismatched-source")
        source.entity_id = source_entity.id

        lead = self._make_lead(
            self.workspace,
            entity_id=lead_entity.id,
            source_record_id=source.id,
        )

        with self.assertRaisesRegex(ValueError, "does not match"):
            save_intelligence_results(
                self.db, self.sample_analysis(),
                workspace_id=self.workspace.id,
                lead_id=lead.id,
            )


if __name__ == "__main__":
    unittest.main()
