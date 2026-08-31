# 贡献指南（Contributing）

感谢参与 **AEO Platform**（Autonomous Ecommerce Operator）开发。本文说明多人协作的最低要求。

## 开始前必读

1. [AGENTS.md](AGENTS.md) — AI / 开发者统一入口
2. [docs/02_PROGRESS.md](docs/02_PROGRESS.md) — 当前任务与里程碑
3. [docs/06_TASK_SPEC.md](docs/06_TASK_SPEC.md) — 开工前 Task Spec 模板

## 工作流（默认）

```
认领任务 → 输出 Spec → 用户「开始」→ feat 分支开发 → test.ps1 全绿 → PR → CI 绿 → merge
```

| 步骤 | 要求 |
|------|------|
| 分支 | `feat/{任务ID}-{简述}`，如 `feat/p1-02-sku-ingest` |
| Commit | `类型(范围): 任务ID 简述`，类型：`feat` `fix` `test` `docs` `chore` |
| 本地验收 | `cd aeo-platform; .\scripts\test.ps1` 全绿 |
| PR | 使用 [PR 模板](.github/pull_request_template.md)，附 `test.ps1` 输出或 CI 链接 |
| 合并 | CI 绿 + 维护者看过 diff → merge `main` |

## Lane 目录锁定（并行开发）

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

认领规则详见 [docs/02_PROGRESS.md §任务认领登记簿](docs/02_PROGRESS.md)。

## 开发环境

```powershell
cd aeo-platform
.\scripts\setup.ps1      # 首次：uv + pnpm + 依赖
.\scripts\dev-start.ps1  # 启动 Postgres/Redis + API/Web
.\scripts\test.ps1       # 合并前必跑
.\scripts\dev-stop.ps1   # 停止
```

版本锁定见 [docs/03_DEV_ENVIRONMENT.md](docs/03_DEV_ENVIRONMENT.md)。

## PR 检查清单

合并前确认：

- [ ] 仅修改任务 Spec 允许的目录（对照「不做什么」）
- [ ] `cd aeo-platform; .\scripts\test.ps1` 全绿
- [ ] 无计划外文件（`git diff main --stat`）
- [ ] 功能开发遵循 TDD：先 RED 再 GREEN（见 `06_TASK_SPEC.md`）
- [ ] 完成声明附证据（pytest 输出、curl 结果或截图），禁止只说「应该好了」

## 并行隔离（可选）

赶工期时可用 **git worktree** 为每个 Lane 建独立工作区，详见 [docs/SESSIONS.md](docs/SESSIONS.md)。

## 问题与讨论

- Bug / 功能请求：GitHub Issue（可用 [任务模板](.github/ISSUE_TEMPLATE/task.yml)）
- 架构变更：先写 ADR（`docs/adr/`），经维护者批准后再实现

## License

贡献代码即表示同意以 [MIT License](LICENSE) 发布。
