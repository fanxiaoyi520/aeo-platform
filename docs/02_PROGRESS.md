# 进度表（Progress Tracker）

> **唯一任务执行来源。** AI Agent 仅可执行本表中 `in_progress` 或用户明确指名的任务。  
> **总计划状态：** `APPROVED` — 2026-08-29 批准开工  
> **执行模式：** **单总控 + Spec + Git 分支 + PR + CI**（进阶档，2026-08-29）  
> 多窗口工人模式见 §任务认领登记簿（**可选**，默认不用）。

**最后更新：** 2026-08-30  
**当前阶段：** W11 — S7-03 已完成；下一 **S7-04** MS7 验收  
**Git：** `main` @ `bb20a6a`  
**CI：** `.github/workflows/ci.yml`（push 后 GitHub Actions 自动跑）

---

## 推荐工作流（默认）

```
用户 ──► 单总控对话（本对话）
           │
           ├─► 输出任务 Spec（06_TASK_SPEC.md）→ 用户「开始」
           ├─► git checkout -b feat/s3-05-compliance-agent
           ├─► 开发 + commit + 本地 test.ps1
           ├─► push → 开 PR → CI 绿 → 看 diff
           ├─► merge PR → main
           └─► 更新 02_PROGRESS.md = 任务 completed
```

| 步骤 | 命令 / 动作 |
|------|-------------|
| 初始化（一次性） | `git init` ✅ 已完成 |
| 首次提交 | `git add . && git commit` ✅ `b3e5a78` on `main` |
| 任务 Spec | 见 [`06_TASK_SPEC.md`](06_TASK_SPEC.md)；用户「开始」后再编码 |
| 开功能分支 | `git checkout -b feat/s6-01-prod-compose`（下一任务） |
| 本地验收 | `cd launch-aeo; .\scripts\test.ps1` |
| 开 PR | `git push -u origin HEAD` → `gh pr create`（见 PR 模板） |
| 云端 CI | PR / push to `main` → GitHub Actions |
| 合并 | CI 绿 + 看 diff → merge PR → 更新进度表 |

---

## 总览

| 里程碑 | 状态 | 计划周 | 实际完成日 |
|--------|------|--------|------------|
| MS0 计划批准 | `completed` | W0 | 2026-08-29 |
| MS1 工程底座 | `completed` | W1–W2 | 2026-08-29 |
| MS2 RAG 可用 | `completed` | W3 | 2026-08-30 |
| MS3 Agent 核心 | `completed` | W4–W6 | 2026-08-30 |
| MS4 浏览器调研 | `pending` | W7 | — |
| MS5 运营工作台 | `completed` | W8–W9 | 2026-08-30 |
| MS6 生产加固 | `completed` | W10 | 2026-08-30 |
| MS7 试点验收 | `pending` | W11–W12 | — |

---

## 模块进度

| 模块 | 名称 | 状态 | 完成度 | 泳道 |
|------|------|------|--------|------|
| M01 | 基础设施与工程化 | `completed` | 100% | — |
| M02 | RAG 知识库 | `completed` | 100% | MS2 已批准（2026-08-30） |
| M03 | Agent 编排引擎 | `completed` | 100% | MS3 已批准（2026-08-30） |
| M05 | 运营工作台 | `completed` | 100% | MS5 已批准（2026-08-30） |
| M06 | 部署与安全 | `completed` | 100% | MS6 已批准（2026-08-30） |
| M04 | 浏览器自动化 | `pending` | 0% | MS3 已解除阻塞，待 S4-01 |
| M07 | 可观测与商业指标 | `in_progress` | 60% | S7-03 报告 + 演示脚本完成 |

---

## 多泳道并行（Lane）

