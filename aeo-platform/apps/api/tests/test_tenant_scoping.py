"""P5-05: Tenant scoping and query isolation tests."""

import os
from uuid import uuid4

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASEURL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")

from aeo_api.auth.context import current_tenant_id  # noqa: E402
from aeo_api.db.models import KnowledgeDocument, Task  # noqa: E402
from aeo_api.db.tenant_models import SYSTEM_TENANT_ID, TenantMixin  # noqa: E402
from aeo_api.db.tenant_scoping import (  # noqa: E402
    apply_tenant_filter,
    get_current_tenant,
    has_tenant_column,
    is_system_tenant,
)


def test_task_has_tenant_column() -> None:
    assert has_tenant_column(Task)


def test_knowledge_document_has_tenant_column() -> None:
    assert has_tenant_column(KnowledgeDocument)


def test_task_inherits_tenant_mixin() -> None:
    assert issubclass(Task, TenantMixin)


def test_knowledge_document_inherits_tenant_mixin() -> None:
    assert issubclass(KnowledgeDocument, TenantMixin)


def test_tenant_mixin_default_uses_context_var() -> None:
    from aeo_api.db.tenant_models import _get_tenant_id

    tid = str(uuid4())
    token = current_tenant_id.set(tid)
    try:
        assert _get_tenant_id() == tid
    finally:
        current_tenant_id.reset(token)


def test_tenant_mixin_default_falls_back_to_system() -> None:
    from aeo_api.db.tenant_models import _get_tenant_id

    token = current_tenant_id.set(None)
    try:
        assert _get_tenant_id() == SYSTEM_TENANT_ID
    finally:
        current_tenant_id.reset(token)


def test_get_current_tenant_returnss_context_value() -> None:
    tid = str(uuid4())
    token = current_tenant_id.set(tid)
    try:
        assert get_current_tenant() == tid
    finally:
        current_tenant_id.reset(token)


def test_get_current_tenant_falls_back_to_system() -> None:
    token = current_tenant_id.set(None)
    try:
        assert get_current_tenant() == SYSTEM_TENANT_ID
    finally:
        current_tenant_id.reset(token)


def test_is_system_tenant_true_for_system() -> None:
    token = current_tenant_id.set(SYSTEM_TENANT_ID)
    try:
        assert is_system_tenant() is True
    finally:
        current_tenant_id.reset(token)


def test_is_system_tenant_false_for_other() -> None:
    token = current_tenant_id.set(str(uuid4()))
    try:
        assert is_system_tenant() is False
    finally:
        current_tenant_id.reset(token)


def test_apply_tenant_filter_skips_system_tenant() -> None:
    from sqlalchemy import select

    token = current_tenant_id.set(SYSTEM_TENANT_ID)
    try:
        stmt = select(Task)
        filtered = apply_tenant_filter(stmt)
        assert filtered is stmt
    finally:
        current_tenant_id.reset(token)


def test_apply_tenant_filter_adds_where_for_tenant() -> None:
    from sqlalchemy import select

    tid = str(uuid4())
    token = current_tenant_id.set(tid)
    try:
        stmt = select(Task)
        filtered = apply_tenant_filter(stmt)
        compiled = str(filtered.compile(compile_kwargs={"literal_binds": True}))
        assert "tenant_id" in compiled
        assert tid in compiled
    finally:
        current_tenant_id.reset(token)


def test_has_tenant_column_false_for_plain_model() -> None:
    from aeo_api.db.models import TaskCheckpoint

    assert has_tenant_column(TaskCheckpoint) is False


def test_audit_log_has_tenant_column() -> None:
    from aeo_api.db.models import AuditLog

    assert has_tenant_column(AuditLog)
    assert issubclass(AuditLog, TenantMixin)


def test_competitor_listing_has_tenant_column() -> None:
    from aeo_api.db.models import CompetitorListing

    assert has_tenant_column(CompetitorListing)
    assert issubclass(CompetitorListing, TenantMixin)


def test_selection_score_has_tenant_column() -> None:
    from aeo_api.db.models import SelectionScore

    assert has_tenant_column(SelectionScore)
    assert issubclass(SelectionScore, TenantMixin)


def test_intelligence_schedule_has_tenant_column() -> None:
    from aeo_api.db.models import IntelligenceSchedule

    assert has_tenant_column(IntelligenceSchedule)
    assert issubclass(IntelligenceSchedule, TenantMixin)


def test_apply_tenant_filter_on_audit_log() -> None:
    from aeo_api.db.models import AuditLog
    from sqlalchemy import select

    tid = str(uuid4())
    token = current_tenant_id.set(tid)
    try:
        stmt = select(AuditLog)
        filtered = apply_tenant_filter(stmt)
        compiled = str(filtered.compile(compile_kwargs={"literal_binds": True}))
        assert "tenant_id" in compiled
        assert tid in compiled
    finally:
        current_tenant_id.reset(token)
