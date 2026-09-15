"""P6-26: add shopify_credentials table for encrypted Admin API credentials

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "shopify_credentials",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("store_url_encrypted", sa.String(512), nullable=False),
        sa.Column("access_token_encrypted", sa.String(512), nullable=False),
        sa.Column("shop_name", sa.String(128), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_index("idx_shopify_credentials_tenant", "shopify_credentials", ["tenant_id"])
    op.create_index(
        "idx_shopify_credentials_tenant_active",
        "shopify_credentials",
        ["tenant_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_index("idx_shopify_credentials_tenant_active", table_name="shopify_credentials")
    op.drop_index("idx_shopify_credentials_tenant", table_name="shopify_credentials")
    op.drop_table("shopify_credentials")
