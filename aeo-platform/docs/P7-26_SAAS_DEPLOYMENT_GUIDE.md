# P7-26: SaaS Deployment Guide & Operations Manual

**Status**: DRAFT  
**Date**: 2026-09-18  
**Phase**: P7-MS4 (SaaS Preparation)

---

## 1. Deployment Architecture

### 1.1 Overview

AEO Platform is designed as a multi-tenant SaaS application with the following deployment characteristics:

- **Stateless API tier**: Horizontally scalable FastAPI workers
- **Stateful services**: PostgreSQL (primary data), Redis (cache/sessions), S3-compatible storage (files)
- **Background workers**: Orchestrator for async tasks (order sync, inventory updates, ad optimization)
- **Multi-tenant isolation**: Row-level tenant scoping via `tenant_id` foreign keys

### 1.2 Infrastructure Requirements

**Minimum (Development/Staging)**:
- 2 vCPU, 4 GB RAM
- PostgreSQL 14+
- Redis 6+
- 10 GB storage

**Production (Small, <100 tenants)**:
- 4 vCPU, 8 GB RAM (API)
- 2 vCPU, 4 GB RAM (Orchestrator)
- PostgreSQL 14+ (managed, e.g., RDS)
- Redis 6+ (managed, e.g., ElastiCache)
- 100 GB storage (S3-compatible)

**Production (Medium, 100-1000 tenants)**:
- 8 vCPU, 16 GB RAM (API, 2+ instances)
- 4 vCPU, 8 GB RAM (Orchestrator, 2+ instances)
- PostgreSQL 14+ (managed, read replicas)
- Redis 6+ (cluster mode)
- 500 GB storage

**Production (Large, >1000 tenants)**:
- Auto-scaling API tier (8-32 vCPU, 16-64 GB RAM)
- Dedicated orchestrator pool per workload type
- PostgreSQL with horizontal sharding by tenant
- Redis cluster with partitioning
- Multi-region deployment

---

## 2. Deployment Procedures

### 2.1 Initial Setup

**Prerequisites**:
- Python 3.11+
- PostgreSQL 14+ with `pgcrypto` extension
- Redis 6+
- S3-compatible storage bucket
- SMTP server for email notifications
- Stripe account for billing (optional)

**Database Initialization**:

```bash
# Create database
createdb aeo_platform

# Run migrations
cd aeo-platform
python -m alembic upgrade head

# Verify schema
python -c "from apps.api.db import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

**Environment Variables**:

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/aeo_platform
REDIS_URL=redis://host:6379/0
SECRET_KEY=<64-char-random-string>
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_S3_BUCKET=aeo-platform-files
AWS_REGION=us-east-1

# Optional
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=<password>
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
LOG_LEVEL=INFO
MAX_WORKERS=4
```

### 2.2 Application Deployment

**Option A: Docker Compose (Small/Medium)**

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    image: aeo-platform/api:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    ports:
      - "8000:8000"
    deploy:
      replicas: 2
  
  orchestrator:
    image: aeo-platform/orchestrator:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    deploy:
      replicas: 1
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
```

**Option B: Kubernetes (Large)**

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aeo-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aeo-api
  template:
    metadata:
      labels:
        app: aeo-api
    spec:
      containers:
      - name: api
        image: aeo-platform/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: aeo-secrets
              key: database-url
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
          limits:
            cpu: "4"
            memory: "8Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 2.3 Rolling Updates

**Zero-downtime deployment**:

```bash
# Kubernetes
kubectl set image deployment/aeo-api api=aeo-platform/api:v2.0.0
kubectl rollout status deployment/aeo-api

# Docker Compose
docker-compose pull api
docker-compose up -d --no-deps --build api
```

**Database migrations**:

```bash
# Run migrations before deploying new code
python -m alembic upgrade head

