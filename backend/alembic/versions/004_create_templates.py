"""create templates table

Revision ID: 004
Revises: 003
Create Date: 2026-04-02

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("config", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_templates_is_deleted", "templates", ["is_deleted"])
    op.create_index("ix_templates_created_by", "templates", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_templates_created_by", table_name="templates")
    op.drop_index("ix_templates_is_deleted", table_name="templates")
    op.drop_table("templates")
