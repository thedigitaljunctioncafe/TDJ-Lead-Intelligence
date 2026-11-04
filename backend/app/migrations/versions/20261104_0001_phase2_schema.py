"""Introduce multi-workspace Phase 2 lead intelligence schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, select
from app import models
from app.database import Base

revision = "20261104_0001"
down_revision = None
branch_labels = None
depends_on = None

DEFAULT_WORKSPACE_ID = "00000000-0000-4000-8000-000000000001"
DEFAULT_WORKSPACE_SLUG = "the-digital-junction"


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Create all new tables first, excluding the Phase 1 table that needs an in-place upgrade.
    new_tables = [table for table in Base.metadata.sorted_tables if table.name != "search_jobs"]
    Base.metadata.create_all(bind=bind, tables=new_tables)

    # Seed the default TDJ workspace used to own all Phase 1 search jobs.
    workspaces = models.Workspace.__table__
    existing = bind.execute(select(workspaces.c.id).where(workspaces.c.slug == DEFAULT_WORKSPACE_SLUG)).first()
    default_workspace_id = existing[0] if existing else DEFAULT_WORKSPACE_ID
    if existing is None:
        bind.execute(workspaces.insert().values(
            id=default_workspace_id,
            name="The Digital Junction",
            slug=DEFAULT_WORKSPACE_SLUG,
            workspace_type="organization",
            is_active=True,
        ))

    inspector = inspect(bind)
    if "search_jobs" not in inspector.get_table_names():
        models.SearchJob.__table__.create(bind=bind)
    else:
        columns = {column["name"] for column in inspector.get_columns("search_jobs")}
        if "workspace_id" not in columns:
            with op.batch_alter_table("search_jobs") as batch_op:
                batch_op.add_column(sa.Column("workspace_id", sa.String(length=36), nullable=True))
            bind.execute(sa.text("UPDATE search_jobs SET workspace_id = :workspace_id WHERE workspace_id IS NULL"), {"workspace_id": default_workspace_id})
            with op.batch_alter_table("search_jobs") as batch_op:
                batch_op.alter_column("workspace_id", existing_type=sa.String(length=36), nullable=False)
                batch_op.create_foreign_key("fk_search_jobs_workspace_id_workspaces", "workspaces", ["workspace_id"], ["id"], ondelete="CASCADE")
                batch_op.create_index("ix_search_jobs_workspace_id", ["workspace_id"])


def downgrade():
    # Destructive downgrade intentionally not automated: Phase 2 data may have been added.
    raise RuntimeError("Automatic downgrade is disabled to prevent accidental loss of lead/workspace data. Restore a verified backup instead.")
