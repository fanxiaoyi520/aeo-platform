# M01 — 基础设施与工程化

| 属性 | 值 |
|------|-----|
| **模块 ID** | M01 |
| **优先级** | P0 |
| **里程碑** | MS1（W1–W2） |
| **状态** | `blocked`（等待总计划批准） |
| **依赖** | 无 |
| **规范依据** | `03_DEV_ENVIRONMENT.md`、`04_ARCHITECTURE_STANDARDS.md`、`05_PERFORMANCE_STANDARDS.md` |

---

## 1. 目标

建立生产级 Monorepo 工程底座，**严格按统一规范**落地开发环境、架构分层与性能基线配置，使后续模块可在统一规范下并行开发。

## 2. 交付物

- [ ] `launch-aeo/` Monorepo 目录结构（符合 `04` §4 包职责）
- [ ] `docker-compose.dev.yml` 一键启动，端口符合 `03` §7
- [ ] FastAPI 应用：`/health`、`/ready` 端点（P-API-04：p95 ≤ 50ms）
- [ ] Alembic 数据库迁移框架 + `04` §6.2 索引
- [ ] `LLMProvider` 接口 + OpenAI 兼容实现（`LLM_TIMEOUT_SECONDS=45`）
- [ ] 统一响应格式 + 错误码（`packages/shared/errors.py`，`04` §5）
- [ ] `scripts/setup.ps1` / `setup.sh` / `dev-up` / `test`（`03` §6）
- [ ] `.env.example` 全部 `APP_/DB_/LLM_` 前缀变量（`03` §5）
- [ ] CI：ruff + mypy + pytest + docker build（`03` §8）
- [ ] prod compose 资源 limits（`05` §3.1）
- [ ] Prometheus `/metrics` 骨架（`05` §10）

## 3. 技术规范

### 3.1 Python 包管理

- 使用 **uv `0.4.18`**（见 `03_DEV_ENVIRONMENT.md` §2、§4.1）
- 工作区：`apps/api`、`apps/orchestrator`、`apps/browser`、`packages/*`
- 锁文件：`uv.lock` 提交 Git

### 3.2 数据库初始表（MS1 范围）

```sql
-- tasks: 运营任务主表
-- task_checkpoints: LangGraph 检查点元数据
-- audit_logs: HITL 与敏感操作审计
-- knowledge_documents: RAG 文档元数据
```

详细 Schema 在 S1-03 任务中输出 ADR-001。

### 3.3 LLMProvider 接口

```python
class LLMProvider(Protocol):
    async def chat(self, messages: list[Message], **kwargs) -> str: ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
```

实现：`OpenAICompatibleProvider`（支持 base_url 指向内网网关）。

### 3.4 API 规范

- 统一响应：`{ "code": 0, "data": {}, "request_id": "uuid" }`
- 错误码区间：1xxxx 客户端 / 2xxxx 业务 / 5xxxx 系统

## 4. 验收标准

1. `docker compose -f infra/compose/docker-compose.dev.yml up` 全部 healthy
2. `curl localhost:8000/health` 返回 200，p95 ≤ 50ms
3. `scripts/test.ps1` 通过（ruff + mypy + pytest）
4. 切换 `LLM_BASE_URL` 环境变量可指向不同网关
5. API 响应格式符合 `04` §5.2，错误码从 `packages/shared/errors.py` 引用
6. prod compose 包含 `05` §3.1 资源 limits

## 5. 不在本模块范围

- Agent 业务逻辑（M03）
- 前端（M05）
