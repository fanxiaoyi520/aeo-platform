# Launch AEO — 生产部署指南

> **模块：** M06 部署与安全 · **任务：** S6-05  
> **适用环境：** 单机 Docker Compose（本地 / 内网服务器），数据不出域。

---

## 1. 架构概览

```
┌─────────────┐     ┌─────────────┐
│  Web :3000  │────▶│  API :8000  │
│  Next.js    │     │  FastAPI    │
└─────────────┘     └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        PostgreSQL      Redis       Chroma
        (internal)   (internal)   (volume)
```

| 服务 | 端口（宿主机） | 说明 |
|------|----------------|------|
| **web** | 3000 | 运营工作台 |
| **api** | 8000 | REST API + Swagger `/docs` |
| **postgres** | 无（仅 internal） | 任务、审计、HITL 状态 |
| **redis** | 无（仅 internal） | 限流、缓存 |

Compose 文件：`launch-aeo/infra/compose/docker-compose.prod.yml`

---

## 2. 前置条件

| 项 | 要求 |
|----|------|
| Docker | CLI + Compose v2（Windows 推荐 WSL Ubuntu，见 `scripts/install-docker-admin.cmd`） |
| 磁盘 | ≥ 10 GB（镜像 + 数据卷） |
| 内存 | ≥ 4 GB 可用（API 限制 2G） |
| LLM | OpenAI 兼容网关或内网推理服务（`LLM_BASE_URL` / `LLM_API_KEY`） |

---

## 3. 首次部署

### 3.1 配置密钥

```powershell
cd launch-aeo
copy .env.prod.example .env.prod
# 编辑 .env.prod — 至少修改以下项：
#   POSTGRES_PASSWORD
#   AUTH_API_KEY
#   LLM_API_KEY / EMBED_API_KEY（若不用 hash embeddings）
#   CORS_ORIGINS（生产 Web 域名，如 https://aeo.example.com）
```

**安全提示：** `.env.prod` 已在 `.gitignore` 中，切勿提交仓库。生产环境 `AUTH_API_KEY` 不得使用 `dev-api-key` 等默认值（API 启动时会拒绝）。

### 3.2 启动

```powershell
cd launch-aeo
.\scripts\prod-up.ps1
```

`prod-up.ps1` 会依次：

1. 校验 compose 配置  
2. `docker compose up -d --build`  
3. 执行 Alembic 迁移  
4. 入库知识库（默认 hash embeddings，无需外网 Embedding API）

### 3.3 验证

```powershell
.\scripts\demo.ps1
```

或手动检查：

| URL | 期望 |
|-----|------|
| `http://127.0.0.1:8000/health` | `200` |
| `http://127.0.0.1:8000/ready` | `database` + `redis` 均为 `true` |
| `http://127.0.0.1:3000` | 工作台首页 |
| `http://127.0.0.1:8000/docs` | Swagger（公开，无需 Key） |

带认证的 API 调用：

```powershell
$key = (Get-Content .env.prod | Where-Object { $_ -match '^AUTH_API_KEY=' }) -replace '^AUTH_API_KEY=',''
curl -H "Authorization: Bearer $key" http://127.0.0.1:8000/api/v1/knowledge/stats
```

### 3.4 停止

```powershell
.\scripts\prod-down.ps1
```

数据卷（PostgreSQL、Chroma、Redis）默认保留；`docker compose down -v` 会**删除**所有数据。

---

## 4. 备份与恢复

### 4.1 备份

```powershell
# Windows（调用 WSL bash 或本机 bash）
.\scripts\backup.ps1

# Linux / WSL 直接执行
./scripts/backup.sh
```

输出目录：`launch-aeo/backups/YYYYMMDD_HHMMSS/`

| 文件 | 内容 |
|------|------|
| `postgres.sql` | `pg_dump` 全库（含 schema + 数据） |
| `chroma_data.tar.gz` | Chroma 向量索引目录 |

**建议：** 每日 cron / 计划任务备份；备份文件加密后异地存储。

