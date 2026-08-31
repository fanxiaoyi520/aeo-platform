# 统一开发环境规范（Development Environment）

| 属性 | 值 |
|------|-----|
| **版本** | v1.0.0 |
| **状态** | `DRAFT` — 随总计划一并审核 |
| **约束力** | 全项目强制统一，禁止各模块自行选型 |

---

## 1. 原则

1. **版本锁定**：所有运行时、依赖主版本写入本文件与锁文件，禁止「latest」裸用
2. **环境一致**：开发 = Docker Compose dev；生产 = Docker Compose prod；禁止「仅我本机能跑」
3. **一键初始化**：`make setup` 或 `scripts/setup.ps1`（Windows）完成环境搭建
4. **跨平台**：主开发机 Windows 10+；生产部署目标 Linux（Docker）；脚本双端兼容

---

## 2. 运行时版本（锁定）

| 组件 | 版本 | 说明 |
|------|------|------|
| **Python** | `3.11.9` | 后端、Agent、Browser、脚本 |
| **Node.js** | `20.18.0` LTS | 前端、工具链 |
| **pnpm** | `9.12.0` | 前端包管理（禁止 npm/yarn 混用） |
| **uv** | `0.4.18` | Python 包管理与虚拟环境 |
| **Docker Engine** | `≥ 24.0` | 容器运行时 |
| **Docker Compose** | `≥ 2.24` | 编排 |
| **PostgreSQL** | `16.4` | 关系库镜像 tag 固定 |
| **Redis** | `7.4` | 缓存/队列镜像 tag 固定 |
| **Playwright** | `1.48.0` | 与 Python 包版本一致 |
| **Chromium** | Playwright 内置 | 禁止单独安装其他浏览器 |

> 版本变更须走 CR，更新本文件 + 锁文件 + CI 镜像。

---

## 3. 操作系统与硬件基线

### 3.1 开发机最低配置

| 项 | 要求 |
|----|------|
| OS | Windows 10 19044+ / macOS 13+ / Ubuntu 22.04+ |
| CPU | 4 核+ |
| 内存 | **16 GB**（Docker + Playwright + IDE 同时运行） |
| 磁盘 | 50 GB 可用（含 Docker 镜像、Chroma 数据、截图） |
| 网络 | 可访问 LLM API（内网网关或公网） |

### 3.2 生产/试点部署基线

| 项 | 要求 |
|----|------|
| OS | Linux x86_64（Docker Host） |
| CPU | 4 核 |
| 内存 | **8 GB** 最低，**16 GB** 推荐 |
| 磁盘 | 100 GB SSD（数据卷 `postgres` / `chroma` / `screenshots`） |

---

## 4. 工具链统一

### 4.1 Python 工具链

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| **uv** | 依赖安装、venv | `pyproject.toml`（workspace root） |
| **ruff** | lint + format | `pyproject.toml [tool.ruff]` |
| **mypy** | 类型检查（strict 模式） | `pyproject.toml [tool.mypy]` |
| **pytest** | 单元/集成测试 | `pytest.ini` |
| **pytest-asyncio** | 异步测试 | — |
| **alembic** | 数据库迁移 | `apps/api/alembic/` |

**Python 工作区结构（uv workspace）：**

```
pyproject.toml          # workspace root
apps/api/pyproject.toml
apps/orchestrator/pyproject.toml
apps/browser/pyproject.toml
packages/shared/pyproject.toml
packages/llm/pyproject.toml
```

### 4.2 前端工具链

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| **pnpm** | 包管理 | `pnpm-lock.yaml` |
| **Next.js** | `14.2.x` | `apps/web/package.json` |
| **TypeScript** | `5.6.x` strict | `apps/web/tsconfig.json` |
| **ESLint** | lint | `apps/web/.eslintrc.json` |
| **Prettier** | format | `.prettierrc`（root 统一） |
| **Tailwind CSS** | `3.4.x` | `apps/web/tailwind.config.ts` |

### 4.3 Git 与提交规范

| 项 | 规范 |
|----|------|
| 分支 | `main`（稳定）、`feat/*`、`fix/*` |
| Commit | Conventional Commits：`feat:` `fix:` `docs:` `chore:` |
| `.gitignore` | 统一 root 维护：`.env`、`data/`、`node_modules/`、`.venv/`、`__pycache__/` |
| 禁止入库 | `.env`、密钥、内部未公开数据、`data/chroma/`、`data/screenshots/` |

### 4.4 IDE 统一（推荐）

| 项 | 配置 |
|----|------|
| 编辑器 | Cursor / VS Code |
| 工作区配置 | `.vscode/settings.json`（root 提交到 Git） |
| Python 解释器 | `.venv`（uv 创建） |
| Format on Save | 开启（ruff + prettier） |
| 推荐扩展 | Python、Ruff、ESLint、Prettier、Docker、Even Better TOML |

---

## 5. 环境变量规范

### 5.1 文件约定

