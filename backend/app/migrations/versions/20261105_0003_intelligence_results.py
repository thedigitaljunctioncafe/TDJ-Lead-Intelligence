"""Add workspace-scoped unified intelligence result persistence."""

from alembic import op
import sqlalchemy as sa

revision = "20261105_0003"
down_revision = "20261104_0002"
branch_labels = None
depends_on = None


def upgrade():
    # Alembic revision tracking prevents this migration from running twice.
    # Avoid inspection here so offline SQL generation remains supported.

    op.create_table(
        "intelligence_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(length=36),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "discovery_run_id",
            sa.String(length=36),
            sa.ForeignKey("discovery_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "source_record_id",
            sa.String(length=36),
            sa.ForeignKey("source_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "entity_id",
            sa.String(length=36),
            sa.ForeignKey("entities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "lead_id",
            sa.String(length=36),
            sa.ForeignKey("leads.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("result_type", sa.String(length=40), nullable=False),
        sa.Column("result_key", sa.String(length=128), nullable=False),
        sa.Column("result_payload", sa.JSON(), nullable=False),
        sa.Column("engine_version", sa.String(length=80), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "workspace_id",
            "result_key",
            name="uq_intelligence_result_workspace_key",
        ),
        sa.CheckConstraint(
            "result_type IN "
            "('discovery_signal', 'confirmed_service_intent', "
            "'potential_opportunity')",
            name="ck_intelligence_result_type",
        ),
        sa.CheckConstraint(
            "confidence_score IS NULL OR "
            "(confidence_score >= 0 AND confidence_score <= 100)",
            name="ck_intelligence_result_confidence_range",
        ),
    )

    op.create_index(
        "ix_intelligence_results_workspace_type",
        "intelligence_results",
        ["workspace_id", "result_type"],
    )
    op.create_index(
        "ix_intelligence_results_source_record",
        "intelligence_results",
        ["source_record_id"],
    )
    op.create_index(
        "ix_intelligence_results_entity",
        "intelligence_results",
        ["entity_id"],
    )
    op.create_index(
        "ix_intelligence_results_lead",
        "intelligence_results",
        ["lead_id"],
    )
    op.create_index(
        "ix_intelligence_results_discovery_run",
        "intelligence_results",
        ["discovery_run_id"],
    )


def downgrade():
    raise RuntimeError(
        "Automatic downgrade is disabled to prevent accidental loss "
        "of intelligence data. Restore a verified backup instead."
    )