# Verify migration success
python -c "from alembic.script import ScriptDirectory; from alembic.config import Config; config = Config(); script = ScriptDirectory.from_config(config); print(f'Current revision: {script.get_current_head()}')"
```

---

## 3. Scaling Strategies

### 3.1 Horizontal Scaling

**API Tier**:
- Stateless workers behind load balancer
- Scale based on CPU utilization (>70% → add instance)
- Scale based on request latency (p95 > 500ms → add instance)
- Use connection pooling (pgbouncer) to manage database connections

**Orchestrator**:
- Partition workloads by queue (orders, inventory, ads)
- Scale each worker pool independently
- Use Redis streams for work distribution
- Implement leader election for singleton tasks

**Database**:
- Read replicas for query offloading (reporting, analytics)
- Connection pooling with pgbouncer (max 100 connections per pool)
- Partition large tables by `tenant_id` (hash partitioning)
- Archive old data to cold storage (>90 days)

### 3.2 Vertical Scaling

**When to scale up**:
- Single instance CPU > 80% sustained
- Memory pressure (swap usage > 10%)
- Disk I/O saturation (>80% utilization)
- Network bandwidth limits approached

**Scaling checklist**:
1. Increase instance size (e.g., 4 vCPU → 8 vCPU)
2. Adjust worker count (`MAX_WORKERS` env var)
3. Increase database connection pool size
4. Monitor for 24 hours before further scaling

### 3.3 Multi-Region Deployment

**Architecture**:
- Active-active across 2+ regions
- DNS-based routing (Route 53 latency-based)
- Cross-region database replication (async)
- CDN for static assets (CloudFront)

**Data consistency**:
- Eventual consistency for cross-region reads
- Strong consistency within region
- Conflict resolution: last-write-wins with vector clocks
- Tenant affinity: pin tenant to primary region

---

## 4. Monitoring & Alerting

### 4.1 Metrics Collection

**Application metrics** (Prometheus format):

```python
# apps/api/metrics.py
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

TENANT_COUNT = Gauge(
    'tenants_total',
    'Total active tenants'
)

QUEUE_DEPTH = Gauge(
    'orchestrator_queue_depth',
    'Pending tasks in orchestrator queue',
    ['queue_name']
)
```

**Infrastructure metrics**:
- CPU utilization (per instance)
- Memory usage (per instance)
- Disk I/O (reads/writes per second)
- Network throughput (bytes in/out)
- Database connections (active/idle)
- Redis memory usage

### 4.2 Alerting Rules

**Critical alerts** (page immediately):
- API error rate > 5% for 5 minutes
- Database connection pool exhausted
- Orchestrator queue depth > 10000
- Disk usage > 90%
- SSL certificate expiring in <7 days

**Warning alerts** (notify during business hours):
- API latency p95 > 1 second for 10 minutes
- CPU utilization > 80% for 30 minutes
- Memory usage > 85% for 15 minutes
- Failed login attempts > 100/hour
- Tenant quota usage > 90%

**Info alerts** (log for review):
- Deployment completed
- Database migration executed
- New tenant onboarded
- Billing reconciliation completed

### 4.3 Dashboards

**Grafana dashboard panels**:
1. **Overview**: Request rate, error rate, latency p50/p95/p99
2. **Tenants**: Active tenants, quota usage, top tenants by API calls
3. **Infrastructure**: CPU, memory, disk, network per instance
4. **Database**: Query rate, connection count, slow queries, replication lag
5. **Orchestrator**: Queue depth, task duration, failure rate per queue
6. **Billing**: MRR, churn rate, failed payments, revenue per tenant

---

## 5. Backup & Recovery

### 5.1 Backup Strategy

**Database backups**:
- Automated daily full backup (02:00 UTC)
- Continuous WAL archiving for point-in-time recovery
- Retention: 30 days daily, 12 weekly, 6 monthly
- Cross-region replication for disaster recovery

**File storage backups**:
- S3 versioning enabled
- Cross-region replication to secondary region
- Lifecycle policy: archive to Glacier after 90 days

**Configuration backups**:
- Environment variables in secrets manager (AWS Secrets Manager)
- Infrastructure as Code (Terraform/CloudFormation)
- Version control for all configuration files

### 5.2 Recovery Procedures

**Database recovery**:

```bash
# Point-in-time recovery (AWS RDS)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier aeo-prod \
  --target-db-instance-identifier aeo-prod-restored \
  --restore-time "2026-09-18T10:00:00Z"