| 文件 | 用途 | 入库 |
|------|------|------|
| `.env.example` | 全部变量模板（无真实值） | ✅ |
| `.env` | 本地实际配置 | ❌ |
| `.env.dev` | Docker Compose dev 引用 | ❌ |
| `.env.prod` | Docker Compose prod 引用 | ❌ |

### 5.2 变量命名（全项目统一前缀）

| 前缀 | 示例 | 说明 |
|------|------|------|
| `APP_` | `APP_ENV=development` | 应用全局 |
| `DB_` | `DB_URL=postgresql://...` | 数据库 |
| `REDIS_` | `REDIS_URL=redis://...` | Redis |
| `LLM_` | `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` | 大模型 |
| `EMBED_` | `EMBED_MODEL`、`EMBED_BASE_URL` | 向量模型 |
| `BROWSER_` | `BROWSER_HEADLESS=true` | Playwright |
| `AUTH_` | `AUTH_API_KEY` | API 认证 |

**禁止**各模块自定义无前缀的 `API_KEY`、`SECRET` 等歧义变量。

### 5.3 环境枚举

| `APP_ENV` | 用途 |
|-----------|------|
| `development` | 本地开发，详细日志，热重载 |
| `staging` | 预发验证 |
| `production` | 生产，日志 JSON，无热重载 |

---

## 6. 本地启动流程（统一）

```powershell
# Windows — 首次
.\scripts\setup.ps1

# 日常一键启动（推荐：Docker 只跑 DB，API/Web 本机后台）
.\scripts\dev-start.ps1

# 停止
.\scripts\dev-stop.ps1

# 全容器启动（含 API 镜像构建，较慢）
.\scripts\dev-up.ps1
```

```bash
# Linux/macOS 等价
make setup && make dev-up
```

**统一入口脚本（Sprint 1 交付）：**

| 脚本 | 作用 |
|------|------|
| `scripts/setup.ps1` / `scripts/setup.sh` | 安装 uv、pnpm、拉依赖、建 venv |
| `scripts/dev-start.ps1` | **日常一键启动**（Postgres/Redis + 本机 API/Web） |
| `scripts/dev-stop.ps1` | 停止 dev-start 拉起的全部服务 |
| `scripts/dev-up.ps1` | 全容器 dev compose（含 API 构建，较慢） |
| `scripts/dev-down.ps1` | 停止 dev compose 容器 |
| `scripts/migrate.ps1` | 执行 Alembic |
| `scripts/test.ps1` | 全量 lint + test |
| `Makefile` | Linux/macOS 快捷命令（与 ps1 功能对齐） |

---

## 7. 端口分配（统一，禁止冲突）

| 服务 | 端口 | 协议 |
|------|------|------|
| `web`（Next.js dev） | `3000` | HTTP |
| `api`（FastAPI） | `8000` | HTTP |
| `postgres` | `5432` | TCP（仅 dev 暴露 host） |
| `redis` | `6379` | TCP（仅 dev 暴露 host） |
| `prometheus`（可选） | `9090` | HTTP |
| `browser` 内部 | 不暴露 | 仅 api 内网调用 |

**prod compose：** 仅暴露 `web:3000` 与 `api:8000`（或合并反代 `80`）。

---

## 8. CI/CD 统一（GitHub Actions 或本地等价）

```yaml
# 每次 PR / push main 执行（Sprint 1 落地）
jobs:
  lint-python:   ruff check + ruff format --check + mypy
  lint-web:      pnpm lint + pnpm typecheck
  test-python:   pytest --cov=apps --cov=packages --cov-fail-under=70
  test-web:      pnpm test（如有）
  build-docker:  docker compose -f infra/compose/docker-compose.dev.yml build
```

---

## 9. 依赖管理规则

| 规则 | 说明 |
|------|------|
| Python | `uv lock` 生成 `uv.lock`，提交到 Git |
| Node | `pnpm-lock.yaml` 提交到 Git |
| 新增依赖 | 须说明用途，禁止引入功能重叠库 |
| 安全扫描 | `uv pip audit` / `pnpm audit` 纳入 CI（MS6） |

**禁止引入的重复方案：**

| 已有 | 禁止再引入 |
|------|-----------|
| FastAPI | Flask、Django REST |
| LangGraph | 自研状态机（除非 ADR） |
| Chroma | Pinecone、Milvus（首期） |
| pnpm | npm、yarn |
| uv | poetry、pipenv |
| structlog | 混用 loguru + logging 多套 |

---

## 10. 验收标准（M01 环境部分）

- [ ] `scripts/setup.ps1` 在 Windows 10 干净环境可执行
- [ ] `docker compose dev up` 后所有服务 healthy
- [ ] `scripts/test.ps1` 通过（即使测试为空也须 exit 0）
- [ ] `.env.example` 覆盖全部 `APP_/DB_/LLM_` 变量
- [ ] 版本号与本文件 §2 一致
