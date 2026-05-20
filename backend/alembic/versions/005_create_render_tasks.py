"""create render_tasks table

Revision ID: 005
Revises: 004
Create Date: 2026-04-02

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "render_tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=False,
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("templates.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("ai_clean_result", sa.Text, nullable=True),
        sa.Column("ai_structure", postgresql.JSONB, nullable=True),
        sa.Column("result_path", sa.String(512), nullable=True),
        sa.Column("preview_path", sa.String(512), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
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
    op.create_index("ix_render_tasks_created_by", "render_tasks", ["created_by"])
    op.create_index("ix_render_tasks_status", "render_tasks", ["status"])


def downgrade() -> None:
    op.drop_index("ix_render_tasks_status", table_name="render_tasks")
    op.drop_index("ix_render_tasks_created_by", table_name="render_tasks")
    op.drop_table("render_tasks")
