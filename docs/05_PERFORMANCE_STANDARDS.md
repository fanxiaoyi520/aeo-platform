# 统一性能规范（Performance Standards）

| 属性 | 值 |
|------|-----|
| **版本** | v1.0.0 |
| **状态** | `DRAFT` — 随总计划一并审核 |
| **约束力** | 全项目强制统一；未达标不得标记里程碑完成 |

---

## 1. 性能目标总览

### 1.1 业务 SLA（用户可感知）

| 指标 ID | 场景 | 目标 (p95) | 目标 (p99) | 测量点 |
|---------|------|------------|------------|--------|
| **P-BIZ-01** | 单任务端到端（含浏览器调研） | **≤ 180s** | ≤ 300s | 任务 create → completed |
| **P-BIZ-02** | 单任务端到端（降级模式，无浏览器） | **≤ 60s** | ≤ 90s | 同上 |
| **P-BIZ-03** | HITL 审核页加载 | ≤ 2s | ≤ 4s | 前端 FCP |
| **P-BIZ-04** | Agent Trace SSE 延迟 | ≤ 2s | ≤ 5s | 节点完成 → 前端收到事件 |
| **P-BIZ-05** | 知识库检索 | ≤ 500ms | ≤ 1s | RAG API |
| **P-BIZ-06** | 任务列表页（20 条） | ≤ 1s | ≤ 2s | API + 渲染 |

### 1.2 API SLA

| 指标 ID | 端点类型 | 目标 (p95) | 目标 (p99) |
|---------|----------|------------|------------|
| **P-API-01** | 读操作（GET 单条） | ≤ 200ms | ≤ 500ms |
| **P-API-02** | 读操作（GET 列表） | ≤ 500ms | ≤ 1s |
| **P-API-03** | 写操作（POST/PATCH） | ≤ 1s | ≤ 2s |
| **P-API-04** | 健康检查 `/health` | ≤ 50ms | ≤ 100ms |

> **p95 / p99**：生产环境或压测报告中的百分位延迟。

### 1.3 可用性 SLA

| 指标 ID | 目标 | 说明 |
|---------|------|------|
| **P-AVL-01** | 核心 API 月度可用性 ≥ **99.5%** | 试点期按 7×24 本地部署统计 |
| **P-AVL-02** | 计划内重启恢复 ≤ **60s** | `docker compose up` 后全服务 ready |
| **P-AVL-03** | 单任务失败可重试成功率 ≥ **95%** | 含自动重试后 |

---

## 2. Agent 节点超时（强制）

| Agent | 超时 | 重试次数 | 退避策略 |
|-------|------|----------|----------|
| `research_agent` | **120s** | 2 | 指数退避 2s/4s |
| `rules_agent` | **30s** | 2 | 固定 1s |
| `generate_agent` | **60s** | 2 | 固定 2s |
| `compliance_agent` | **15s** | 0（逻辑重试走回流） | — |
| `review_agent` | **10s** | 2 | 固定 1s |
| **整图总超时** | **300s** | — | 超时 → 任务 `failed` |

**LLM 单次调用超时：** 45s（`LLM_TIMEOUT_SECONDS=45`）

---

## 3. 资源配额（单实例）

### 3.1 容器资源限制（prod compose）

| 服务 | CPU limit | Memory limit | Memory reservation |
|------|-----------|--------------|-------------------|
| `api` | 2 core | **2 GB** | 1 GB |
| `web` | 1 core | **512 MB** | 256 MB |
| `postgres` | 1 core | **1 GB** | 512 MB |
| `redis` | 0.5 core | **256 MB** | 128 MB |
| `browser`（worker） | 1 core | **1 GB** | 512 MB |

### 3.2 并发限制

| 项 | 限制 | 配置项 |
|----|------|--------|
| 同时运行 Agent 任务 | **3** | `AGENT_MAX_CONCURRENT=3` |
| Playwright 浏览器上下文 | **2** | `BROWSER_MAX_CONTEXTS=2` |
| API 请求（全局限流） | **100 req/min** | `RATE_LIMIT_PER_MINUTE=100` |
| 单用户同时 SSE 连接 | **5** | — |
| RAG ingest 批量 | **10 文档/批次** | — |
| 竞品抓取 / 任务 | **5 ASIN** | M04 已定义 |

**超出并发：** 返回 `20030` 任务队列已满，客户端提示稍后重试。

---

## 4. 数据库性能规范

### 4.1 连接池

| 参数 | 值 |
|------|-----|
| `pool_size` | 10 |
| `max_overflow` | 5 |
| `pool_timeout` | 30s |
| `pool_recycle` | 1800s |

### 4.2 索引要求（Sprint 1 Schema 必须包含）

```sql
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX idx_audit_logs_task_id ON audit_logs(task_id);
CREATE INDEX idx_listing_versions_task_id ON listing_versions(task_id);
```

### 4.3 查询规范

