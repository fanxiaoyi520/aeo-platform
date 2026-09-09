# AEO Platform 运维手册

> 日常运维操作与应急响应流程。

## 日常检查清单

### 每日检查

- [ ] 服务健康状态：`docker compose ps`
- [ ] API 响应时间：Grafana → HTTP Request Duration p95 < 2s
- [ ] 错误率：Grafana → Error Rate < 1%
- [ ] 磁盘空间：`df -h`（关注 `pg_data`、`backups/`）
- [ ] 备份状态：检查 `backups/` 最新备份时间

### 每周检查

- [ ] Prometheus 存储空间：`docker system df`
- [ ] 日志大小：`docker logs api --tail 1000 | wc -l`
- [ ] 证书有效期：`openssl x509 -enddate -noout -in /path/to/cert.pem`
- [ ] 依赖更新：检查安全公告

## 常见操作

### 重启服务

```bash
# 重启单个服务
docker compose -f infra/compose/docker-compose.prod.yml restart api

# 重启所有服务
docker compose -f infra/compose/docker-compose.prod.yml restart
```

### 查看实时日志

```bash
# API 日志
docker compose -f infra/compose/docker-compose.prod.yml logs -f api

# 按时间过滤（最近 1 小时）
docker compose -f infra/compose/docker-compose.prod.yml logs --since 1h api
```

### 数据库操作

```bash
# 进入 PostgreSQL shell
docker compose -f infra/compose/docker-compose.prod.yml exec postgres psql -U aeo -d aeo

# 常用查询
SELECT count(*) FROM agent_tasks WHERE status = 'running';
SELECT count(*) FROM knowledge_chunks;
\dt  # 列出所有表
\q   # 退出
```

### Redis 操作

```bash
# 进入 Redis CLI
docker compose -f infra/compose/docker-compose.prod.yml exec redis redis-cli

# 常用命令
INFO memory          # 内存使用
INFO keyspace        # 键统计
FLUSHDB              # 清空当前数据库（慎用！）
```

### 知识库重建

```bash
# 通过 API 重建索引
curl -X POST http://localhost:8000/api/v1/knowledge/reindex \
  -H "Authorization: Bearer YOUR_AUTH_KEY"
```

## 应急响应

### API 无响应

**症状**：`/health` 超时或返回 5xx

**排查步骤**：

```bash
# 1. 检查容器状态
docker compose -f infra/compose/docker-compose.prod.yml ps api

# 2. 查看日志
docker compose -f infra/compose/docker-compose.prod.yml logs --tail 100 api

# 3. 检查资源使用
docker stats aeo-api-prod --no-stream

# 4. 重启服务
docker compose -f infra/compose/docker-compose.prod.yml restart api
```

**常见原因**：
- 内存不足 → 增加 `deploy.resources.limits.memory`
- 数据库连接池耗尽 → 检查 `DB_POOL_SIZE` 配置
- LLM API 超时 → 检查 `LLM_TIMEOUT_SECONDS`

### 数据库连接失败

**症状**：API 日志显示 `connection refused` 或 `too many connections`

**排查步骤**：

```bash
# 1. 检查 PostgreSQL 状态
docker compose -f infra/compose/docker-compose.prod.yml ps postgres

# 2. 测试连接
docker compose -f infra/compose/docker-compose.prod.yml exec postgres pg_isready -U aeo

# 3. 查看活跃连接
docker compose -f infra/compose/docker-compose.prod.yml exec postgres psql -U aeo -c "SELECT count(*) FROM pg_stat_activity;"

# 4. 重启 PostgreSQL（会断开所有连接）
docker compose -f infra/compose/docker-compose.prod.yml restart postgres
```

### Redis 内存溢出

**症状**：API 日志显示 `OOM command not allowed`

**紧急处理**：

