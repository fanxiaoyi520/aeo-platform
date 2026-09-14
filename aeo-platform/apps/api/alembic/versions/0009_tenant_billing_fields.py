"""P6-03: add stripe_customer_id, trial_ends_at, billing_status to tenants

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("stripe_customer_id", sa.String(128), nullable=True),
    )
    op.create_index(
        "ix_tenants_stripe_customer_id", "tenants", ["stripe_customer_id"], unique=True
    )

    op.add_column(
        "tenants",
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "tenants",
        sa.Column("billing_status", sa.String(32), nullable=True, server_default="active"),
    )


def downgrade() -> None:
    op.drop_column("tenants", "billing_status")
    op.drop_column("tenants", "trial_ends_at")
    op.drop_index("ix_tenants_stripe_customer_id", table_name="tenants")
    op.drop_column("tenants", "stripe_customer_id")
