"""P6-02: add subscriptions, invoices, billing_events tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("stripe_customer_id", sa.String(128), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="incomplete"),
        sa.Column("plan", sa.String(32), nullable=False, server_default="free"),
        sa.Column("stripe_price_id", sa.String(128), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_tenant_id", "subscriptions", ["tenant_id"])
    op.create_index("ix_subscriptions_stripe_customer_id", "subscriptions", ["stripe_customer_id"])
    op.create_index("ix_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"], unique=True)
    op.create_index("idx_subscriptions_tenant_status", "subscriptions", ["tenant_id", "status"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("stripe_invoice_id", sa.String(128), nullable=False),
        sa.Column("stripe_customer_id", sa.String(128), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("amount_due", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(8), nullable=False, server_default="usd"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invoice_pdf", sa.String(1024), nullable=True),
        sa.Column("hosted_invoice_url", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoices_tenant_id", "invoices", ["tenant_id"])
    op.create_index("ix_invoices_stripe_invoice_id", "invoices", ["stripe_invoice_id"], unique=True)
    op.create_index("ix_invoices_stripe_customer_id", "invoices", ["stripe_customer_id"])
    op.create_index("idx_invoices_tenant_status", "invoices", ["tenant_id", "status"])

    op.create_table(
        "billing_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("stripe_event_id", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("stripe_customer_id", sa.String(128), nullable=True),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_billing_events_stripe_event_id", "billing_events", ["stripe_event_id"], unique=True)
    op.create_index("ix_billing_events_stripe_customer_id", "billing_events", ["stripe_customer_id"])
    op.create_index("idx_billing_events_type", "billing_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("idx_billing_events_type", table_name="billing_events")
    op.drop_index("ix_billing_events_stripe_customer_id", table_name="billing_events")
    op.drop_index("ix_billing_events_stripe_event_id", table_name="billing_events")
    op.drop_table("billing_events")

    op.drop_index("idx_invoices_tenant_status", table_name="invoices")
    op.drop_index("ix_invoices_stripe_customer_id", table_name="invoices")
    op.drop_index("ix_invoices_stripe_invoice_id", table_name="invoices")
    op.drop_index("ix_invoices_tenant_id", table_name="invoices")
    op.drop_table("invoices")

    op.drop_index("idx_subscriptions_tenant_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_stripe_subscription_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_stripe_customer_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_tenant_id", table_name="subscriptions")
    op.drop_table("subscriptions")
