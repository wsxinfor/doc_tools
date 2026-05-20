"""create documents table

Revision ID: 002
Revises: 001
Create Date: 2026-04-02

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("filename", sa.String(256), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("file_type", sa.String(8), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column(
            "uploader_id",
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
    )
    op.create_index("ix_documents_uploader_id", "documents", ["uploader_id"])
    op.create_index("ix_documents_is_deleted", "documents", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_documents_is_deleted", table_name="documents")
    op.drop_index("ix_documents_uploader_id", table_name="documents")
    op.drop_table("documents")
