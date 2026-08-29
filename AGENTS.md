# AI Agent 必读入口

> **任何 AI Agent、新会话、切换模型前，必须先完整阅读本文件及下方链接文档，否则禁止编写代码或修改计划。**

## 推荐工作流（默认，CR-20260829-002）

**单总控对话 + Git 分支 + CI** — 用户 2026-08-29 批准。

| 层级 | 做什么 |
|------|--------|
| **单总控** | 用户只维护一个主对话（派活、实现、验收、集成） |
| **Git 分支** | 每个任务 `feat/{任务ID}-{简述}`，合并前 `test.ps1` 全绿 |
| **CI** | push 到 GitHub 后 Actions 自动跑与本地相同的检查 |

多 Cursor 窗口、SESSIONS 登记簿为**可选**，默认不用。

### Git 分支命名

```
feat/s3-01-orchestrator
feat/s5-web-knowledge
fix/health-ready-timeout
```

### 日常口令（总控对话）

| 口令 | 行为 |
|------|------|
| **推进 W3** / **做 S3-01** | 总控在对应分支开发或继续任务 |
| **验收 MS2** | 对照模块文档实测 + `test.ps1` |
| **合并检查** | 跑 `test.ps1`，汇报是否可合 main |
| **批准 MSx** | 实测通过后更新里程碑 `completed` |

### 合并前检查清单

1. `cd launch-aeo; .\scripts\test.ps1` 全绿  
2. 仅改任务相关目录  
3. 总控更新 `02_PROGRESS.md` 任务/里程碑状态  

---

## 强制阅读顺序

1. [`docs/00_GOVERNANCE.md`](docs/00_GOVERNANCE.md)
2. [`docs/01_MASTER_PLAN.md`](docs/01_MASTER_PLAN.md)
3. [`docs/03_DEV_ENVIRONMENT.md`](docs/03_DEV_ENVIRONMENT.md)
4. [`docs/04_ARCHITECTURE_STANDARDS.md`](docs/04_ARCHITECTURE_STANDARDS.md)
5. [`docs/05_PERFORMANCE_STANDARDS.md`](docs/05_PERFORMANCE_STANDARDS.md)
6. [`docs/02_PROGRESS.md`](docs/02_PROGRESS.md) — 任务与里程碑
7. 当前任务对应 `docs/modules/M*.md`

## 工作状态检查

| 检查项 | 要求 |
|--------|------|
| 总计划状态 | `APPROVED` |
| 任务来源 | `02_PROGRESS.md` 中 `in_progress` 或用户点名 |
| 分支 | 功能开发在 `feat/*` 分支（Git 已初始化后） |
| 验收 | 本地 `test.ps1` + 可选 GitHub Actions CI |
| 完成后 | 总控更新 `02_PROGRESS.md` |

## 可选：多窗口工人模式

仅赶工期时使用。见 `02_PROGRESS.md` §任务认领登记簿 与 [`docs/SESSIONS.md`](docs/SESSIONS.md)。

## 项目代号

**Launch AEO**（Autonomous Ecommerce Operator）

## 项目负责人

用户（元征科技 AI 部门技术开发，目标转岗 AI 电商 Agent 团队）