| 泳道 | 当前任务 | 包/目录所有权 | 状态 |
|------|----------|---------------|------|
| **Lane A** | MS2 已批准 | `infra/`、`scripts/dev-up*` | `idle` |
| **Lane B** | MS3 已批准，Lane 空闲 | `apps/orchestrator/`、`apps/api/` | `idle` |
| **Lane D** | MS5 已批准，Lane 空闲 | `apps/web/` | `idle` |
| **Lane E** | Docker 已安装（WSL） | `scripts/install-docker*` | `done` |

### Agent 认领规则

1. **先登记、后编码**：开工前更新下方 **§任务认领登记簿**；未登记不得改代码。
2. **一次一 Lane**：每个工人会话只认领一个 Lane + 一组任务 ID。
3. **禁止抢单**：`claimed` 且非本人 → 停止并通知总控；总控负责改派（改登记簿）。
4. **文件所有权**：禁止跨 Lane 修改对方目录；`packages/shared`、DB migration **仅总控**可改。
5. **集成检查**：合并前必须 `.\scripts\test.ps1` 全绿。
6. **会话结束**：认领改为 `done` 或 `released`；里程碑 `completed` **仅总控**可写。

---

## 任务认领登记簿（Claim Registry）

> **权威来源。** 用户在新会话说 **「领取空闲任务」** 即可，无需粘贴提示词。  
> Agent 读本表 → 按 `优先级` 自动认领 → 读 `模块文档` → 在 `目录锁定` 内编码。

| 任务 ID | Lane | 优先级 | 可工人认领 | 绑定任务 | 模块文档 | 目录锁定 | 认领状态 | 认领人 | 认领时间 (UTC+8) | 交付摘要 |
|---------|------|--------|------------|----------|----------|----------|----------|--------|------------------|----------|
| S3-01 | B | 1 | 是 | — | `M03-agent-orchestration.md` | `apps/orchestrator/` | `done` | 工人-B | 2026-08-29 11:07 | TaskState + 5 节点 stub + LangGraph 图（HITL interrupt） |
| S3-02 | B | 1 | 否 | — | `M03-agent-orchestration.md` | `apps/orchestrator/` | `done` | 总控 | 2026-08-29 11:20 | research_agent 无浏览器版：用户竞品输入 + LLM 关键词降级 |
| S3-03 | B | 1 | 否 | — | `M03-agent-orchestration.md` | `apps/orchestrator/` | `done` | 总控 | 2026-08-29 11:32 | rules_agent：RAG 检索平台规则/产品资料/范例 |
| S3-04 | B | 1 | 否 | — | `M03-agent-orchestration.md` | `apps/orchestrator/` | `done` | 总控 | 2026-08-29 11:38 | generate_agent：Amazon/TikTok LLM 模板 + JSON 输出 |
| S3-05 | B | 1 | 否 | — | `M03-agent-orchestration.md` | `apps/orchestrator/` | `done` | 总控 | 2026-08-29 11:46 | compliance_agent：规则校验 + 自动修复 + generate 重试回路 |
| S3-06 | B | 1 | 否 | — | `M03-agent-orchestration.md` | `apps/orchestrator/` | `done` | 总控 | 2026-08-30 08:50 | HITL approve/reject + Postgres checkpoint 工厂 |
| S3-07 | B | 1 | 否 | — | `M03-agent-orchestration.md` | `apps/orchestrator/`、`apps/api/` | `done` | 总控 | 2026-08-30 09:00 | review_agent 持久化 ListingVersion + 任务 CRUD/HITL API |
| S3-08 | B | 1 | 否 | — | `M03-agent-orchestration.md` | `apps/orchestrator/` | `done` | 总控 | 2026-08-30 09:05 | CLI `aeo-orchestrate run` + MS3 验收测试 6 项 |
| S5-01 | D | 2 | 是 | S5-06 | `M05-frontend-workbench.md` | `apps/web/` | `done` | 工人-D | 2026-08-29 11:08 | Next.js 14 + AppShell 布局 + 导航 |
| S5-02 | D | 2 | 是 | — | `M05-frontend-workbench.md` | `apps/web/` | `done` | 总控 | 2026-08-30 09:10 | `/tasks` 列表 + `/tasks/new` 创建 + BFF 代理 |
| S5-03 | D | 2 | 是 | — | `M05-frontend-workbench.md` | `apps/web/`、`apps/api/` | `done` | 总控 | 2026-08-30 09:20 | SSE Trace 时间线 + `/tasks/{id}/events` |
| S5-04 | D | 2 | 是 | — | `M05-frontend-workbench.md` | `apps/web/`、`apps/api/` | `done` | 总控 | 2026-08-30 09:30 | `/tasks/{id}/review` HITL 审核 + approve/reject BFF |
| S5-05 | D | 2 | 是 | — | `M05-frontend-workbench.md` | `apps/web/` | `done` | 总控 | 2026-08-30 09:42 | `/tasks/{id}/result` 复制 + JSON/CSV 导出 |
| S5-07 | D | 2 | 否 | — | `M05-frontend-workbench.md` | `apps/web/`、`apps/api/` | `done` | 总控 | 2026-08-30 09:52 | MS5 验收测试 + 报告 |
| S5-06 | D | 2 | 是 | S5-01 | `M05-frontend-workbench.md` | `apps/web/` | `done` | 工人-D | 2026-08-29 11:08 | `/knowledge` 页 + API 代理对接 knowledge |
| S2-05 | A/E | 9 | 否 | — | `M01-infrastructure.md` | `infra/`、`scripts/dev-up*` | `done` | 总控 | 2026-08-29 11:02 | Docker 三容器 healthy；`/ready` database+redis true；test.ps1 13/13 |

