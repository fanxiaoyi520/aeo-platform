# 统一架构规范（Architecture Standards）

| 属性 | 值 |
|------|-----|
| **版本** | v1.0.0 |
| **状态** | `DRAFT` — 随总计划一并审核 |
| **约束力** | 全项目强制统一，所有模块必须遵守 |

---

## 1. 架构原则

| # | 原则 | 说明 |
|---|------|------|
| A1 | **分层清晰** | 表现层 → 应用层 → 领域层 → 基础设施层，禁止跨层直调 |
| A2 | **单一职责** | 每个服务/包只做一件事；Agent 只做推理编排，不直接访问 DB |
| A3 | **接口契约** | 模块间仅通过定义的 API / 事件 / 共享类型通信 |
| A4 | **可替换** | LLM、向量库、浏览器通过 Adapter 抽象，禁止硬编码供应商 |
| A5 | **可观测** | 每个请求有 `request_id`；每个 Agent 步骤有 `trace_id` |
| A6 | **失败显式** | 降级、重试、熔断必须写入状态与日志，禁止静默吞错 |
| A7 | **数据本地** | 默认本地持久化，外呼仅限 LLM API（可配置内网） |

---

## 2. 物理部署架构

```
                    ┌─────────────────────────────────────┐
                    │         Host（Linux / Win+Docker）    │
                    │  ┌───────────────────────────────┐  │
                    │  │  docker network: aeo-internal │  │
                    │  │                               │  │
  Browser ──HTTP──► │  │  ┌─────┐    ┌─────┐           │  │
  (运营人员)        │  │  │ web │───►│ api │           │  │
                    │  │  │:3000│    │:8000│           │  │
                    │  │  └──┬──┘    └──┬──┘           │  │
                    │  │     │          │               │  │
                    │  │     │     ┌────▼────────────┐  │  │
                    │  │     │     │  orchestrator │  │  │
                    │  │     │     │  (api 内嵌)    │  │  │
                    │  │     │     └────┬────────────┘  │  │
                    │  │     │          │               │  │
                    │  │  ┌──▼──┐  ┌────▼───┐  ┌──────┐ │  │
                    │  │  │redis│  │postgres│  │chroma│ │  │
                    │  │  └─────┘  └────────┘  └──────┘ │  │
                    │  │          ┌──────────┐           │  │
                    │  │          │ browser  │           │  │
                    │  │          │(playwright)          │  │
                    │  │          └──────────┘           │  │
                    │  └───────────────────────────────┘  │
                    │  volumes: pg_data, chroma_data,    │
                    │           screenshots, knowledge     │
                    └─────────────────────────────────────┘
                              │
                              ▼
                    LLM API（内网网关 / OpenAI 兼容）
```

**首期部署形态：** `api` 进程内嵌 `orchestrator` + 调用 `browser` 模块（同容器或 sidecar），**不拆微服务**，降低运维复杂度。Phase 2 可按负载拆分。

---

## 3. 逻辑分层架构

```
┌─────────────────────────────────────────────────────────────┐
│ L1  Presentation — apps/web                                  │
│     Pages / Components / API Client / SSE Hooks              │
├─────────────────────────────────────────────────────────────┤
│ L2  Application  — apps/api/routers, apps/api/services       │
│     REST 路由、鉴权、DTO 校验、事务边界、SSE 推送              │
├─────────────────────────────────────────────────────────────┤
│ L3  Domain       — apps/orchestrator, apps/browser           │
│     Agent 图、业务规则、合规检查、任务状态机                    │
├─────────────────────────────────────────────────────────────┤
│ L4  Infrastructure — packages/llm, packages/shared, adapters  │
│     DB Repo、RAG、LLM、Playwright、Redis、文件存储             │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 调用规则（强制）

| 从 | 到 | 允许 |
|----|-----|------|
| L1 web | L2 api | ✅ HTTP/SSE only |
| L2 api | L3 orchestrator | ✅ Service 接口 |
| L2 api | L4 infra | ✅ Repository / Adapter |
| L3 orchestrator | L4 infra | ✅ Tool / Adapter |
| L3 orchestrator | L2 api router | ❌ 禁止 |
| L1 web | L3/L4 | ❌ 禁止直连 |
| L4 | L3 | ❌ 禁止 |

---

## 4. 包职责划分（统一）

| 包/应用 | 职责 | 禁止 |
|---------|------|------|
| `apps/web` | UI、用户交互、SSE 消费 | 业务逻辑、直接调 LLM |
| `apps/api` | HTTP 入口、鉴权、DTO、编排调用 | Agent 图定义 |
| `apps/orchestrator` | LangGraph 图、Agent 节点、状态机 | HTTP 路由 |
| `apps/browser` | Playwright 封装、页面解析 | 业务决策 |
| `packages/shared` | 共享类型、常量、错误码、工具函数 | 业务逻辑 |
| `packages/llm` | LLMProvider、EmbeddingProvider | 业务 Prompt（Prompt 模板放 orchestrator） |

---

## 5. API 设计规范（统一）

### 5.1 URL 规范

```
/api/v1/{resource}
/api/v1/{resource}/{id}
/api/v1/{resource}/{id}/{action}
```

**资源命名：** 复数、kebab-case

| 资源 | 路径示例 |
|------|----------|
| 任务 | `/api/v1/tasks` |
| 知识库 | `/api/v1/knowledge/documents` |
| 指标 | `/api/v1/metrics/summary` |
| 健康 | `/health`, `/ready`（无版本前缀） |

### 5.2 统一响应格式

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 5.3 统一错误码

| 区间 | 含义 | 示例 |
|------|------|------|
| `0` | 成功 | — |
| `10001–19999` | 客户端错误 | `10001` 参数校验失败 |
| `20001–29999` | 业务错误 | `20001` 任务不存在 |
| `20010–20019` | Agent 错误 | `20010` Agent 超时 |
| `20020–20029` | HITL 错误 | `20020` 任务非待审核状态 |
| `50001–59999` | 系统错误 | `50001` 数据库不可用 |

完整错误码表在 `packages/shared/errors.py` 维护，**禁止各模块自定义重复码**。

### 5.4 分页规范

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

Query：`?page=1&page_size=20&sort=-created_at`

---

## 6. 数据架构（统一模型）

### 6.1 核心实体关系

```
tasks 1───N task_checkpoints
tasks 1───N listing_versions
tasks 1───1 task_metrics
tasks 1───N audit_logs
knowledge_documents 1───N knowledge_chunks（逻辑，向量在 Chroma）
```

### 6.2 命名规范

| 层 | 规范 | 示例 |
|----|------|------|
| 数据库表 | snake_case 复数 | `tasks`, `audit_logs` |
| 列名 | snake_case | `created_at`, `task_id` |
| Python 模型 | PascalCase | `Task`, `AuditLog` |
| Python 字段 | snake_case | `task_id` |
| TypeScript 类型 | PascalCase | `Task`, `TaskStatus` |
| API JSON | snake_case | 与 Python 一致 |
| 环境变量 | UPPER_SNAKE | `DB_URL` |

**前后端字段统一 snake_case**，禁止 API 层 camelCase 与 DB 不一致。

### 6.3 时间与时区

- 数据库存 **UTC**（`TIMESTAMPTZ`）
- API 返回 ISO 8601 UTC：`2026-08-29T01:30:00Z`
- 前端按用户本地时区展示

### 6.4 主键策略

- 全部使用 **UUID v4**（`uuid` 类型），禁止自增 ID 对外暴露

---

## 7. Agent 架构规范

### 7.1 目录结构

```
apps/orchestrator/
├── graph.py              # 图定义与编译
├── state.py              # TaskState 类型
├── nodes/
│   ├── research.py
│   ├── rules.py
│   ├── generate.py
│   ├── compliance.py
│   └── review.py
├── tools/
│   ├── rag_tool.py
│   └── browser_tool.py
├── prompts/
│   ├── amazon.py
│   └── tiktok.py
└── checkpoints/
    └── postgres_saver.py
