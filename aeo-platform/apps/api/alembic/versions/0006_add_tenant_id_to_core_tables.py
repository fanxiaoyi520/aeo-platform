"""P5-05: add tenant_id to tasks and knowledge_documents

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SYSTEM_TENANT_ID = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("tenant_id", sa.String(64), nullable=False, server_default=SYSTEM_TENANT_ID),
    )
    op.create_index("ix_tasks_tenant_id", "tasks", ["tenant_id"])

    op.add_column(
        "knowledge_documents",
        sa.Column("tenant_id", sa.String(64), nullable=False, server_default=SYSTEM_TENANT_ID),
    )
    op.create_index("ix_knowledge_documents_tenant_id", "knowledge_documents", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_documents_tenant_id", table_name="knowledge_documents")
    op.drop_column("knowledge_documents", "tenant_id")
    op.drop_index("ix_tasks_tenant_id", table_name="tasks")
    op.drop_column("tasks", "tenant_id")
