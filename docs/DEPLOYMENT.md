# AEO Platform 生产部署指南

> 本文档指导如何在生产环境部署 AEO Platform。

## 前置条件

- Docker Engine 24.0+ 与 Docker Compose v2.20+
- 至少 8GB RAM、4 CPU 核心
- 已注册域名（用于 TLS 证书）
- PostgreSQL 客户端工具（可选，用于手动备份/恢复）

## 快速部署

### 1. 克隆仓库

```bash
git clone https://github.com/fanxiaoyi520/aeo-platform.git
cd aeo-platform
```

### 2. 配置环境变量

```bash
cp .env.prod.example .env.prod
```

编辑 `.env.prod`，**必须修改**以下配置：

| 变量 | 说明 | 示例 |
|------|------|------|
| `POSTGRES_PASSWORD` | 数据库密码 | `your-strong-password-here` |
| `LLM_API_KEY` | LLM API 密钥 | `sk-...` |
| `EMBED_API_KEY` | Embedding API 密钥 | `sk-...` |
| `AUTH_API_KEY` | API 认证密钥 | `your-auth-key` |
| `GRAFANA_ADMIN_PASSWORD` | Grafana 管理员密码 | `your-grafana-password` |
| `CORS_ORIGINS` | 前端域名 | `https://your-domain.com` |

### 3. 启动基础服务

```bash
docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml up -d
```

验证服务状态：

```bash
docker compose -f infra/compose/docker-compose.prod.yml ps
```

应看到所有服务状态为 `running` 或 `healthy`。

### 4. 启用 TLS（推荐）

如果已配置域名和 DNS 指向服务器 IP：

```bash
docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml --profile tls up -d
```

首次部署需要手动获取证书：

```bash
# 停止 nginx
docker compose -f infra/compose/docker-compose.prod.yml --profile tls stop nginx

# 获取证书（替换 your-domain.com）
docker compose -f infra/compose/docker-compose.prod.yml --profile tls run --rm certbot \
  certbot certonly --webroot -w /var/www/certbot -d your-domain.com --email your-email@example.com --agree-tos

# 修改 nginx.conf 中的 server_name 为实际域名
# 重启 nginx
docker compose -f infra/compose/docker-compose.prod.yml --profile tls start nginx
```

### 5. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health
curl http://localhost:8000/ready

# Prometheus 指标
curl http://localhost:8000/metrics

# Grafana 看板（默认端口 3001）
# 访问 http://your-server:3001
# 用户名: admin（或 GRAFANA_ADMIN_USER）
# 密码: 配置的 GRAFANA_ADMIN_PASSWORD
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| API | 8000 | FastAPI 主服务 |
| Web | 3000 | Next.js 前端 |
| Grafana | 3001 | 监控看板 |
| Nginx (TLS) | 80, 443 | 反向代理（需 tls profile） |

**注意**：Prometheus (9090) 仅内部网络可访问，不暴露到主机。

## 备份与恢复

### 手动备份

```bash
./scripts/backup.sh
```

备份文件保存在 `backups/{timestamp}/` 目录，包含：
- `postgres.sql` — 数据库完整备份
- `redis.rdb` — Redis 快照
- `chroma_data.tar.gz` — 知识库向量数据
- `manifest.txt` — 备份元数据

### 自动备份

配置 cron 定时执行：

```bash
# 每天凌晨 2 点备份
0 2 * * * cd /path/to/aeo-platform && ./scripts/backup.sh >> /var/log/aeo-backup.log 2>&1
```

备份保留策略：默认保留 7 天，可通过 `BACKUP_RETENTION_DAYS` 环境变量调整。

### 恢复

```bash
# 恢复 PostgreSQL
docker compose -f infra/compose/docker-compose.prod.yml exec -T postgres psql -U aeo -d aeo < backups/{timestamp}/postgres.sql

# 恢复 Chroma
docker compose -f infra/compose/docker-compose.prod.yml exec -T api tar xzf - -C /app/data/chroma < backups/{timestamp}/chroma_data.tar.gz
```

## 监控与告警

### Grafana 看板

访问 `http://your-server:3001`，预配置看板包括：

- HTTP 请求率与延迟（p95）
- Agent 执行次数与延迟
- LLM 调用与 Token 使用
- 任务并发数
- RAG 检索统计
- 错误率（5xx）

### Prometheus

内部访问：`http://api:9090`（从容器内）

Prometheus 自动抓取 API 指标，配置见 `infra/monitoring/prometheus.yml`。

## 日志

查看服务日志：

```bash
# API 日志
docker compose -f infra/compose/docker-compose.prod.yml logs -f api

# 所有服务
docker compose -f infra/compose/docker-compose.prod.yml logs -f
```

## 资源限制

生产 Compose 已配置资源限制：

| 服务 | CPU | 内存 |
|------|-----|------|
| postgres | 1 核 | 1GB |
| redis | 0.5 核 | 256MB |
| api | 2 核 | 2GB |
| web | 1 核 | 512MB |
| prometheus | 0.5 核 | 512MB |
| grafana | 0.5 核 | 256MB |
| nginx | 0.5 核 | 128MB |

根据实际负载调整 `docker-compose.prod.yml` 中的 `deploy.resources`。

## 安全加固

### 已实施

- ✅ TLS 1.2/1.3（Let's Encrypt）
- ✅ HSTS、CSP、X-Frame-Options 等安全头
- ✅ API 速率限制（30r/s，burst 50）
- ✅ Prometheus 仅内部网络访问
- ✅ Redis AOF 持久化
- ✅ PostgreSQL 密码认证
- ✅ Grafana 自定义管理员密码

### 建议额外措施

- 配置防火墙规则，仅开放 80/443 端口
- 定期更新 Docker 镜像：`docker compose pull && docker compose up -d`
- 监控磁盘空间，特别是 `pg_data` 和 `backups/`
- 配置离线备份（如 S3、OSS）

## 故障排查

### API 无法连接数据库

```bash
# 检查 PostgreSQL 状态
docker compose -f infra/compose/docker-compose.prod.yml ps postgres

# 查看 PostgreSQL 日志
docker compose -f infra/compose/docker-compose.prod.yml logs postgres
```

### Redis 连接失败

```bash
# 检查 Redis 状态
docker compose -f infra/compose/docker-compose.prod.yml exec redis redis-cli ping
```

### 证书续期失败

```bash
# 手动续期
docker compose -f infra/compose/docker-compose.prod.yml --profile tls run --rm certbot \
  certbot renew --webroot -w /var/www/certbot

# 重载 Nginx
docker compose -f infra/compose/docker-compose.prod.yml --profile tls exec nginx nginx -s reload
```

## 升级

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker compose -f infra/compose/docker-compose.prod.yml build

# 滚动更新
docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml up -d
```

## 支持

- GitHub Issues: https://github.com/fanxiaoyi520/aeo-platform/issues
- 文档: `docs/` 目录
