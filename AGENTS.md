# AI Agent 必读入口

> **任何 AI Agent、新会话、切换模型前，必须先阅读本文件，并按下方「分层阅读」加载上下文，否则禁止编写代码或修改计划。**  
> 目标：默认必读约 **200 行量级**；完整通读 00–05 仅在改治理/范围/规范时按需进行。

## 推荐工作流（默认，CR-20260829-002）

**单总控对话 + Git 分支 + PR + CI** — 用户 2026-08-29 批准；进阶档 PR 流程 2026-08-29 接入。

| 层级 | 做什么 |
|------|--------|
| **单总控** | 用户只维护一个主对话（派活、实现、验收、集成） |
| **任务 Spec** | 开工前贴 Spec（[`docs/06_TASK_SPEC.md`](docs/06_TASK_SPEC.md)），用户回复「开始」后再写代码 |
| **Git 分支** | 每个任务 `feat/{任务ID}-{简述}`，合并前 `test.ps1` 全绿 |
| **Pull Request** | push 后开 PR → 看 diff → CI 绿 → merge `main`（不直接合 main） |
| **CI** | push / PR 到 `main` 时 GitHub Actions 自动跑与本地相同的检查 |

多 Cursor 窗口、SESSIONS 登记簿为**可选**，默认不用。口令/合并清单以**本文件**为准；Lane 目录表以 [`CONTRIBUTING.md`](CONTRIBUTING.md) 为准；Spec/TDD/开源以 [`docs/06_TASK_SPEC.md`](docs/06_TASK_SPEC.md) 为准；任务状态以 [`docs/02_PROGRESS.md`](docs/02_PROGRESS.md) 为准。

### Git 分支命名

```
feat/s3-01-orchestrator
feat/s5-web-knowledge
fix/health-ready-timeout
```

### 日常口令（总控对话）

| 口令 | 行为 |
|------|------|
| **推进 W3** / **做 S3-01** | 先输出任务 Spec（`06_TASK_SPEC.md`），用户「开始」后在对应分支开发 |
| **探索 S3-05** | 大任务（估时 > 2h）：先方案对比，用户确认后再出 Spec（见 `06_TASK_SPEC.md` §设计探索） |
| **开始** | 按已确认 Spec 写代码 |
| **验收 MS2** | 对照模块文档实测 + `test.ps1` |
| **合并检查** | 跑 `test.ps1`，汇报是否可开 PR |
| **开 PR** | push 分支并用 `gh pr create`（或网页），填 PR 模板 |
| **合 PR** | CI 绿 + 看过 diff → merge → 更新 `02_PROGRESS.md` |
| **批准 MSx** | 实测通过后更新里程碑 `completed` |

### 合并前检查清单

1. `cd aeo-platform; .\scripts\test.ps1` 全绿  
2. 仅改任务相关目录（对照 Spec「不做什么」）  
3. `git diff main --stat` 无计划外文件  
4. 开 PR，等 CI 绿，用户确认 diff 后 merge  
5. 总控更新 `02_PROGRESS.md` 任务/里程碑状态  
6. **证据优先**（禁止只说「应该好了」）：完成声明须附带 `test.ps1` 完整输出（`x/x passed`），或关键 curl 响应 / 日志片段 / 截图  

### 工程纪律（吸纳 Superpowers 精华，不装插件）

| 原则 | 落地位置 |
|------|----------|
| **证据优先于声明** | 上表第 6 条；合并检查、验收报告必须贴真实输出 |
| **TDD 优先** | `06_TASK_SPEC.md` §TDD 纪律 — 功能开发先 RED 再 GREEN |
| **系统化调试** | `06_TASK_SPEC.md` §修 Bug 版 — 四阶段根因分析 |
| **两阶段审查** | `SESSIONS.md` §工人 PR 前审查 — 规格符合性 → 代码质量 |
| **并行隔离** | `SESSIONS.md` §git worktree — 多工人同时开发 |
| **开源优先（分级）** | `.cursor/rules/oss-first-implementation.mdc` + `06_TASK_SPEC.md` §开源优先 — L1/L2 按任务规模调研 |

### Commit 格式（进阶档）

```
feat(orchestrator): S3-05 compliance_agent + retry loop
fix(api): health ready timeout on slow redis
docs: add task spec template
```

`类型(范围): 任务ID 简述` — 类型：`feat` `fix` `test` `docs` `chore`

---

## 分层阅读（P1 — 替代「每次完整通读 00–05」）

### 每次会话（必读）

1. **本文件** `AGENTS.md`（工作流、口令、合并清单）
2. [`docs/02_PROGRESS.md`](docs/02_PROGRESS.md) **仅顶部状态**（当前阶段 / 下一任务 / `in_progress`）；仅执行其中 `in_progress` 或用户点名任务
3. **当前任务上下文**（按任务选一）：对应 Spec（[`docs/specs/`](docs/specs/) 或对话中的 Spec）、[`docs/modules/M*.md`](docs/modules/)、或扩展计划相关节（如 [`docs/11_PHASE6_BILLING_DATA_PLAN.md`](docs/11_PHASE6_BILLING_DATA_PLAN.md)）

确认 `plan_status`：读 `02` 顶部「总计划状态」即可；若标注非 `APPROVED`，再打开 [`docs/01_MASTER_PLAN.md`](docs/01_MASTER_PLAN.md) 核对。

### 按需加载（改到才读）

| 你在改… | 再读 |
|---------|------|
| 治理 / CR / 变更控制 | [`docs/00_GOVERNANCE.md`](docs/00_GOVERNANCE.md) |
| 范围 / 技术栈 / 里程碑 | [`docs/01_MASTER_PLAN.md`](docs/01_MASTER_PLAN.md) |
| 环境 / 版本 / 脚本 / 端口 | [`docs/03_DEV_ENVIRONMENT.md`](docs/03_DEV_ENVIRONMENT.md) |
| 分层 / API 契约 / 包职责 | [`docs/04_ARCHITECTURE_STANDARDS.md`](docs/04_ARCHITECTURE_STANDARDS.md) |
| SLA / 超时 / 并发 / 压测 | [`docs/05_PERFORMANCE_STANDARDS.md`](docs/05_PERFORMANCE_STANDARDS.md) |
| 开工契约 / TDD / 开源调研 | [`docs/06_TASK_SPEC.md`](docs/06_TASK_SPEC.md) |
| 生产部署 | [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) |
| 运维巡检 / 应急 | [`docs/RUNBOOK.md`](docs/RUNBOOK.md) |
| 多窗口工人 | [`docs/SESSIONS.md`](docs/SESSIONS.md) |
| 架构决策 | [`docs/adr/README.md`](docs/adr/README.md) |

**新 Agent / 换模型：** 视为零上下文，重新执行「每次会话」三步；不要假设记得上次对话。

## 工作状态检查

| 检查项 | 要求 |
|--------|------|
| 总计划状态 | `APPROVED` |
| 任务来源 | `02_PROGRESS.md` 中 `in_progress` 或用户点名 |
| 分支 | 功能开发在 `feat/*` 分支（Git 已初始化后） |
| 验收 | 本地 `test.ps1` + PR 上 CI 绿 |
| 完成后 | merge PR → 总控更新 `02_PROGRESS.md` |

## 可选：多窗口工人模式

仅赶工期时使用。见 `02_PROGRESS.md` §任务认领登记簿 与 [`docs/SESSIONS.md`](docs/SESSIONS.md)（含 **两阶段审查** 与 **git worktree** 并行规范）。

## 项目代号

**AEO Platform**（Autonomous Ecommerce Operator）

## 项目负责人

用户（项目维护者）
