
"""Safely ensure requested_by_user_id exists on search_jobs."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20261104_0002"
down_revision = "20261104_0001"
branch_labels = None
depends_on = None

FK_NAME = "fk_search_jobs_requested_by_user_id_users"


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    columns = {
        column["name"]
        for column in inspector.get_columns("search_jobs")
    }

    foreign_keys = {
        fk.get("name")
        for fk in inspector.get_foreign_keys("search_jobs")
    }

    with op.batch_alter_table("search_jobs") as batch_op:
        if "requested_by_user_id" not in columns:
            batch_op.add_column(
                sa.Column(
                    "requested_by_user_id",
                    sa.String(length=36),
                    nullable=True,
                )
            )

        if FK_NAME not in foreign_keys:
            batch_op.create_foreign_key(
                FK_NAME,
                "users",
                ["requested_by_user_id"],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    columns = {
        column["name"]
        for column in inspector.get_columns("search_jobs")
    }

    foreign_keys = {
        fk.get("name")
        for fk in inspector.get_foreign_keys("search_jobs")
    }

    with op.batch_alter_table("search_jobs") as batch_op:
        if FK_NAME in foreign_keys:
            batch_op.drop_constraint(
                FK_NAME,
                type_="foreignkey",
            )

        if "requested_by_user_id" in columns:
            batch_op.drop_column("requested_by_user_id")
