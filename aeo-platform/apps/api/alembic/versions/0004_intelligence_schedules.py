"""MV2-03 intelligence schedules table

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "intelligence_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", sa.String(128), nullable=False, unique=True),
        sa.Column("sku", sa.String(128), nullable=False),
        sa.Column("cron_expression", sa.String(64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("payload", postgresql.JSON(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_intel_sched_sku", "intelligence_schedules", ["sku"])
    op.create_index("idx_intel_sched_enabled", "intelligence_schedules", ["enabled"])


def downgrade() -> None:
    op.drop_table("intelligence_schedules")
