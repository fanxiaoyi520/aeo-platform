"""P5-06: add tenant_id to audit_logs, competitor_listings, selection_scores, intelligence_schedules

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SYSTEM_TENANT_ID = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column("tenant_id", sa.String(64), nullable=False, server_default=SYSTEM_TENANT_ID),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])

    op.add_column(
        "competitor_listings",
        sa.Column("tenant_id", sa.String(64), nullable=False, server_default=SYSTEM_TENANT_ID),
    )
    op.create_index("ix_competitor_listings_tenant_id", "competitor_listings", ["tenant_id"])

    op.add_column(
        "selection_scores",
        sa.Column("tenant_id", sa.String(64), nullable=False, server_default=SYSTEM_TENANT_ID),
    )
    op.create_index("ix_selection_scores_tenant_id", "selection_scores", ["tenant_id"])

    op.add_column(
        "intelligence_schedules",
        sa.Column("tenant_id", sa.String(64), nullable=False, server_default=SYSTEM_TENANT_ID),
    )
    op.create_index("ix_intelligence_schedules_tenant_id", "intelligence_schedules", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_intelligence_schedules_tenant_id", table_name="intelligence_schedules")
    op.drop_column("intelligence_schedules", "tenant_id")
    op.drop_index("ix_selection_scores_tenant_id", table_name="selection_scores")
    op.drop_column("selection_scores", "tenant_id")
    op.drop_index("ix_competitor_listings_tenant_id", table_name="competitor_listings")
    op.drop_column("competitor_listings", "tenant_id")
    op.drop_index("ix_audit_logs_tenant_id", table_name="audit_logs")
    op.drop_column("audit_logs", "tenant_id")
