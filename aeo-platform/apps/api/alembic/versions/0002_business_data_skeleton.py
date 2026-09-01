"""MV1-06 business data tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "order_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_order_id", sa.String(64), nullable=False),
        sa.Column("sku", sa.String(128), nullable=False),
        sa.Column("platform", sa.String(32), nullable=False, server_default="amazon"),
        sa.Column("marketplace", sa.String(16), nullable=False, server_default="US"),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("item_price", sa.String(32), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("order_status", sa.String(32), nullable=False, server_default="Unshipped"),
        sa.Column("purchase_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_source", sa.String(16), nullable=False, server_default="mock"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_order_records_external_order_id", "order_records", ["external_order_id"])
    op.create_index("ix_order_records_sku", "order_records", ["sku"])
    op.create_index("idx_order_records_platform_sku", "order_records", ["platform", "sku"])

    op.create_table(
        "ad_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_campaign_id", sa.String(64), nullable=False, unique=True),
        sa.Column("platform", sa.String(32), nullable=False, server_default="amazon"),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="enabled"),
        sa.Column("daily_budget", sa.String(32), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("data_source", sa.String(16), nullable=False, server_default="mock"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "ad_spend_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("spend", sa.String(32), nullable=True),
        sa.Column("impressions", sa.Integer(), nullable=True),
        sa.Column("clicks", sa.Integer(), nullable=True),
        sa.Column("attributed_gmv", sa.String(32), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("data_source", sa.String(16), nullable=False, server_default="mock"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ad_spend_snapshots_campaign_id", "ad_spend_snapshots", ["campaign_id"])
    op.create_index(
        "idx_ad_spend_campaign_date",
        "ad_spend_snapshots",
        ["campaign_id", "snapshot_date"],
    )


def downgrade() -> None:
    op.drop_table("ad_spend_snapshots")
    op.drop_table("ad_campaigns")
    op.drop_table("order_records")