**认领状态：** `unclaimed` → `claimed` → `done` | `released`  
**认领人格式：** `工人-B` | `工人-D` | `总控` | `用户`

### 自动认领规则（工人）

1. 筛 `unclaimed` + `可工人认领=是` → 按 `优先级` 最小优先  
2. 有 `绑定任务` 时同会话一并认领，认领人同为 `工人-{Lane}`  
3. 全占用 → 回复「无空闲任务」+ 认领人列表，不写代码  
4. 改派：仅总控可将他人 `claimed` 改为 `released`

### W3 并行时间线（方案 2）

| 周 | Lane A | Lane B | Lane D | 集成 |
|----|--------|--------|--------|------|
| W3 | MS2 验收 | S3-01 状态模型 | S5-01 + S5-06 | 周五 test.ps1 |
| W4–W5 | — | S3-02~05 | S5-06 完善 | 每周集成 |
| W6 | — | MS3 验收 | S5-02 待 MS3 | **集成周** |
| W7+ | — | — | S5-03~07 | MS4 启动 |

---

## Sprint 计划

### Sprint 0 — 计划审核 ✅

| ID | 任务 | 负责人 | 状态 | 备注 |
|----|------|--------|------|------|
| S0-01 | 用户审核总计划 v1.1.0 | 用户 | `completed` | 已审核 |
| S0-02 | 根据反馈修订计划（如有） | AI | `completed` | v1.1.0 |
| S0-03 | 用户批准开工 | 用户 | `completed` | 2026-08-29 |

### Sprint 1 — 工程底座（MS1）✅

| ID | 任务 | 模块 | 状态 | 依赖 |
|----|------|------|------|------|
| S1-01 | Monorepo 脚手架初始化（uv workspace + pnpm） | M01 | `completed` | MS0 |
| S1-02 | Docker Compose dev 环境（端口/网络按 `03` §7） | M01/M06 | `completed` | S1-01 |
| S1-03 | PostgreSQL 模型与迁移（Alembic + `04` §6 索引） | M01 | `completed` | S1-02 |
| S1-04 | FastAPI 骨架 + 统一响应/错误码（`04` §5） | M01 | `completed` | S1-02 |
| S1-05 | LLMProvider 抽象 + 超时配置（`05` §8） | M01 | `completed` | S1-04 |
| S1-06 | 统一脚本 setup/dev-up/test（`03` §6） | M01 | `completed` | S1-01 |
| S1-07 | CI：lint + test + docker build（`03` §8） | M01 | `completed` | S1-01 |
| S1-08 | prod compose 资源 limits + Prometheus 骨架 | M01/M06 | `completed` | S1-02 |
| S1-09 | MS1 验收（含 `03/04/05` 规范检查清单） | M01 | `completed` | S1-01~08 |

