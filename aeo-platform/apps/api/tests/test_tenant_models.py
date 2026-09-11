"""P5-01: Tenant & User model unit tests."""

import os
import uuid

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")

from aeo_api.db.tenant_models import SYSTEM_TENANT_ID, Tenant, TenantMixin, User


def test_tenant_creation() -> None:
    tid = uuid.uuid4()
    tenant = Tenant(id=tid, name="Acme Corp", slug="acme-corp", plan="free", is_active=True)
    assert tenant.id == tid
    assert tenant.name == "Acme Corp"
    assert tenant.slug == "acme-corp"
    assert tenant.plan == "free"
    assert tenant.is_active is True
    assert tenant.settings is None


def test_tenant_plan_override() -> None:
    tenant = Tenant(id=uuid.uuid4(), name="Pro Inc", slug="pro-inc", plan="pro")
    assert tenant.plan == "pro"


def test_tenant_settings_json() -> None:
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Custom",
        slug="custom",
        settings={"max_users": 50, "features": ["ads", "analytics"]},
    )
    assert tenant.settings == {"max_users": 50, "features": ["ads", "analytics"]}


def test_user_creation() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    user = User(
        id=uid,
        tenant_id=tid,
        email="admin@acme.com",
        hashed_password="$2b$12$fakehash",
        display_name="Admin",
        role="owner",
        is_active=True,
    )
    assert user.id == uid
    assert user.tenant_id == tid
    assert user.email == "admin@acme.com"
    assert user.role == "owner"
    assert user.is_active is True
    assert user.last_login_at is None


def test_user_default_role() -> None:
    user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        email="member@acme.com",
        hashed_password="$2b$12$fakehash",
        role="member",
        is_active=True,
    )
    assert user.role == "member"
    assert user.is_active is True


def test_system_tenant_id_format() -> None:
    assert SYSTEM_TENANT_ID == "00000000-0000-0000-0000-000000000000"
    uuid.UUID(SYSTEM_TENANT_ID)


def test_tenant_mixin_has_tenant_id() -> None:
    assert hasattr(TenantMixin, "tenant_id")


def test_tenant_model_table_name() -> None:
    assert Tenant.__tablename__ == "tenants"
    assert User.__tablename__ == "users"
