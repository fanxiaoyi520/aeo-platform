# M06 — 部署与安全

| 属性 | 值 |
|------|-----|
| **模块 ID** | M06 |
| **优先级** | P0 |
| **里程碑** | MS1（基础）、MS6（生产） |
| **状态** | `completed` |
| **依赖** | M01 |

---

## 1. 目标

实现本地生产级部署，满足「数据不出域、可审计、可恢复」的安全要求。

## 2. 交付物

### 2.1 MS1（dev 环境）

- [ ] `docker-compose.dev.yml`
- [ ] 各服务 Dockerfile
- [ ] `.env.example`
- [ ] 健康检查：`/health`、`/ready`

### 2.2 MS6（prod 环境）

- [ ] `docker-compose.prod.yml`（prod profile）
- [ ] API 认证：API Key 或 JWT（单用户首期）
- [ ] 请求限流：100 req/min per key
- [ ] CORS 白名单
- [ ] 日志：structlog JSON 格式，敏感字段脱敏
- [ ] 数据卷备份脚本
- [ ] 部署文档 `docs/DEPLOYMENT.md`

## 3. 安全规范

| 项 | 要求 |
|----|------|
| 密钥 | 仅环境变量，`.env` 在 `.gitignore` |
| 数据库 | 不暴露公网端口（prod compose 仅 internal network） |
| LLM 调用 | 记录 request_id、token 用量，不记录完整 prompt 中的敏感字段 |
| 文件上传 | 类型白名单 pdf/md/json，单文件 ≤ 10MB |
| 审计 | HITL approve/reject、知识库删除 → `audit_logs` |

## 4. 脱敏规则

日志与 trace 中以下字段替换为 `***`：

- `api_key`, `password`, `supplier_price`, `cost_price`

## 5. 验收标准

1. prod compose 在无外网情况下可启动（LLM 指向内网）
2. 未认证请求返回 401
3. 审计日志可查询最近 100 条 HITL 操作
4. `scripts/backup.sh` 可备份 PostgreSQL + Chroma 数据卷

## 6. 不在本模块范围

- K8s / 云部署
- SOC2 / 等保认证
