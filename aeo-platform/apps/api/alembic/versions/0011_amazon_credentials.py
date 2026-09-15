"""P6-21: add amazon_credentials table for encrypted SP-API credentials

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "amazon_credentials",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("client_id_encrypted", sa.String(512), nullable=False),
        sa.Column("client_secret_encrypted", sa.String(512), nullable=False),
        sa.Column("refresh_token_encrypted", sa.String(512), nullable=False),
        sa.Column("marketplace_id", sa.String(32), nullable=False, server_default="ATVPDKIKX0DER"),
        sa.Column("region", sa.String(16), nullable=False, server_default="us-east-1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_index("idx_amazon_credentials_tenant", "amazon_credentials", ["tenant_id"])
    op.create_index(
        "idx_amazon_credentials_tenant_active",
        "amazon_credentials",
        ["tenant_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_index("idx_amazon_credentials_tenant_active", table_name="amazon_credentials")
    op.drop_index("idx_amazon_credentials_tenant", table_name="amazon_credentials")
    op.drop_table("amazon_credentials")
