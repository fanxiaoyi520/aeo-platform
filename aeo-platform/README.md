# AEO Platform — Application Codebase

**AEO** = Autonomous Ecommerce Operator（不是 Answer Engine Optimization）

生产级 AI 电商自主运营系统代码仓库。

> 通用跨境 Listing 优化平台，示例数据见 `pilot/sample-sku-testset.json` 与 `knowledge/products/sample-product.md`。

## 快速开始

> 以下命令均在 **`aeo-platform/`** 目录下执行。克隆仓库后：
>
> ```powershell
> git clone https://github.com/fanxiaoyi520/aeo-platform.git
> cd aeo-platform
> ```

### 日常开发（推荐，一键启动）

```powershell
.\scripts\setup.ps1          # 仅首次
.\scripts\dev-start.ps1      # Postgres/Redis + API + Web，后台运行
```

浏览器：
- **http://127.0.0.1:3000** — Web 界面
- **http://127.0.0.1:8000/docs** — API 文档

停止：`.\scripts\dev-stop.ps1`  
状态：`.\scripts\dev-start.ps1 -Status`  
重建知识库：`.\scripts\dev-start.ps1 -Ingest`

### 方式 A：无 Docker（仅 API 文档）

```powershell
.\scripts\setup.ps1
.\scripts\dev-local.ps1
```

浏览器：**http://127.0.0.1:8000/docs**

### 方式 B：Docker CLI（全容器，含 API 镜像构建，较慢）

数据目录默认在 `scripts/install-docker-cli.ps1` 的 `$DataRoot`（可按本机修改）。

```powershell
# 1. 管理员 PowerShell（在 aeo-platform/ 目录下）
.\scripts\install-docker-cli.ps1

# 首次 WSL 需：重启 → 打开 Ubuntu 设密码 → 再运行一次 install 脚本

# 2. 普通 PowerShell 启动项目（全容器，较慢；日常用 dev-start.ps1）
.\scripts\dev-up.ps1
```

验证：
```powershell
wsl -d Ubuntu docker --version
wsl -d Ubuntu docker compose version
```

停止：
```powershell
.\scripts\dev-down.ps1
```

> **不用 Docker Desktop**。Docker Engine 装在 WSL Ubuntu 里，只有 `docker` 命令行。

## 目录结构

```
aeo-platform/
├── apps/api/           # FastAPI 主服务
├── packages/shared/    # 共享类型、错误码
├── packages/llm/       # LLM 适配器
├── infra/compose/      # docker-compose（WSL docker 使用）
├── scripts/
│   ├── install-docker-cli.ps1  # 安装 WSL 命令行 Docker
│   ├── docker-cli.ps1          # docker / wsl docker 封装
│   ├── dev-up.ps1
│   └── dev-local.ps1
└── knowledge/          # RAG 源文档（MS2）
```

## API 端点

| 端点 | 说明 | 认证 |
|------|------|------|
| `GET /health` | 存活检查 | 否 |
| `GET /ready` | DB + Redis 就绪 | 否 |
| `GET /metrics` | Prometheus 指标 | 否 |
| `POST /api/v1/knowledge/search` | RAG 检索 | 是（Bearer Token） |
| `POST /api/v1/knowledge/reindex` | 重建知识库索引 | 是 |
| `GET /api/v1/knowledge/stats` | 索引统计 | 是 |

### 索引知识库（无需 LLM Key）

```powershell
.\scripts\ingest.ps1
```

### 测试 RAG（需先 dev-local.ps1 启动 API）

在 `/docs` 里找到 **knowledge** 分组：
- `POST /api/v1/knowledge/reindex` — 重建索引
- `POST /api/v1/knowledge/search` — 示例 body:
```json
{"query": "Amazon title 字数限制", "platform": "amazon"}
```
