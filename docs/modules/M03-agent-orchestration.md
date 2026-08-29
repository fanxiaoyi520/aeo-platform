# M03 — Agent 编排引擎

| 属性 | 值 |
|------|-----|
| **模块 ID** | M03 |
| **优先级** | P0 |
| **里程碑** | MS3（W4–W6） |
| **状态** | `blocked` |
| **依赖** | M01, M02 |

---

## 1. 目标

基于 LangGraph 实现生产级多 Agent 编排，支持状态持久化、重试、熔断、HITL 人工审核。

## 2. Agent 定义

### 2.1 research_agent

| 项 | 说明 |
|----|------|
| 输入 | 产品 SKU、目标平台、目标市场（如 US） |
| 输出 | 竞品 ASIN 列表、竞品标题/卖点摘要、关键词建议 |
| 工具 | `browser.search_competitors`（M04）、`web.search`（降级） |
| 超时 | 120s |
| 失败策略 | 降级为仅用户手动输入竞品信息 |

### 2.2 rules_agent

| 项 | 说明 |
|----|------|
| 输入 | 平台、品类、research 输出 |
| 输出 | 适用规则摘要、产品资料片段、范例参考 |
| 工具 | `rag.search` |
| 超时 | 30s |

### 2.3 generate_agent

| 项 | 说明 |
|----|------|
| 输入 | rules 输出 + research 输出 + 用户原始输入 |
| 输出 | `title`, `bullets[5]`, `search_terms`, `description`（可选） |
| 工具 | `llm.chat` |
| 超时 | 60s |
| 平台模板 | Amazon / TikTok 分别定义 Prompt 模板 |

### 2.4 compliance_agent

| 项 | 说明 |
|----|------|
| 输入 | generate 输出 |
| 输出 | `passed: bool`, `issues: []`, `fixed_output`（尝试自动修复） |
| 规则 | 标题字数、禁用词表、Bullet 条数、HTML 标签 |
| 重试 | 不通过 → 回流 generate_agent，最多 3 次 |

### 2.5 review_agent（HITL 后）

| 项 | 说明 |
|----|------|
| 输入 | 人工审核后的最终内容 |
| 输出 | 版本存档、任务状态 `completed`、指标快照 |
| 工具 | `db.save_listing_version` |

### 2.6 HITL 节点

- LangGraph `interrupt_before=["human_review"]`
- 前端调用 `POST /api/v1/tasks/{id}/approve` 或 `reject`
- reject 可带修改意见，回流 generate_agent

## 3. 状态模型

```python
class TaskState(TypedDict):
    task_id: str
    platform: Literal["amazon", "tiktok"]
    sku: str
    product_info: dict
    research: dict | None
    rules: dict | None
    generated: dict | None
    compliance: dict | None
    human_feedback: str | None
    final_output: dict | None
    retry_count: int
    degraded_mode: bool
    trace: list[AgentTraceEvent]
    status: TaskStatus
```

## 4. 交付物

- [ ] LangGraph 状态图定义（`apps/orchestrator/graph.py`）
- [ ] 5 个 Agent 节点实现
- [ ] PostgreSQL Checkpointer 集成
- [ ] 任务 API：创建、查询、SSE 事件流、HITL 操作
- [ ] CLI：`python -m apps.orchestrator.cli run --sku X431 ...`
- [ ] 单元测试：各 Agent mock 测试 + 图集成测试

## 5. 可靠性规范

| 机制 | 实现 |
|------|------|
| 重试 | tenacity，指数退避，最多 3 次 |
| 熔断 | 连续失败 5 次 → 暂停该工具 5 分钟 |
| 超时 | 每节点独立超时，超时记入 trace |
| 幂等 | task_id + checkpoint 防重复执行 |

## 6. 验收标准

1. CLI 端到端：输入 SKU → 输出合规 Listing（可 mock LLM）
2. HITL：中断 → API approve → 任务完成
3. compliance 失败自动重试 3 次后转人工
4. research 失败进入 degraded_mode 仍可完成生成
5. 全流程 trace 可查询

## 7. 不在本模块范围

- Playwright 具体实现（M04）
- 前端 UI（M05）