# Verify restored database
psql -h aeo-prod-restored.xxx.us-east-1.rds.amazonaws.com -U admin -d aeo_platform -c "SELECT COUNT(*) FROM tenants;"
```

**Application recovery**:

```bash
# Rollback to previous version
kubectl rollout undo deployment/aeo-api

# Or deploy specific version
kubectl set image deployment/aeo-api api=aeo-platform/api:v1.9.0

# Verify health
curl https://api.aeo-platform.com/health/ready
```

**Disaster recovery** (full region failure):
1. Promote read replica in secondary region to primary
2. Update DNS to point to secondary region
3. Deploy application to secondary region
4. Verify data consistency
5. Notify tenants of temporary degradation

**RTO/RPO targets**:
- **RTO** (Recovery Time Objective): <1 hour
- **RPO** (Recovery Point Objective): <5 minutes (WAL archiving)

---

## 6. Security Hardening

### 6.1 Network Security

- VPC with private subnets for database/Redis
- Public subnets only for load balancer
- Security groups: restrict database access to API tier only
- WAF rules: block SQL injection, XSS, rate limiting
- DDoS protection (AWS Shield)

### 6.2 Application Security

- HTTPS only (TLS 1.2+)
- HSTS headers enabled
- CSP headers for frontend
- Rate limiting per tenant (quotas.py)
- Input validation on all endpoints
- SQL injection prevention (parameterized queries)
- XSS prevention (output encoding)
- CSRF protection (SameSite cookies)

### 6.3 Data Security

- Encryption at rest (AES-256 for credentials, see `credentials.py`)
- Encryption in transit (TLS 1.2+)
- Tenant isolation (row-level security, see `tenant.py`)
- Audit logging for sensitive operations
- Regular security scans (quarterly penetration testing)
- SOC 2 Type II compliance roadmap

### 6.4 Access Control

- RBAC for admin panel (admin, operator, viewer roles)
- API key rotation (90-day policy)
- MFA for admin access
- SSH key-based authentication only (no passwords)
- Bastion host for database access
- Just-in-time access for production debugging

---

## 7. Operational Runbooks

### 7.1 High CPU Utilization

**Symptoms**: CPU > 80% for >15 minutes  
**Impact**: Increased latency, potential timeouts

**Diagnosis**:
```bash
# Check top processes
top -b -n 1 | head -20

# Check API request rate
curl -s http://localhost:8000/metrics | grep http_requests_total

# Check orchestrator queue depth
redis-cli LLEN orchestrator:queue:orders
```

**Resolution**:
1. Scale out: add more API instances
2. Identify slow queries: `SELECT * FROM pg_stat_activity WHERE state = 'active';`
3. Optimize hot code paths
4. Increase instance size if vertical scaling needed

### 7.2 Database Connection Exhaustion

**Symptoms**: "Too many clients" errors, API 503s  
**Impact**: Application unable to serve requests

**Diagnosis**:
```bash
# Check active connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check connection pool status
curl -s http://localhost:8000/metrics | grep db_connections

# Identify long-running queries
psql -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;"
```

**Resolution**:
1. Kill long-running queries: `SELECT pg_terminate_backend(pid);`
2. Increase connection pool size (restart API with higher `MAX_WORKERS`)
3. Deploy pgbouncer for connection pooling
4. Scale database vertically if needed

### 7.3 Orchestrator Queue Backlog

**Symptoms**: Queue depth > 10000, tasks not processing  
**Impact**: Delayed order sync, inventory updates, ad optimization

**Diagnosis**:
```bash
# Check queue depth
redis-cli LLEN orchestrator:queue:orders
redis-cli LLEN orchestrator:queue:inventory

# Check worker status
ps aux | grep orchestrator

# Check worker logs
kubectl logs deployment/aeo-orchestrator --tail=100
```

**Resolution**:
1. Scale orchestrator workers: `kubectl scale deployment/aeo-orchestrator --replicas=5`
2. Check for stuck tasks: `redis-cli LRANGE orchestrator:queue:orders 0 10`
3. Restart workers if hung: `kubectl rollout restart deployment/aeo-orchestrator`
4. Increase worker concurrency in config

### 7.4 Tenant Quota Exceeded

**Symptoms**: Tenant reports 429 errors, quota usage > 100%  
**Impact**: Tenant unable to make API calls

**Diagnosis**:
```bash
# Check tenant quota usage
psql -c "SELECT tenant_id, api_calls_used, api_calls_limit FROM tenant_quotas WHERE tenant_id = '<tenant-id>';"

