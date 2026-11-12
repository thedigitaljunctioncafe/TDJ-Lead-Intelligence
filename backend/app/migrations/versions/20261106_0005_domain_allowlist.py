"""Add workspace-scoped approved domain allowlist."""

from alembic import op
import sqlalchemy as sa

revision = "20261106_0005"
down_revision = "20261105_0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "workspace_domain_allowlist",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(length=36),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("domain", sa.String(length=253), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "approved_by_user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "approved_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint(
            "workspace_id",
            "domain",
            name="uq_workspace_allowlist_domain",
        ),
        sa.CheckConstraint(
            "length(domain) >= 1 AND length(domain) <= 253",
            name="ck_allowlist_domain_length",
        ),
    )

    op.create_index(
        "ix_workspace_allowlist_workspace_active",
        "workspace_domain_allowlist",
        ["workspace_id", "is_active"],
    )


def downgrade():
    raise RuntimeError(
        "Automatic downgrade is disabled to protect allowlist history. "
        "Restore a verified backup instead."
    )
