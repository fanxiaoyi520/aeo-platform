# 任务 Spec — MV4-07

**任务：** 六 Agent 指挥台（前端简版）

**级别：** L2（新前端模块 + API）

## 开源调研（L2）

| 项目 | Stars | License | 可借鉴点 | 为何不直接采用 |
|------|-------|---------|----------|----------------|
| builderz-labs/mission-control | ~高 | MIT | Agent 面板、任务收件箱、实时状态 | 独立 Next+SQLite 平台，与 AEO monorepo 架构不符 |
| deepaksinghcs14/agent-nexus | 中 | Apache-2.0 | React Flow 画布、Admin 总览 | Go 后端 + 全栈平台，过重 |
| marmelab/shadcn-admin-kit | ~1k+ | MIT | shadcn CRUD 布局 | Ra-Core 依赖，仅需只读目录视图 |
| **自研（MS5 模式扩展）** | — | — | 复用 AppShell、card、BFF | 贴合 MV1-01 注册表，零新依赖 |

**采纳决策：** 自研页面 + 薄 API（`get_default_registry()` + `get_graph_catalog()`），UI 沿用现有 Tailwind/card 模式。

**做什么：**
- `GET /api/v1/agents` — 返回 Agent 目录 + 子图摘要
- BFF `app/api/agents/route.ts`
- 页面 `/agents` — 六类 Agent 卡片、状态/风控层级、Listing 子图流水线
- 侧栏导航增加「指挥台」
- 验收测试 `test_mv4_command_console.py`

**不做什么：**
- 不改 MV1-08 风控配置页
- 不实现 React Flow 拖拽编排（MV 后续）
- 不启动/调度父任务（仅展示 + 链到 `/tasks`）

**验收：**
1. `/agents` 展示 ≥10 个注册 Agent（6 active listing + 5 planned）
2. Listing 子图显示 6 步流水线
3. `test.ps1` 全绿

**分支：** `feat/mv4-07-command-console`