### 4.2 恢复 PostgreSQL

```powershell
# 确保 prod 栈已启动
Get-Content backups\20260830_120000\postgres.sql | docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml exec -T postgres psql -U aeo -d aeo
```

或在 WSL：

```bash
./scripts/backup.sh  # 先确认 compose 服务名
cat backups/20260830_120000/postgres.sql | docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml exec -T postgres psql -U aeo -d aeo
```

### 4.3 恢复 Chroma

```bash
# 停止 API 后恢复更安全；或热恢复后重启 api 容器
docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml exec -T api sh -c "rm -rf /app/data/chroma/*"
cat backups/20260830_120000/chroma_data.tar.gz | docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml exec -T api tar xzf - -C /app/data/chroma
docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml restart api
```

恢复后可在工作台 `/knowledge` 核对文档数量，或调用 `GET /api/v1/knowledge/stats`。

---

## 5. 安全清单

| 项 | 配置 | 说明 |
|----|------|------|
| API 认证 | `AUTH_API_KEY` | `Authorization: Bearer <key>` |
| 限流 | `RATE_LIMIT_PER_MINUTE=100` | 超限返回 `429` / code `10003` |
| CORS | `CORS_ORIGINS` | 生产必填，仅允许 Web 源 |
| 数据库 | 无 host 端口 | compose internal network |
| 日志脱敏 | 自动 | `api_key`、`password`、`supplier_price`、`cost_price` → `***` |
| 审计 | `GET /api/v1/audit-logs` | 默认 HITL 操作，最多 100 条 |

公开端点（无需 Key）：`/health`、`/ready`、`/metrics`、`/docs`。

---

## 6. 演示流程（10 分钟录制参考）

适用于 MS6 / MS7 验收视频脚本。

1. **启动** — `.\scripts\prod-up.ps1`，等待 healthy  
2. **自动化冒烟** — `.\scripts\demo.ps1`（健康检查 + 认证 + 知识库 + 审计）  
3. **Web 端到端** — 浏览器打开 `http://127.0.0.1:3000`  
   - `/tasks/new` 创建 SKU 任务（如 `X431`）  
   - 详情页观察 SSE Trace  
   - `/tasks/{id}/review` HITL 审核批准  
   - `/tasks/{id}/result` 复制 Listing / 导出 JSON  
4. **CLI（可选）** — `uv run aeo-orchestrate run --sku X431 --auto-approve`  
5. **审计** — Swagger 或 curl 查询 `/api/v1/audit-logs`  

---

## 7. 运维命令速查

```powershell
cd launch-aeo

# 查看容器状态
docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml ps

# API 日志
docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml logs -f api

# 重新入库知识库
docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml exec -T api uv run python /app/scripts/ingest_knowledge.py --reset --hash-embeddings

# 本地开发（非 prod）
.\scripts\dev-up.ps1
```

---

## 8. 故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| API 启动失败「invalid production API key」 | `AUTH_API_KEY` 仍为 dev 默认值 | 修改 `.env.prod` 后重启 |
| `/ready` database=false | Postgres 未就绪或密码不匹配 | 检查 `POSTGRES_PASSWORD` 与 compose 日志 |
| 创建任务失败 | LLM 密钥无效或超时 | 检查 `LLM_*`；内网网关需可达 |
| CORS 错误 | Web 域名未加入白名单 | 更新 `CORS_ORIGINS` 并重启 api |
| 限流 429 | 单 Key 超过 100 req/min | 等待或调高 `RATE_LIMIT_PER_MINUTE`（仅内网调试） |
| Knowledge 为空 | 未执行 ingest | 运行 `prod-up.ps1` 或手动 ingest |

---

## 9. 不在本指南范围

- Kubernetes / 云托管部署  
- TLS 终止（需在反向代理层配置 Nginx / Caddy）  
- 多租户 / SSO  
- 等保 / SOC2 认证  

详见 [`docs/modules/M06-deployment-security.md`](modules/M06-deployment-security.md)。