```

### 7.2 Agent 节点规范

每个节点必须：

1. 接收 `TaskState`，返回 `TaskState` 部分更新
2. 记录 `AgentTraceEvent` 到 `state.trace`
3. 设置超时（见 `05_PERFORMANCE_STANDARDS.md`）
4. 捕获异常 → 写入 `state.error` + 触发重试/降级策略
5. **禁止**节点内直接 HTTP 调外部 API（须经 Tool/Adapter）

### 7.3 Tool 规范

```python
@tool
async def rag_search(query: str, platform: str, top_k: int = 5) -> list[Document]:
    """检索知识库。platform: amazon|tiktok|general"""
```

- 所有 Tool 须有 docstring（供 LLM 理解）
- 输入输出须 Pydantic 校验
- Tool 注册在 `tools/__init__.py` 统一导出

---

## 8. 事件与实时通信

| 场景 | 方案 | 说明 |
|------|------|------|
| Agent Trace 推送 | **SSE** | `GET /api/v1/tasks/{id}/events` |
| 任务状态变更 | SSE 事件 `task.updated` | 禁止 WebSocket（首期） |
| 异步任务执行 | Redis 队列 + Worker | api 投递，orchestrator 消费 |
| 模块间同步调用 | Python async 函数 | 同进程内 |

**SSE 事件格式：**

```json
{
  "event": "agent.step",
  "data": {
    "task_id": "uuid",
    "agent": "research_agent",
    "status": "completed",
    "timestamp": "2026-08-29T01:30:00Z",
    "detail": {}
  }
}
```

---

## 9. 缓存策略（统一）

| 数据 | 缓存 | TTL | 键格式 |
|------|------|-----|--------|
| RAG 检索结果 | Redis | 1h | `rag:{hash(query)}` |
| 竞品 Listing | Redis | 24h | `browser:asin:{asin}` |
| 任务状态（热） | Redis | 任务生命周期 | `task:{id}:state` |
| LLM 响应 | 不缓存 | — | 内容具有随机性 |

---

## 10. 安全架构（摘要，详见 M06）

```
Request → API Key 校验 → 限流 → 路由 → 业务 → 审计日志
                ↓
         敏感字段脱敏后写日志
```

- 首期单用户 API Key，存 `AUTH_API_KEY` 环境变量
- 前端通过 Next.js API Route 或 Bearer Token 代理（避免 Key 暴露浏览器）

---

## 11. ADR（架构决策记录）流程

重大决策须写 `docs/adr/NNNN-title.md`：

| 必须写 ADR 的情况 |
|-------------------|
| 更换技术栈组件 |
| 拆分/合并服务 |
| 更改 API 版本或响应格式 |
| 更改数据库 Schema 破坏性迁移 |

模板：

```markdown
# ADR-0001: 标题
- 状态: 已接受 / 已废弃
- 背景:
- 决策:
- 后果:
```

---

## 12. 验收标准

- [ ] 所有模块目录符合 §4 职责划分
- [ ] API 响应格式符合 §5.2
- [ ] 错误码统一从 `packages/shared/errors.py` 引用
- [ ] Agent 节点符合 §7.2 五项要求
- [ ] 无跨层违规调用（Code Review 检查）
