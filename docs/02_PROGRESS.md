# 进度表（Progress Tracker）

> **唯一任务执行来源。** AI Agent 仅可执行本表中 `in_progress` 或用户明确指名的任务。  
> **总计划状态：** `APPROVED` — 2026-08-29 批准开工  
> **执行模式：** **单总控 + Git 分支 + CI**（CR-20260829-002，用户 2026-08-29 批准）  
> 多窗口工人模式见 §任务认领登记簿（**可选**，默认不用）。

**最后更新：** 2026-08-29  
**当前阶段：** W3 — MS2 待批准；MS3 S3-04 为下一任务  
**Git：** `main` @ `a162802`；当前分支 `feat/s3-03-rules-agent`；远程 [fanxiaoyi520/launch-aeo](https://github.com/fanxiaoyi520/launch-aeo)  
**CI：** `.github/workflows/ci.yml`（push 后 GitHub Actions 自动跑）

---

## 推荐工作流（默认）

```
用户 ──► 单总控对话（本对话）
           │
           ├─► git checkout -b feat/s3-02-research-agent
           ├─► 开发 + 本地 test.ps1
           ├─► git merge → main（总控）
           └─► push → CI 绿 = 可标任务 completed
```

| 步骤 | 命令 / 动作 |
|------|-------------|
| 初始化（一次性） | `git init` ✅ 已完成 |
| 首次提交 | `git add . && git commit` ✅ `b3e5a78` on `main` |
| 开功能分支 | `git checkout -b feat/s3-03-rules-agent` ✅ 进行中 |
| 本地验收 | `cd launch-aeo; .\scripts\test.ps1` |
| 云端 CI | `git push` → GitHub Actions |

---

## 总览

| 里程碑 | 状态 | 计划周 | 实际完成日 |
|--------|------|--------|------------|
| MS0 计划批准 | `completed` | W0 | 2026-08-29 |
| MS1 工程底座 | `completed` | W1–W2 | 2026-08-29 |
| MS2 RAG 可用 | `in_progress` | W3 | — |
| MS3 Agent 核心 | `in_progress` | W4–W6 | — |
| MS4 浏览器调研 | `blocked` | W7 | — |
| MS5 运营工作台 | `in_progress` | W8–W9 | — |
| MS6 生产加固 | `blocked` | W10 | — |
| MS7 试点验收 | `blocked` | W11–W12 | — |

---

## 模块进度

| 模块 | 名称 | 状态 | 完成度 | 泳道 |
|------|------|------|--------|------|
| M01 | 基础设施与工程化 | `completed` | 100% | — |
| M02 | RAG 知识库 | `in_progress` | 100% | S2-05 完成，待批准 MS2 |
| M03 | Agent 编排引擎 | `in_progress` | 45% | S3-01/02/03 ✅；下一 S3-04 |
| M05 | 运营工作台 | `in_progress` | 40% | S5-01/06 ✅；待 S5-02 |
| M04 | 浏览器自动化 | `blocked` | 0% | MS3 后 |
| M07 | 可观测与商业指标 | `blocked` | 0% | — |

---

## 多泳道并行（Lane）

| 泳道 | 当前任务 | 包/目录所有权 | 状态 |
|------|----------|---------------|------|
| **Lane A** | S2-05 已完成，待批准 MS2 | `infra/`、`scripts/dev-up*` | `done` |
| **Lane B** | S3-03 rules_agent 已完成 | `apps/orchestrator/`、`packages/shared`（只读优先） | `done` |
| **Lane D** | S5-01 + S5-06 已完成 | `apps/web/` | `done` |
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
| S5-01 | D | 2 | 是 | S5-06 | `M05-frontend-workbench.md` | `apps/web/` | `done` | 工人-D | 2026-08-29 11:08 | Next.js 14 + AppShell 布局 + 导航 |
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
| S3-04 | generate_agent | M03 | B | `in_progress` | S3-03 |
| S3-05 | compliance_agent + 重试回路 | M03 | B | `pending` | S3-04 |
| S3-06 | HITL 中断/恢复 + PostgreSQL checkpoint | M03 | B | `pending` | S3-05 |
| S3-07 | review_agent + 任务 API | M03 | B | `pending` | S3-06 |
| S3-08 | MS3 验收（CLI + API 演示） | M03 | B | `pending` | S3-01~07 |

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
| S5-02 | 任务创建与列表页 | M05 | D | `pending` | S5-01 + MS3 任务 API |
| S5-03 | Agent Trace 实时展示（SSE） | M05 | D | `pending` | S5-02 |
| S5-04 | HITL 审核页 | M05 | D | `pending` | S5-03 |
| S5-05 | Listing 结果导出 | M05 | D | `pending` | S5-04 |
| S5-06 | 知识库管理页 | M05 | D | `completed` | MS2 检索 API（S2-03） |
| S5-07 | MS5 验收 | M05 | D | `pending` | S5-01~06 |

### Sprint 8 — 生产加固（MS6）

| ID | 任务 | 模块 | 状态 | 依赖 |
|----|------|------|------|------|
| S6-01 | prod Docker Compose profile | M06 | `pending` | MS5 |
| S6-02 | 认证与 API 限流 | M06 | `pending` | S6-01 |
| S6-03 | 日志脱敏与审计日志 | M06/M07 | `pending` | S6-01 |
| S6-04 | 核心模块测试补齐（≥70%） | ALL | `pending` | MS5 |
| S6-05 | 部署文档 + 演示脚本 | M06 | `pending` | S6-01~04 |
| S6-06 | MS6 验收 | ALL | `pending` | S6-01~05 |

### Sprint 9–10 — 试点验收（MS7）

| ID | 任务 | 模块 | 状态 | 依赖 |
|----|------|------|------|------|
| S7-01 | 准备 20 个元征 SKU 测试集 | — | `pending` | MS6 |
| S7-02 | 批量运行并记录指标 | M07 | `pending` | S7-01 |
| S7-03 | 试点报告 + 10 分钟演示视频 | — | `pending` | S7-02 |
| S7-04 | MS7 验收 | ALL | `pending` | S7-01~03 |

---

## 用户口令速查（总控对话）

| 说 | 效果 |
|----|------|
| **推进 W3** / **做 S3-02** | 总控在 `feat/s3-02-*` 分支开发 |
| **验收 MS2** | 实测 + test.ps1 报告 |
| **合并检查** | 跑 test.ps1，是否可合 main |
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
