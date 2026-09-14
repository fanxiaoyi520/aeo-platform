"""P6-07: add plans table for plan definitions

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(32), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("description", sa.String(512), nullable=False),
        sa.Column("stripe_price_monthly", sa.String(128), nullable=True),
        sa.Column("stripe_price_yearly", sa.String(128), nullable=True),
        sa.Column("monthly_tasks", sa.Integer(), nullable=True),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("stripe_price_monthly"),
        sa.UniqueConstraint("stripe_price_yearly"),
    )
    op.create_index("idx_plans_name", "plans", ["name"])
    op.create_index("idx_plans_active", "plans", ["is_active"])


def downgrade() -> None:
    op.drop_index("idx_plans_active", table_name="plans")
    op.drop_index("idx_plans_name", table_name="plans")
    op.drop_table("plans")
