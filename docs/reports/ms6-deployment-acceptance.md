# MS6 生产加固验收报告

| 属性 | 值 |
|------|-----|
| **里程碑** | MS6 |
| **任务** | S6-06 |
| **验收日期** | 2026-08-30 |
| **自动化** | `test.ps1` **126/126**（含 `test_ms6_acceptance.py` 20 项 + S6-01~05 专项测试） |
| **结论** | **通过**（用户于 2026-08-30 批准 MS6） |

---

## 1. 验收范围（M06 §5）

| # | 标准 | 结果 | 证据 |
|---|------|------|------|
| 1 | prod compose 可无外网 Embedding 启动 | ✅ | `RAG_USE_HASH_EMBEDDINGS=true`；`prod-up.ps1` 默认 hash ingest |
| 2 | 未认证 API 请求返回 401 | ✅ | `test_ms6_unauthenticated_api_returns_401`；`ApiKeyMiddleware` |
| 3 | 审计日志可查询最近 100 条 HITL 操作 | ✅ | `GET /api/v1/audit-logs`；`limit` 最大 100 |
| 4 | `backup.sh` 可备份 PostgreSQL + Chroma | ✅ | `pg_dump` + `chroma_data.tar.gz`；见 `DEPLOYMENT.md` §4 |

---

## 2. Sprint 8 任务交付清单

| 任务 | 交付物 | 状态 |
|------|--------|------|
| S6-01 | `docker-compose.prod.yml`、web Dockerfile、`prod-up/down.ps1` | ✅ PR #4 |
| S6-02 | API Key 认证、Redis 限流 100/min、CORS 白名单 | ✅ PR #5 |
| S6-03 | structlog 脱敏、`GET /api/v1/audit-logs`、reindex 审计 | ✅ PR #6 |
| S6-04 | 覆盖率门禁 ≥70%（实际 **86%**） | ✅ PR #7 |
| S6-05 | `docs/DEPLOYMENT.md`、`backup.sh`、`demo.ps1` | ✅ PR #8 |
| S6-06 | 本验收报告 + `test_ms6_acceptance.py` | ✅ 本 PR |

---

## 3. 安全控制核对（M06 §3–§4）

| 控制项 | 实现 | 验证 |
|--------|------|------|
| 密钥仅环境变量 | `.env.prod` gitignore | `test_ms6_env_prod_example_documents_security_controls` |
| 数据库不暴露公网 | postgres/redis 无 host ports | `test_prod_compose_internal_data_services_have_no_host_ports` |
| 生产默认 Key 拒绝启动 | `validate_production_settings` | `test_production_rejects_default_api_key` |
| 限流 100 req/min | `RateLimitMiddleware` | `test_rate_limit_returns_429_after_limit` |
| 日志脱敏四字段 | `aeo_shared.redaction` | `test_ms6_redaction_keys_match_m06_spec` |
| HITL 审计 | `audit_logs` 表 + API | `test_list_audit_logs_defaults_to_hitl_actions` |

---

## 4. 手动抽测步骤（推荐）

```powershell
cd aeo-platform
copy .env.prod.example .env.prod   # 修改 AUTH_API_KEY、POSTGRES_PASSWORD
.\scripts\prod-up.ps1
.\scripts\demo.ps1
.\scripts\backup.ps1
```

1. 确认 `demo.ps1` 五项冒烟全绿  
2. 浏览器打开 `http://127.0.0.1:3000/tasks/new` 完成 HITL 流程  
3. 检查 `backups/` 目录含 `postgres.sql` 与 `chroma_data.tar.gz`  
4. Swagger `GET /api/v1/audit-logs` 返回 HITL 记录  

---

## 5. 不在 MS6 范围（已知）

- K8s / 云托管、TLS 终止（见 `DEPLOYMENT.md` §9）
- 多用户 / SSO
- SOC2 / 等保认证
- MS7 试点 SKU 批量运行与演示视频

---

## 6. 签核

- **技术验收：** S6-06 自动化通过（2026-08-30）
- **里程碑关闭：** 用户于 2026-08-30 批准 MS6
