# P7-22 Multi-Tenant Isolation Audit

> **Status:** `COMPLETE` (2026-09-18)
> **Auditor:** AI Agent (auto)
> **Scope:** `apps/api/src/aeo_api`, `packages/shared`, `packages/integrations`

---

## 1. Architecture

| Layer | Mechanism |
|-------|-----------|
| **Context injection** | `AuthMiddleware` (`apps/api/src/aeo_api/middleware/auth.py`) decodes JWT, sets `tenant_id` on `request.state` and into `ContextVar` via `auth/context.py`. |
| **RBAC dependencies** | `auth/rbac.py` exposes `CurrentTenant` / `CurrentRole` as FastAPI dependencies. |
| **Central filter helper** | `db/tenant_scoping.apply_tenant_filter()` auto-adds `WHERE tenant_id = :tid` to any SQLAlchemy `Select` whose entity has a `tenant_id` column. System tenant bypasses the filter. |
| **Mixin** | `db/tenant_models.TenantMixin` auto-fills `tenant_id` from the context var on INSERT. |

## 2. Tenant-scoped models

| File | Models | Mechanism |
|------|--------|-----------|
| `db/tenant_models.py` | `Tenant`, `User`, `TenantMixin` | Core: `User.tenant_id` FK; `TenantMixin` auto-fills from context var |
| `db/models.py` | `Task`, `AuditLog`, `KnowledgeDocument`, `CompetitorListing`, `SelectionScore`, `IntelligenceSchedule` | All inherit `TenantMixin` |
| `db/amazon_credential.py` | `AmazonCredential` | Explicit `tenant_id` FK |
| `db/shopify_credential.py` | `ShopifyCredential` | Explicit `tenant_id` FK |
| `billing/models.py` | `Subscription`, `Invoice` | Explicit `tenant_id` FK |

## 3. Files that filter by tenant_id

| File | Surface |
|------|---------|
| `services/task_service.py` | `list_tasks` uses `apply_tenant_filter`; `_get_task` manually checks `task.tenant_id != get_current_tenant()` |
| `routers/intelligence.py` | `list_schedules` uses `apply_tenant_filter`; `delete_schedule` manually checks `row.tenant_id` |
| `routers/selection.py` | `list_competitors`, `list_scores` use `apply_tenant_filter` |
| `services/audit_service.py` | `list_logs`, `list_risk_logs` use `apply_tenant_filter` |
| `routers/amazon_credentials.py` | All queries filter `AmazonCredential.tenant_id == tenant_id` |
| `routers/shopify_credentials.py` | All queries filter `ShopifyCredential.tenant_id == tenant_id` |
| `routers/billing.py` | Subscription/invoice queries filter by `tenant_id` |
| `auth/tenant_service.py` | All member queries scoped by `tenant_id` |

## 4. Tenant isolation tests

| Test file | Coverage |
|-----------|----------|
| `tests/test_tenant_scoping.py` | 14 tests covering `apply_tenant_filter`, `has_tenant_column`, mixin defaults, system-tenant bypass |
| `tests/test_tenant_models.py` | Model-level tenant column assertions |
| `tests/test_tenant_admin.py` | Tenant admin endpoint tests |
| `tests/test_tenant_quota.py` | Quota enforcement tests |
| `tests/test_auth_middleware.py` | Middleware tenant context injection |

## 5. Identified gaps

### 5.1 `IntelligenceSchedule.create_schedule` — job_id uniqueness cross-tenant leak

**Location:** `routers/intelligence.py` (create_schedule handler)
**Issue:** The `job_id` uniqueness check queries `IntelligenceSchedule.job_id == body.job_id` **without a tenant filter**. One tenant can block another from creating a schedule with the same `job_id`.
**Severity:** Medium (functional bug, not data leak)
**Fix:** Add `IntelligenceSchedule.tenant_id == tenant_id` to the uniqueness check.

### 5.2 Models missing `tenant_id` entirely

| Model | Risk | Notes |
|-------|------|-------|
| `ListingVersion` | **HIGH** | Written by listing saver closure in `task_service.py` without tenant scoping. If queried directly, data could leak across tenants. |
| `OrderRecord` | Medium | Currently mock/placeholder. Needs tenant scoping before production use. |
| `AdCampaign` | Medium | Currently mock/placeholder. |
| `AdSpendSnapshot` | Medium | Currently mock/placeholder. |
| `TaskCheckpoint` | Low | Tied to `Task` which is scoped; indirect isolation. |

### 5.3 No automatic enforcement

`apply_tenant_filter` is **opt-in per query**. There is no SQLAlchemy session-level event listener or PostgreSQL row-level security policy to catch queries that forget the filter. Any new endpoint that queries a `TenantMixin` model must remember to call `apply_tenant_filter` manually.

**Mitigation options:**
1. Add a SQLAlchemy `before_compile` session event that asserts tenant filter on `TenantMixin` entities.
2. Add PostgreSQL RLS policies for production (requires per-tenant connection setup).
3. Add a CI lint rule that greps for raw queries on `TenantMixin` models without `apply_tenant_filter`.

## 6. Recommendations

1. **P0 (this phase):** Fix `IntelligenceSchedule.job_id` uniqueness check to include tenant filter.
2. **P0 (this phase):** Add `tenant_id` column to `ListingVersion` and scope the listing saver.
3. **P1 (P7-MS4 follow-up):** Add `tenant_id` to `OrderRecord`, `AdCampaign`, `AdSpendSnapshot` before real data flows.
4. **P2 (future):** Implement SQLAlchemy `before_compile` enforcement or PostgreSQL RLS.
5. **P2 (future):** Add a CI lint rule to catch missing tenant filters on new endpoints.

## 7. Test plan (for fixes)

- [ ] Add a test that creates `IntelligenceSchedule` with the same `job_id` in two tenants → both should succeed.
- [ ] Add a test that creates `ListingVersion` in tenant A and verifies tenant B cannot read it.
- [ ] Extend `test_tenant_scoping.py` to cover all `TenantMixin` models.
