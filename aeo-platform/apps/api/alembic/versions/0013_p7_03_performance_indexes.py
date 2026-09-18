"""P7-03: add performance indexes for common query patterns

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-18
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("idx_tasks_tenant_status", "tasks", ["tenant_id", "status"])
    op.create_index("idx_tasks_platform_market", "tasks", ["platform", "market"])

    op.create_index("idx_order_records_purchase_date", "order_records", ["purchase_date"])
    op.create_index("idx_order_records_marketplace", "order_records", ["marketplace"])

    op.create_index("idx_ad_spend_snapshot_date", "ad_spend_snapshots", ["snapshot_date"])

    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])

    op.create_index("idx_competitor_marketplace", "competitor_listings", ["marketplace"])
    op.create_index("idx_competitor_category", "competitor_listings", ["category"])

    op.create_index(
        "idx_selection_platform_market", "selection_scores", ["platform", "marketplace"]
    )
    op.create_index("idx_selection_scored_at", "selection_scores", ["scored_at"])


def downgrade() -> None:
    op.drop_index("idx_selection_scored_at", table_name="selection_scores")
    op.drop_index("idx_selection_platform_market", table_name="selection_scores")
    op.drop_index("idx_competitor_category", table_name="competitor_listings")
    op.drop_index("idx_competitor_marketplace", table_name="competitor_listings")
    op.drop_index("idx_audit_logs_action", table_name="audit_logs")
    op.drop_index("idx_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("idx_ad_spend_snapshot_date", table_name="ad_spend_snapshots")
    op.drop_index("idx_order_records_marketplace", table_name="order_records")
    op.drop_index("idx_order_records_purchase_date", table_name="order_records")
    op.drop_index("idx_tasks_platform_market", table_name="tasks")
    op.drop_index("idx_tasks_tenant_status", table_name="tasks")