### Sprint 2 — RAG（MS2，Lane A）

| ID | 任务 | 模块 | Lane | 状态 | 依赖 |
|----|------|------|------|------|------|
| S2-01 | 知识库目录结构与样例文档 | M02 | A | `completed` | MS1 |
| S2-02 | 文档解析 + 分块 + 向量化 pipeline | M02 | A | `completed` | S2-01 |
| S2-03 | Chroma 持久化与检索 API | M02 | A | `completed` | S2-02 |
| S2-04 | 知识库管理 API（增删查） | M02 | A | `completed` | S2-03 |
| S2-05 | MS2 验收 | M02 | A/E | `completed` | S2-01~04；Docker `/ready` 已验 |

### Sprint 3–4 — Agent 核心（MS3，Lane B）

| ID | 任务 | 模块 | Lane | 状态 | 依赖 |
|----|------|------|------|------|------|
| S3-01 | LangGraph 状态模型定义 | M03 | B | `completed` | MS1 + S2-03 |
| S3-02 | research_agent 实现（无浏览器版） | M03 | B | `completed` | S3-01 |
| S3-03 | rules_agent（RAG 工具调用） | M03 | B | `completed` | S3-01 |
| S3-04 | generate_agent | M03 | B | `completed` | S3-03 |
| S3-05 | compliance_agent + 重试回路 | M03 | B | `completed` | S3-04 |
| S3-06 | HITL 中断/恢复 + PostgreSQL checkpoint | M03 | B | `completed` | S3-05 |
| S3-07 | review_agent + 任务 API | M03 | B | `completed` | S3-06 |
| S3-08 | MS3 验收（CLI + API 演示） | M03 | B | `completed` | S3-01~07 |

### Sprint 5 — 浏览器自动化（MS4）

| ID | 任务 | 模块 | Lane | 状态 | 依赖 |
|----|------|------|------|------|------|
| S4-01 | Playwright 服务封装 | M04 | — | `pending` | MS3 |
| S4-02 | Amazon 竞品 Listing 抓取 | M04 | — | `pending` | S4-01 |
| S4-03 | 接入 research_agent + 降级策略 | M04 | — | `pending` | S4-02 |
| S4-04 | MS4 验收 | M04 | — | `pending` | S4-01~03 |

### Sprint 6–7 — 运营工作台（MS5，Lane D）

| ID | 任务 | 模块 | Lane | 状态 | 依赖 |
|----|------|------|------|------|------|
| S5-01 | Next.js 项目初始化 + 布局 | M05 | D | `completed` | MS1（并行；布局/mock，不等 MS3） |
| S5-02 | 任务创建与列表页 | M05 | D | `completed` | S5-01 + MS3 任务 API |
| S5-03 | Agent Trace 实时展示（SSE） | M05 | D | `completed` | S5-02 |
| S5-04 | HITL 审核页 | M05 | D | `completed` | S5-03 |
| S5-05 | Listing 结果导出 | M05 | D | `completed` | S5-04 |
| S5-06 | 知识库管理页 | M05 | D | `completed` | MS2 检索 API（S2-03） |
| S5-07 | MS5 验收 | M05 | D | `completed` | S5-01~06 |

### Sprint 8 — 生产加固（MS6）

