# 文档导航（docs/）

按角色找入口。权威优先级见 [`00_GOVERNANCE.md`](00_GOVERNANCE.md)。分层阅读见根目录 [`AGENTS.md`](../AGENTS.md)。

## 我是谁 → 先读什么

| 角色 | 先读 | 再读 |
|------|------|------|
| **新人 / 第一次跑起来** | [how-to/getting-started.md](how-to/getting-started.md) | [`aeo-platform/README`](../aeo-platform/README.md)、[`03_DEV_ENVIRONMENT.md`](03_DEV_ENVIRONMENT.md) |
| **总控 / 日常开发** | [`AGENTS.md`](../AGENTS.md) → [`02_PROGRESS.md`](02_PROGRESS.md) 顶部 | 当前任务 Spec / 模块 / [`06_TASK_SPEC.md`](06_TASK_SPEC.md) |
| **改架构 / API / 分层** | [`04_ARCHITECTURE_STANDARDS.md`](04_ARCHITECTURE_STANDARDS.md) | [`adr/README.md`](adr/README.md) |
| **改环境 / 版本 / CI** | [`03_DEV_ENVIRONMENT.md`](03_DEV_ENVIRONMENT.md) | |
| **性能 / 超时 / 并发** | [`05_PERFORMANCE_STANDARDS.md`](05_PERFORMANCE_STANDARDS.md) | |
| **运维 / 上线** | [`DEPLOYMENT.md`](DEPLOYMENT.md)、[`RUNBOOK.md`](RUNBOOK.md) | |
| **多人并行工人** | [`SESSIONS.md`](SESSIONS.md)（可选）、[`CONTRIBUTING.md`](../CONTRIBUTING.md) §Lane | [`02_PROGRESS.md`](02_PROGRESS.md) 认领表 |
| **看范围 / 里程碑** | [`01_MASTER_PLAN.md`](01_MASTER_PLAN.md) | 扩展：[`10_MANAGER_VISION_PLAN.md`](10_MANAGER_VISION_PLAN.md)、[`11_PHASE6_BILLING_DATA_PLAN.md`](11_PHASE6_BILLING_DATA_PLAN.md) |

## 目录地图

| 路径 | 用途 |
|------|------|
| `00`–`06` | 治理、总计划、进度、环境/架构/性能、Spec 模板 |
| `modules/` | Phase 1 模块计划（M01–M07） |
| `11_PHASE6_*.md` | 当前扩展：计费与真实店铺数据（含模块映射） |
| `adr/` | 架构决策记录 |
| `specs/` | L2 开源调研 Spec 存档 |
| `how-to/` | 任务型操作指南 |
| `reports/` | 验收证据 |
| `pilot/`、`templates/` | 试点与报告模板 |
| `DEPLOYMENT.md` / `RUNBOOK.md` | 部署与运维 |
| `internal/` | 内部归档（不公开分发） |

## 单一真相源（勿重复维护）

| 内容 | 文件 |
|------|------|
| 口令 / 合并清单 | [`AGENTS.md`](../AGENTS.md) |
| Lane 目录表 | [`CONTRIBUTING.md`](../CONTRIBUTING.md) |
| Spec / TDD / 开源 | [`06_TASK_SPEC.md`](06_TASK_SPEC.md) |
| 任务状态 | [`02_PROGRESS.md`](02_PROGRESS.md) |