```bash
# 1. 查看内存使用
docker compose -f infra/compose/docker-compose.prod.yml exec redis redis-cli INFO memory

# 2. 清理过期键
docker compose -f infra/compose/docker-compose.prod.yml exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 3. 增加内存限制（修改 docker-compose.prod.yml）
# 重启 Redis
docker compose -f infra/compose/docker-compose.prod.yml restart redis
```

### 磁盘空间不足

**症状**：`df -h` 显示使用率 > 90%

**清理步骤**：

```bash
# 1. 清理旧备份
find backups/ -maxdepth 1 -mtime +3 -exec rm -rf {} +

# 2. 清理 Docker 无用资源
docker system prune -f
docker volume prune -f

# 3. 清理日志（如果配置了日志文件）
truncate -s 0 /var/log/aeo-*.log

# 4. 压缩旧备份
tar czf backups/archive_$(date +%Y%m).tar.gz backups/20*
rm -rf backups/20*
```

### TLS 证书过期

**症状**：浏览器显示证书警告

**续期步骤**：

```bash
# 1. 手动续期
docker compose -f infra/compose/docker-compose.prod.yml --profile tls run --rm certbot \
  certbot renew --webroot -w /var/www/certbot

# 2. 重载 Nginx
docker compose -f infra/compose/docker-compose.prod.yml --profile tls exec nginx nginx -s reload

# 3. 验证证书
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

## 性能优化

### API 性能调优

```bash
# 调整 worker 数量（修改 .env.prod）
API_WORKERS=4  # 建议：CPU 核心数 * 2 + 1

# 调整数据库连接池
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# 调整 LLM 超时
LLM_TIMEOUT_SECONDS=30
```

### 数据库优化

```sql
-- 检查慢查询
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- 分析表统计信息
ANALYZE;

-- 检查索引使用率
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

### Redis 优化

```bash
# 启用慢查询日志
CONFIG SET slowlog-log-slower-than 10000  # 10ms
CONFIG SET slowlog-max-len 128

# 查看慢查询
SLOWLOG GET 10
```

## 备份验证

定期测试备份恢复：

```bash
# 1. 创建测试数据库
docker compose -f infra/compose/docker-compose.prod.yml exec postgres createdb -U aeo aeo_test

# 2. 恢复备份到测试库
docker compose -f infra/compose/docker-compose.prod.yml exec -T postgres \
  psql -U aeo -d aeo_test < backups/latest/postgres.sql

# 3. 验证数据完整性
docker compose -f infra/compose/docker-compose.prod.yml exec postgres \
  psql -U aeo -d aeo_test -c "SELECT count(*) FROM agent_tasks;"

# 4. 清理测试库
docker compose -f infra/compose/docker-compose.prod.yml exec postgres dropdb -U aeo aeo_test
```

## 监控告警配置

### Prometheus 告警规则

创建 `infra/monitoring/alert-rules.yml`：

```yaml
groups:
  - name: aeo-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(aeo_http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "高错误率 (>10%)"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(aeo_http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高延迟 (p95 > 2s)"
      
      - alert: DiskSpaceLow
        expr: node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "磁盘空间不足 (<10%)"
```

## 升级流程

### 常规升级

```bash
# 1. 备份当前状态
./scripts/backup.sh

# 2. 拉取最新代码
git pull origin main

# 3. 查看变更
git log --oneline HEAD@{1}..HEAD

# 4. 重新构建镜像
docker compose -f infra/compose/docker-compose.prod.yml build

# 5. 滚动更新
docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml up -d

# 6. 验证服务
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

### 数据库迁移

如果新版本包含数据库迁移：

```bash
# Alembic 会自动在 API 启动时执行迁移
# 手动执行：
docker compose -f infra/compose/docker-compose.prod.yml exec api \
  alembic upgrade head
```

## 联系支持

- **紧急问题**：GitHub Issues（标记 `priority: critical`）
- **一般问题**：GitHub Discussions
- **文档错误**：提交 PR 修正