| ID | 任务 | 模块 | 状态 | 依赖 |
|----|------|------|------|------|
| S6-01 | prod Docker Compose profile | M06 | `completed` | MS5 |
| S6-02 | 认证与 API 限流 | M06 | `completed` | S6-01 |
| S6-03 | 日志脱敏与审计日志 | M06/M07 | `completed` | S6-01 |
| S6-04 | 核心模块测试补齐（≥70%） | ALL | `completed` | MS5 |
| S6-05 | 部署文档 + 演示脚本 | M06 | `completed` | S6-01~04 |
| S6-06 | MS6 验收 | ALL | `completed` | S6-01~05 |

### Sprint 9–10 — 试点验收（MS7）

| ID | 任务 | 模块 | 状态 | 依赖 |
|----|------|------|------|------|
| S7-01 | 准备 20 个元征 SKU 测试集 | — | `completed` | MS6 |
| S7-02 | 批量运行并记录指标 | M07 | `completed` | S7-01 |
| S7-03 | 试点报告 + 10 分钟演示视频 | — | `completed` | S7-02 |
| S7-04 | MS7 验收 | ALL | `pending` | S7-01~03 |

---

## 管理岗 Phase 2 — 生产商业级扩展（**已批准**，MV1 待 MS7）

> Phase 2 计划 **已 `APPROVED`**（2026-08-30）。MV1 编码仍 blocked，须 **MS7 通过 + SP-API 确认**。

| 文档 | 状态 |
|------|------|
| [`10_MANAGER_VISION_PLAN.md`](10_MANAGER_VISION_PLAN.md) | `APPROVED` — 生产商业级 Phase 2 |
| [`10_MANAGER_VISION_PROGRESS.md`](10_MANAGER_VISION_PROGRESS.md) | MV0 ✅；MV1–MV5 blocked |

**当前主执行：** Phase 1 `02_PROGRESS`（**MS7 进行中**）→ S7-01~04 → 再开 MV1。

---

## 用户口令速查（总控对话）

| 说 | 效果 |
|----|------|
| **做 S3-05** | 先输出 Spec（`06_TASK_SPEC.md`），不写代码 |
| **开始** | 在 `feat/s3-05-*` 按 Spec 开发 |
| **合并检查** | 跑 test.ps1，是否可开 PR |
| **开 PR** | push + 创建 PR，等 CI 绿 |
| **合 PR** | merge 后更新进度表 |
| **验收 MS2** | 实测 + test.ps1 报告 |
| **批准 MS2** | 关闭 MS2 里程碑（须实测通过） |

可选多窗口：见 [`SESSIONS.md`](SESSIONS.md)。协议见 [`AGENTS.md`](../AGENTS.md)。

---

## 阻塞项（Blockers）

| ID | 描述 | 负责人 | 状态 |
|----|------|--------|------|
| B-001 | 总计划待用户批准 | 用户 | `closed` |
| B-002 | Docker 未安装，MS2 `/ready` 无法验收 | 用户 | `closed` |

