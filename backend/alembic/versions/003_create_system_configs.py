"""create system_configs table

Revision ID: 003
Revises: 002
Create Date: 2026-04-02

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "system_configs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("value", sa.String(2048), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_system_configs_key", "system_configs", ["key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_system_configs_key", table_name="system_configs")
    op.drop_table("system_configs")