| 规则 | 说明 |
|------|------|
| 禁止 N+1 | 列表查询用 JOIN 或批量加载 |
| 分页必选 | 默认 `page_size=20`，最大 `100` |
| 慢查询阈值 | **> 500ms** 记 WARN 日志 |
| 大字段 | `trace`/`generated` 用 JSONB，列表接口不返回 |

---

## 5. 缓存与 RAG 性能

| 项 | 目标 | 实现 |
|----|------|------|
| RAG 检索 p95 | ≤ 500ms | Redis 缓存 + Chroma 本地 SSD |
| Embedding 批量 | ≤ 2s / 10 条 | 批量 API 调用 |
| 知识库规模（首期） | ≤ 500 文档 / 5 万 chunk | 超出须评估分片 |
| Chroma 查询 `top_k` | 默认 5，最大 20 | 配置项 |

---

## 6. 浏览器自动化性能

| 项 | 目标 |
|----|------|
| 单 ASIN 抓取 p95 | ≤ 30s |
| 单任务 5 ASIN 总耗时 p95 | ≤ 90s |
| 请求间隔 | ≥ 3s（反爬） |
| 截图大小 | ≤ 500 KB（JPEG 压缩） |
| 截图保留 | 30 天自动清理（cron 脚本） |

---

## 7. 前端性能

| 指标 | 目标 | 工具 |
|------|------|------|
| Lighthouse Performance | ≥ **80** | Chrome Lighthouse（桌面） |
| LCP | ≤ 2.5s | Core Web Vitals |
| 首屏 JS bundle | ≤ **300 KB** gzip | Next.js analyzer |
| 图片 | WebP/AVIF，懒加载 | — |
| SSE 重连 | 断线 3s 内自动重连，最多 5 次 | 前端 Hook |

---

## 8. LLM 调用性能与成本

| 项 | 规范 |
|----|------|
| 单次 max_tokens | `generate`: 2048；`compliance`: 512 |
| 上下文窗口控制 | 注入 RAG 结果 ≤ 4K tokens |
| 流式输出 | `generate_agent` 使用 streaming（降低首字延迟） |
| Token 计量 | 每次调用记录 `tokens_in/out` 到 `task_metrics` |
| 单任务 Token 上限 | **30K tokens**（超出中止并标记 `token_limit_exceeded`） |

---

## 9. 压测与验收流程

### 9.1 压测工具

| 工具 | 用途 |
|------|------|
| **locust** | API 压测（`tests/load/`） |
| **pytest-benchmark** | 单函数基准 |
| 自定义脚本 | Agent 端到端批量跑批 |

### 9.2 里程碑压测要求

| 里程碑 | 压测内容 | 通过标准 |
|--------|----------|----------|
| MS1 | `/health` + 任务 CRUD 空跑 | P-API-01/02 达标 |
| MS2 | RAG 检索 100 并发查询 | P-BIZ-05 达标 |
| MS3 | 10 任务顺序执行（mock LLM） | P-BIZ-02 达标 |
| MS4 | 5 ASIN 抓取 × 10 轮 | 浏览器 §6 达标 |
| MS6 | 3 并发 Agent 任务 × 1h 稳定性 | P-AVL-01/03 达标 |
| MS7 | 20 SKU 试点批跑 | P-BIZ-01 达标 |

### 9.3 压测报告模板

存放：`docs/reports/perf-{milestone}-{date}.md`

```markdown
# 性能报告 MSx
- 环境：CPU / 内存 / 磁盘
- 并发数：
- 结果表：指标 ID / 目标 / 实测 p95 / 是否通过
- 瓶颈分析：
- 优化项（如有）：
```

---

## 10. 监控与告警阈值

| 指标 | WARN | CRITICAL |
|------|------|----------|
| API p95 延迟 | > 目标 × 1.5 | > 目标 × 3 |
| Agent 任务失败率（1h） | > 10% | > 30% |
| Redis 内存使用 | > 70% | > 90% |
| PostgreSQL 连接数 | > 80% pool | 连接超时 |
| 磁盘使用（data 卷） | > 70% | > 85% |
| LLM 调用错误率（1h） | > 5% | > 20% |

Prometheus metrics 命名：`aeo_{subsystem}_{metric}_{unit}`  
示例：`aeo_api_request_duration_seconds`, `aeo_agent_task_total`

---

## 11. 性能优化优先级（开发约束）

遇到性能问题时，**按此顺序**优化，禁止跳过：

1. 算法/查询优化（索引、N+1、分页）
2. 缓存（Redis，见架构 §9）
3. 异步/队列（超并发任务排队）
4. 资源扩容（Docker limits）
5. 架构拆分（仅 Phase 2，须 ADR）

---

## 12. 验收标准

- [ ] `05_PERFORMANCE_STANDARDS.md` 所有 P-* 指标在 MS6 前有过压测记录
- [ ] Agent 超时配置可从环境变量读取，与 §2 一致
- [ ] prod compose 包含 §3.1 资源 limits
- [ ] 慢查询日志已启用
- [ ] MS7 试点报告包含 P-BIZ-01 实测数据