---

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-08-29 | 初版进度表创建，所有开发任务 blocked |
| 2026-08-29 | MS2：mypy 修复、CI 纳入 rag/tests、20 题抽检 |
| 2026-08-29 | **CR-20260829-001 批准**：多泳道并行（方案 2）；S3-01、S5-01、S5-06 与 S2-05 并行 |
| 2026-08-29 | 新增 **1 总控 + ≤2 工人** 混合模式；**任务认领登记簿**（防重复认领） |
| 2026-08-29 | 总控完成 S2-05：Docker healthy、`/ready` 通过；B-002 关闭 |
| 2026-08-29 | **CR-20260829-002**：默认 **单总控 + Git 分支 + CI**；test/CI 纳入 orchestrator（17 项） |
| 2026-08-29 | S3-01 completed；S3-02 in_progress；Git 仓库 init |
| 2026-08-29 | S3-02 completed：research_agent 无浏览器版；test.ps1 **19/19** 全绿 |
| 2026-08-29 | 远程仓库上线：`fanxiaoyi520/launch-aeo`；`main` push 完成 |
| 2026-08-29 | S3-03 completed：rules_agent RAG 集成；test.ps1 **21/21** 全绿 |
| 2026-08-29 | S3-03 合并 push `main`；S3-04 completed：generate_agent；test.ps1 **23/23** 全绿 |
| 2026-08-29 | 新增 `06_TASK_SPEC.md`：任务 Spec 模板 + S3-05 示例；接入 AGENTS 工作流 |
| 2026-08-29 | **进阶档**：PR 模板、Issue 模板、commit 规范；工作流改为 Spec → PR → merge |
| 2026-08-29 | S3-05 completed：compliance_agent 校验/自动修复/重试回路；test.ps1 **29/29** 全绿 |
| 2026-08-30 | S3-06 completed：HITL approve/reject + Postgres checkpoint；test.ps1 **35/35** 全绿 |
| 2026-08-30 | S3-07 completed：review_agent + 任务 API；test.ps1 **41/41** 全绿 |
| 2026-08-30 | S3-08 completed：CLI + MS3 验收测试；test.ps1 **47/47** 全绿 |
| 2026-08-30 | **用户批准 MS3**：里程碑 `completed`；M04/MS4 解除阻塞 |
| 2026-08-30 | S5-02 completed：任务列表/创建页 + `/api/tasks` BFF；web typecheck/lint ✅ |
| 2026-08-30 | S5-03 completed：SSE `/api/v1/tasks/{id}/events` + Trace 时间线；test.ps1 **48/48** |
| 2026-08-30 | S5-04 merged：PR #1 HITL 审核页；`main` @ `14759df`；CI ✅ |
| 2026-08-30 | S5-05 merged：PR #2 Listing 导出页；`main` @ `bc780aa`；CI ✅ |
| 2026-08-30 | docs: sync progress @ `52fe3ab` |
| 2026-08-30 | **用户批准 MS2**：里程碑 `completed`；M02 关闭 |
| 2026-08-30 | S5-07 merged：PR #3 MS5 验收；`main` @ `e13e339`；test.ps1 **70/70** |
| 2026-08-30 | **用户批准 MS5**：里程碑 `completed`；MS6 解除阻塞 |
| 2026-08-30 | S6-01 merged：PR #4 prod compose + web Dockerfile + prod-up/down；test.ps1 **75/75**；CI ✅ |
| 2026-08-30 | S6-02 merged：PR #5 rate limit + CORS + prod key guard；test.ps1 **80/80**；CI ✅ |
| 2026-08-30 | S6-03 merged：PR #6 log redaction + audit API；test.ps1 **88/88**；CI ✅ |
| 2026-08-30 | S6-04 merged：PR #7 coverage gate 70% + core tests；test.ps1 **102/102**，覆盖率 **86%**；CI ✅ |
| 2026-08-30 | S6-05 merged：PR #8 DEPLOYMENT.md + backup/demo scripts；test.ps1 **106/106**；CI ✅ |
| 2026-08-30 | S6-06 merged：PR #9 MS6 验收报告 + acceptance tests；test.ps1 **126/126**；CI ✅ |
| 2026-08-30 | **用户批准 MS6**：里程碑 `completed`；MS7 解除阻塞；下一 **S7-01** |
| 2026-08-30 | S7-01：20 元征 SKU 测试集 JSON + 文档；test.ps1 **143/143** |
| 2026-08-30 | S7-01 merged：PR #10 pilot testset；test.ps1 **143/143**；CI ✅ |
| 2026-08-30 | S7-02：batch_pilot.py + pilot_metrics；test.ps1 **151/151** |
| 2026-08-30 | S7-02 merged：PR #11 batch pilot；test.ps1 **151/151**；CI ✅ |
| 2026-08-30 | S7-03：试点报告模板 + generate_pilot_report + 演示脚本 |
| 2026-08-30 | S7-03 merged：PR #12 pilot report + demo script；test.ps1 **160/160**；CI ✅ |