# Check recent API calls
psql -c "SELECT COUNT(*) FROM api_logs WHERE tenant_id = '<tenant-id>' AND created_at > NOW() - INTERVAL '1 hour';"
```

**Resolution**:
1. Verify quota enforcement logic in `quotas.py`
2. Check for quota reset timing (daily/monthly)
3. Offer tenant upgrade to higher plan tier
4. Temporary quota increase if legitimate spike

### 7.5 Billing Reconciliation Failure

**Symptoms**: Reconciliation report shows discrepancies  
**Impact**: Revenue leakage, incorrect tenant billing

**Diagnosis**:
```bash
# Check reconciliation report
python -c "from apps.api.billing import BillingReconciler; reconciler = BillingReconciler(); report = reconciler.reconcile_month('2026-09'); print(report)"

# Check Stripe webhook logs
kubectl logs deployment/aeo-api | grep "stripe_webhook"

# Verify tenant usage data
psql -c "SELECT tenant_id, SUM(api_calls) FROM tenant_usage WHERE month = '2026-09' GROUP BY tenant_id;"
```

**Resolution**:
1. Retry failed Stripe API calls
2. Manually adjust tenant usage if data corrupted
3. Issue credits for overcharged tenants
4. Update reconciliation logic if systematic error

---

## 8. Performance Optimization

### 8.1 Database Optimization

**Indexing strategy**:
- Primary keys: `id` (UUID)
- Foreign keys: `tenant_id`, `user_id`
- Query patterns: `(tenant_id, created_at)`, `(tenant_id, status)`
- Partial indexes: `WHERE status = 'active'`

**Query optimization**:
- Use `EXPLAIN ANALYZE` for slow queries
- Avoid `SELECT *`, specify columns
- Batch operations with `INSERT ... ON CONFLICT`
- Use `LIMIT` for large result sets
- Connection pooling with pgbouncer

**Partitioning**:
```sql
-- Partition large tables by tenant
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  ...
) PARTITION BY HASH (tenant_id);

CREATE TABLE orders_p0 PARTITION OF orders FOR VALUES WITH (MODULUS 8, REMAINDER 0);
CREATE TABLE orders_p1 PARTITION OF orders FOR VALUES WITH (MODULUS 8, REMAINDER 1);
-- ... up to p7
```

### 8.2 Caching Strategy

**Redis caching**:
- Session data (TTL: 24 hours)
- API response cache (TTL: 5 minutes, cache key: `tenant_id:endpoint:params`)
- Tenant metadata (TTL: 1 hour)
- Rate limit counters (TTL: 1 minute)

**Cache invalidation**:
- Write-through for tenant metadata
- TTL-based expiration for API responses
- Explicit invalidation on data updates
- Cache stampede prevention (singleflight pattern)

### 8.3 Async Processing

**Orchestrator patterns**:
- Priority queues (critical > high > normal > low)
- Retry with exponential backoff (3 attempts, 1s/2s/4s delays)
- Dead letter queue for failed tasks
- Idempotency keys for duplicate prevention

**Task scheduling**:
- Cron-based for recurring tasks (hourly sync, daily reports)
- Event-driven for reactive tasks (order received → inventory update)
- Batch processing for bulk operations (nightly reconciliation)

---

## 9. Compliance & Governance

### 9.1 Data Retention

- **Active tenant data**: Retained indefinitely
- **Deleted tenant data**: 30-day grace period, then hard delete
- **Audit logs**: 7 years (financial regulations)
- **API logs**: 90 days (operational), then archive
- **Backups**: 30 days daily, 12 weekly, 6 monthly

### 9.2 Privacy (GDPR)

- Right to access: Export tenant data via `data_export.py`
- Right to rectification: Update tenant records via API
- Right to erasure: Delete tenant and all associated data
- Data portability: CSV/JSON export in standard formats
- Consent management: Track consent in `tenant_consents` table

### 9.3 Audit Trail

**Logged events**:
- Tenant creation/deletion
- User login/logout
- API key rotation
- Quota changes
- Billing adjustments
- Data export/download
- Admin actions

**Log format**:
```json
{
  "timestamp": "2026-09-18T10:00:00Z",
  "event": "tenant_created",
  "actor": "admin@example.com",
  "tenant_id": "uuid",
  "details": {"plan": "pro"},
  "ip_address": "1.2.3.4"
}
```

---

## 10. Troubleshooting

### 10.1 Common Issues

**Issue**: API returns 500 Internal Server Error  
**Cause**: Unhandled exception in request handler  
**Fix**: Check logs (`kubectl logs`), identify root cause, add error handling

**Issue**: Slow API responses (>5s)  
**Cause**: Slow database query, missing index, lock contention  
**Fix**: `EXPLAIN ANALYZE` query, add index, optimize query, check for locks

**Issue**: Orchestrator tasks not executing  
**Cause**: Worker crashed, queue full, Redis connection lost  
**Fix**: Restart workers, check queue depth, verify Redis connectivity

**Issue**: Tenant data leak (cross-tenant access)  
**Cause**: Missing `tenant_id` filter in query  
**Fix**: Add `apply_tenant_filter` to query, audit all endpoints

### 10.2 Debugging Tools

**Enable debug logging**:
```bash
export LOG_LEVEL=DEBUG
```

**Profile slow requests**:
```python
# apps/api/middleware.py
import cProfile

class ProfilerMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        profiler = cProfile.Profile()
        profiler.enable()
        await self.app(scope, receive, send)
        profiler.disable()
        profiler.print_stats(sort='cumulative')
```

**Database query analysis**:
```sql
-- Find slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_all_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 10;
```

---

## 11. Cost Optimization

### 11.1 Infrastructure Costs

**Compute**:
- Use reserved instances for baseline load (30% savings)
- Spot instances for batch processing (70% savings)
- Auto-scaling to match demand (avoid over-provisioning)

**Database**:
- Right-size instances (monitor CPU/memory utilization)
- Use read replicas for reporting (offload primary)
- Archive old data to reduce storage costs

**Storage**:
- S3 Intelligent-Tiering for automatic cost savings
- Lifecycle policies to move old data to Glacier
- Compress large files before upload

### 11.2 Monitoring Costs

**Tools**:
- Prometheus + Grafana (self-hosted, low cost)
- AWS CloudWatch (pay-per-metric)
- Datadog (expensive but comprehensive)

**Optimization**:
- Sample high-frequency metrics (1 per minute, not 1 per second)
- Aggregate metrics before storage (5-minute rollups)
- Retain detailed metrics for 7 days, aggregates for 90 days

---

## 12. Future Enhancements

### 12.1 Roadmap

**Q4 2026**:
- Multi-region deployment (US + EU)
- Kubernetes auto-scaling (HPA based on custom metrics)
- Advanced caching (Redis Cluster, CDN integration)

**Q1 2027**:
- Database sharding by tenant (horizontal scaling)
- Event sourcing for audit trail
- GraphQL API for flexible queries

**Q2 2027**:
- Machine learning for demand forecasting
- Automated capacity planning
- Self-healing infrastructure (auto-remediation)

### 12.2 Technology Evaluations

- **Service mesh**: Istio for traffic management, mTLS
- **Serverless**: AWS Lambda for event-driven tasks
- **Observability**: OpenTelemetry for distributed tracing
- **CI/CD**: ArgoCD for GitOps deployments

---

## 13. References

- [`P7-22_TENANT_ISOLATION_AUDIT.md`](P7-22_TENANT_ISOLATION_AUDIT.md) — Tenant isolation audit
- [`04_ARCHITECTURE_STANDARDS.md`](04_ARCHITECTURE_STANDARDS.md) — Architecture standards
- [`05_PERFORMANCE_STANDARDS.md`](05_PERFORMANCE_STANDARDS.md) — Performance standards
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Production Checklist](https://www.postgresql.org/docs/current/production.html)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

---

**Document owner**: AI Agent  
**Last updated**: 2026-09-18  
**Review cycle**: Quarterly
