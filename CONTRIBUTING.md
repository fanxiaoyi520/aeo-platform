# 贡献指南（Contributing）

感谢参与 **AEO Platform**（Autonomous Ecommerce Operator）开发。本文说明多人协作的最低要求。

## 开始前必读

1. [AGENTS.md](AGENTS.md) — 工作流、口令、合并清单（**单一真相源**）
2. [docs/02_PROGRESS.md](docs/02_PROGRESS.md) — 当前任务与里程碑
3. [docs/06_TASK_SPEC.md](docs/06_TASK_SPEC.md) — Spec / TDD / 开源优先模板

## 工作流与 PR

默认流程、分支命名、Commit 格式、合并前检查与证据要求 → **只维护在** [AGENTS.md](AGENTS.md)。  
PR 请使用 [.github/pull_request_template.md](.github/pull_request_template.md)。

## Lane 目录锁定（并行开发）— 本文件为权威

多人同时开发时，**每人只改自己 Lane 的目录**，避免合并冲突。

| Lane | 目录 | 典型任务 |
|------|------|----------|
| **A** | `aeo-platform/infra/`、`scripts/dev-up*`、`scripts/install-docker*` | 基础设施、Docker |
| **B** | `aeo-platform/apps/orchestrator/`、`aeo-platform/apps/api/` | Agent、API |
| **C** | `aeo-platform/apps/browser/` | Playwright 浏览器 |
| **D** | `aeo-platform/apps/web/` | Next.js 前端 |
| **E** | `aeo-platform/packages/rag/`、`packages/llm/` | RAG、LLM 适配器 |

**仅维护者可改（需单独 PR 或总控协调）：**

- `aeo-platform/packages/shared/` — 错误码、共享类型
- `aeo-platform/apps/api/alembic/` — 数据库迁移
- `docs/01_MASTER_PLAN.md`、`docs/04_ARCHITECTURE_STANDARDS.md` — 架构变更须走 CR

认领状态见 [docs/02_PROGRESS.md §任务认领登记簿](docs/02_PROGRESS.md)；占用状态见同文件 §Lane。

## 开发环境

```powershell
cd aeo-platform
.\scripts\setup.ps1      # 首次：uv + pnpm + 依赖
.\scripts\dev-start.ps1  # 启动 Postgres/Redis + API/Web
.\scripts\test.ps1       # 合并前必跑
.\scripts\dev-stop.ps1   # 停止
```

版本锁定见 [docs/03_DEV_ENVIRONMENT.md](docs/03_DEV_ENVIRONMENT.md)。

**Docker 数据目录（Windows）：** 默认 `%LOCALAPPDATA%\aeo-platform\docker`，可通过 `AEO_DOCKER_ROOT` 覆盖。

## 并行隔离（可选）

赶工期时可用 **git worktree**；多窗口角色与登记 → [docs/SESSIONS.md](docs/SESSIONS.md)（默认单总控，不必用）。

## 问题与讨论

- Bug / 功能请求：GitHub Issue（可用 [任务模板](.github/ISSUE_TEMPLATE/task.yml)）
- 架构变更：先写 [ADR](docs/adr/README.md)（`docs/adr/`），经维护者批准后再实现

## License

贡献代码即表示同意以 [MIT License](LICENSE) 发布。
