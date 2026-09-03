"""MV2-01 competitor pool and selection scoring tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "competitor_listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("asin", sa.String(32), nullable=False),
        sa.Column("sku", sa.String(128), nullable=False),
        sa.Column("platform", sa.String(32), nullable=False, server_default="amazon"),
        sa.Column("marketplace", sa.String(16), nullable=False, server_default="US"),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("brand", sa.String(128), nullable=True),
        sa.Column("price", sa.String(32), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("bullet_points", postgresql.JSON(), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("data_source", sa.String(16), nullable=False, server_default="mock"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_competitor_listings_asin", "competitor_listings", ["asin"])
    op.create_index("ix_competitor_listings_sku", "competitor_listings", ["sku"])
    op.create_index("idx_competitor_platform_asin", "competitor_listings", ["platform", "asin"])

    op.create_table(
        "selection_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sku", sa.String(128), nullable=False),
        sa.Column("platform", sa.String(32), nullable=False, server_default="amazon"),
        sa.Column("marketplace", sa.String(16), nullable=False, server_default="US"),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("demand_score", sa.Float(), nullable=False),
        sa.Column("competition_score", sa.Float(), nullable=False),
        sa.Column("profitability_score", sa.Float(), nullable=False),
        sa.Column("completeness_score", sa.Float(), nullable=False),
        sa.Column("competitor_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detail", postgresql.JSON(), nullable=True),
        sa.Column("recommendation", sa.String(32), nullable=False, server_default="review"),
        sa.Column("scored_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_selection_scores_sku", "selection_scores", ["sku"])
    op.create_index("idx_selection_score", "selection_scores", ["total_score"])


def downgrade() -> None:
    op.drop_table("selection_scores")
    op.drop_table("competitor_listings")
