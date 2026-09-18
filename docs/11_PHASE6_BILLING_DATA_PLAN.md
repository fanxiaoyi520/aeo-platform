# Phase 6 — 计费集成与真实店铺数据迁移

> **状态：** `APPROVED` — 2026-09-14 用户批准  
> **前置条件：** Phase 5 多租户 SaaS ✅（P5-01~11 全部完成）  
> **创建日期：** 2026-09-14  
> **性质：** 生产商业化交付；将 mock 数据层替换为真实 API，并接入 SaaS 计费系统。

---

## 1. 背景与目标

Phase 1~5 建立了完整的多租户 SaaS 平台，但存在两个关键缺口：

1. **计费系统缺失**：租户 `plan` 字段为静态字符串（free/pro/enterprise），无支付网关、无订阅生命周期、无发票。用户无法自助升级/降级/取消。
2. **数据层仍为 Mock**：Amazon SP-API、Shopify Admin API、Google Ads、Facebook Ads 均为 mock adapter + JSON fixtures；仪表盘/指标/分析使用内联 mock 生成器。无真实店铺数据流入。

**Phase 6 目标：**
- 接入 Stripe 实现订阅计费闭环（注册→试用→付费→升降级→取消→发票）
- 将 mock adapter 替换为真实 API 实现，按优先级分批上线
- 保持向后兼容：无凭据时自动降级到 mock，不影响开发/测试环境

---

## 2. 范围

### 2.1 范围内（In Scope）

| 轨道 | 内容 |
|------|------|
| **P6-A 计费** | Stripe Checkout + Customer Portal、Subscription/Invoice DB 模型、Webhook 处理、Plan 生命周期 API、计费前端（定价页/订阅管理/发票历史）、max_users 配额执行 |
| **P6-B 数据迁移** | Amazon SP-API OAuth + 4 Protocol 实现、Shopify Admin API + 工厂切换、真实指标聚合替换 Style-B mock 生成器、data_source 标记翻转、凭据管理（加密存储 + 设置 UI） |

### 2.2 范围外（Out of Scope）

- Google Ads / Facebook Ads 真实 API（无消费端接线，延至 Phase 7）
- TikTok 店铺数据集成（不存在 mock 层）
- 多币种/税务合规（Stripe Tax 基础集成可选，完整税务延后）
- 自助服务退款流程（人工处理）
- 真实卖家号获取（用户侧前置条件）

---

## 3. 里程碑

| 里程碑 | 名称 | 预估工期 | 依赖 | 交付物 |
|--------|------|----------|------|--------|
| **P6-MS1** | 计费基础 | 1.5 周 | Phase 5 | Stripe 集成 + 订阅模型 + Webhook + Plan API |
| **P6-MS2** | 计费前端 | 1 周 | P6-MS1 | 定价页 + 订阅管理 + 发票历史 + 配额执行 |
| **P6-MS3** | Amazon 真实数据 | 2 周 | 卖家号凭据 | SP-API OAuth + Listings/Orders/Advertising/Inventory 实现 |
| **P6-MS4** | Shopify 真实数据 | 1.5 周 | Shopify 凭据 | Admin API 实现 + 工厂切换 + 凭据管理 UI |
| **P6-MS5** | 指标真实化 | 1 周 | P6-MS3/MS4 | 替换 Style-B mock 生成器 + data_source 翻转 + 验收 |

**总工期：~7 周**（P6-A 与 P6-B 可并行；MS3/MS4 依赖用户提供真实凭据）

---

## 4. 任务分解

### P6-MS1 — 计费基础（后端）

| ID | 任务 | 模块 | 依赖 | 验收 |
|----|------|------|------|------|
| P6-01 | Stripe SDK 集成 + 配置（API key、webhook secret、price IDs） | M06 | — | `stripe` 依赖安装；health check 验证连通性 |
| P6-02 | 订阅/发票 DB 模型 + Alembic 迁移（subscriptions、invoices、billing_events 表） | M01 | P6-01 | 迁移可逆；模型含 stripe_customer_id、status、current_period_end |
| P6-03 | Tenant 模型扩展：stripe_customer_id、trial_ends_at、billing_status 字段 | M01 | P6-02 | 迁移 0008；现有租户不受影响 |
| P6-04 | 计费服务层：create_checkout_session、create_portal_session、sync_subscription、handle_plan_change | M06 | P6-02/03 | 单测覆盖（mock Stripe API） |
| P6-05 | Stripe Webhook 端点：checkout.session.completed、customer.subscription.updated/deleted、invoice.payment_failed | M06 | P6-04 | 签名验证；事件幂等处理；plan 自动同步到 tenants.plan |
| P6-06 | 计费 API 路由：POST /billing/checkout、POST /billing/portal、GET /billing/subscription、GET /billing/invoices | M06 | P6-04/05 | 需 owner/admin 角色；返回 Stripe URL 或订阅状态 |
| P6-07 | Plan 定义表（plans）：price_id、monthly_tasks、max_users、features JSON；替换硬编码 PLAN_QUOTAS | M06 | P6-02 | quota_service 从 DB 读取；向后兼容 fallback |
| P6-08 | max_users 配额执行：invite_member 时检查当前成员数 vs plan limit | M06 | P6-07 | 超限返回 403；测试覆盖 |
| P6-09 | P6-MS1 验收：计费服务集成测试 + webhook 模拟 + plan 同步验证 | ALL | P6-01~08 | test.ps1 全绿；覆盖率 ≥ 70% |

### P6-MS2 — 计费前端

| ID | 任务 | 模块 | 依赖 | 验收 |
|----|------|------|------|------|
| P6-10 | 定价页（/pricing）：三档 plan 卡片 + 功能对比 + CTA 按钮 | M05 | P6-06 | 公开页面；CTA 跳转 Stripe Checkout |
| P6-11 | 订阅管理 UI：设置页增加「订阅」区域（当前 plan、续期日期、管理按钮→Stripe Portal） | M05 | P6-06 | owner/admin 可见；Portal 链接有效 |
| P6-12 | 发票历史页（/billing/invoices）：列表 + 下载链接 | M05 | P6-06 | 分页；PDF 下载跳转 Stripe |
| P6-13 | 配额超限 UX：任务创建/成员邀请超限时显示升级提示 + 跳转定价页 | M05 | P6-08 | 429/403 响应触发升级引导 |
| P6-14 | 前端计费 API 代理路由（/api/billing/*） | M05 | P6-06 | 传递 access token；错误处理一致 |
| P6-15 | P6-MS2 验收：手动走通 注册→试用→升级→Portal→发票 全流程 | ALL | P6-10~14 | 截图/录屏证据；test.ps1 全绿 |

### P6-MS3 — Amazon 真实数据

| ID | 任务 | 模块 | 依赖 | 验收 |
|----|------|------|------|------|
| P6-16 ✅ | SP-API OAuth 实现：LWA token 刷新（refresh_token→access_token）+ 缓存 | MV-M10 | — | `get_access_token()` 返回真实 token；过期自动刷新 |
| P6-17 ✅ | SpApiListingsAdapter 实现：get_listing、list_listings（Catalog Items API） | MV-M10 | P6-16 | 满足 ListingsClient Protocol；字段映射完成 |
| P6-18 ✅ | SpApiOrdersAdapter 实现：list_orders（Orders API） | MV-M10 | P6-16 | 满足 OrdersClient Protocol；含物流字段 |
| P6-19 ✅ | SpApiAdvertisingAdapter 实现：list_campaigns、list_spend_snapshots（Advertising API via requests） | MV-M10 | P6-16 | 满足 AdvertisingClient Protocol |
| P6-20 ✅ | SpApiInventoryAdapter 实现：get_inventory、list_inventory（Inventories API） | MV-M10 | P6-16 | 满足 InventoryClient Protocol |
| P6-21 ✅ | 凭据管理：Amazon 设置加密存储（AES-256-GCM + DB + API）+ 连接测试 | M05/M06 | P6-16 | 凭据不明文落盘；连接测试按钮 |
| P6-22 ✅ | 降级策略：SP-API 限流/错误时 fallback 到 mock + 告警日志 | MV-M10 | P6-17~20 | FallbackWrapper + 指数退避重试 + data_source="spapi-degraded" 标记 |
| P6-23 ✅ | P6-MS3 验收：AMAZON_DATA_SOURCE=spapi 端到端跑通 research/ads/ops/support 节点 | ALL | P6-16~22 | 真实数据流入；test.ps1 全绿（mock 测试不受影响） |

### P6-MS4 — Shopify 真实数据

| ID | 任务 | 模块 | 依赖 | 验收 |
|----|------|------|------|------|
| P6-24 ✅ | Shopify 工厂切换：get_store_client() 支持 mock/shopify 模式（env SHOPIFY_DATA_SOURCE） | MV-M10 | — | 与 Amazon 模式一致；默认 mock |
| P6-25 ✅ | ShopifyApiAdapter 实现：7 个 Protocol 方法（products/orders/inventory/carts/customers/discounts/metrics） | MV-M10 | P6-24 | 满足 StoreClient Protocol；GraphQL Admin API |
| P6-26 ✅ | Shopify 凭据管理：store_url + access_token 加密存储 + 设置 UI | M05/M06 | P6-25 | 连接测试；scope 验证 |
| P6-27 ✅ | 降级策略：Shopify API 错误时 fallback mock + 告警 | MV-M10 | P6-25 | 与 P6-22 模式一致 |
| P6-28 ✅ | P6-MS4 验收：SHOPIFY_DATA_SOURCE=shopify 端到端跑通 DTC dashboard/content/ops/support | ALL | P6-24~27 | 真实数据流入；test.ps1 全绿 |

### P6-MS5 — 指标真实化与终验

| ID | 任务 | 模块 | 依赖 | 验收 |
|----|------|------|------|------|
| P6-29 ✅ | 真实指标聚合服务：从 UnifiedOrderRecord + AdSpendSnapshot 计算 GMV/ROI/转化率，替换 _generate_mock_snapshots | MV-M09 | P6-MS3/MS4 | dashboard API 返回 data_source="live" 数据 |
| P6-30 ✅ | 分析报告真实化：替换 _build_mock_report + orchestrator _generate_mock_metrics | MV-M09 | P6-29 | analytics API 返回真实聚合 |
| P6-31 ✅ | data_source 标记全量翻转：UnifiedOrderRecord、BusinessMetricsSnapshot、OrderMetricRecord 默认值改为动态 | MV-M10 | P6-29/30 | mock 环境仍为 "mock"；真实环境为 "spapi"/"shopify"/"live" |
| P6-32 | Phase 6 终验：计费全流程 + 双平台真实数据 + 指标看板 + 降级策略 端到端验收 | ALL | P6-01~31 | 验收报告；test.ps1 全绿；覆盖率 ≥ 70% |

---

## 5. 技术决策

### 5.1 支付网关：Stripe

| 考量 | 决策 |
|------|------|
| 为何选 Stripe | 全球覆盖、Checkout/Portal 托管页面减少 PCI 合规负担、Webhook 成熟、Python SDK 官方维护 |
| 替代方案 | Paddle（MoR，税务自动但生态小）、LemonSqueezy（被 Stripe 收购）、自建（合规成本过高） |
| 集成模式 | Stripe Checkout（一次性托管支付页）+ Customer Portal（自助管理）+ Webhook（状态同步）；**不自建支付表单** |
| 币种 | 首期 USD；多币种延后 |
| 试用 | 注册即 free plan（非 trial）；pro/enterprise 通过 Checkout 升级；可选 14 天 trial（Stripe subscription trial_period_days） |

### 5.2 凭据存储

| 考量 | 决策 |
|------|------|
| Amazon SP-API | refresh_token + client_id/secret → AES-256-GCM 加密存 DB（key 从 env/KMS）；access_token 缓存 Redis（TTL=expiry-60s） |
| Shopify | Admin API access_token（custom app）→ 同样加密存储 |
| 不做什么 | 不引入 Vault/外部 KMS（首期）；env var 仅用于加密主密钥 |

### 5.3 降级策略

```
真实 API 调用
  ├─ 成功 → data_source="spapi"/"shopify"/"live"
  ├─ 限流(429) → 指数退避重试 ×3 → 仍失败 → fallback mock + data_source="spapi-degraded" + WARN 日志
  └─ 错误(5xx/网络) → 重试 ×2 → fallback mock + data_source="*-degraded" + ERROR 日志
```

- 降级对上层透明（Protocol 接口不变）
- 仪表盘显示 data_source 标记，运维可感知
- mock fallback 使用缓存的真实数据快照（若有），否则用 fixtures

### 5.4 开源优先

| 组件 | 选型 | 理由 |
|------|------|------|
| Stripe Python SDK | `stripe` (官方) | L1 — 官方维护，直接依赖 |
| SP-API 封装 | `python-amazon-sp-api` (stars 400+) | L2 — 对比 `sp-api-python-sdk`；前者活跃度高、覆盖 Listings/Orders/Advertising |
| Shopify GraphQL | `Shopify/shopify_python_api` (官方) | L1 — 官方 SDK，GraphQL Admin API 支持 |
| 加密存储 | `cryptography` (已在依赖树) | L1 — Fernet/AES-GCM，无需新依赖 |

---

## 6. 风险与前置条件

| 风险 | 影响 | 缓解 |
|------|------|------|
| 用户无 Amazon 卖家号 | P6-MS3 阻塞 | MS3/MS4 可独立于 MS1/MS2；先交付计费，数据迁移待凭据就绪 |
| SP-API 审批周期长（2-4 周） | MS3 延期 | 提前提交申请；开发期间用 sandbox/mock |
| Stripe 账户未开通 | MS1 阻塞 | 用户需提前注册 Stripe + 获取 API key |
| 真实 API 限流影响测试 | CI 不稳定 | CI 始终用 mock；真实 API 测试标记 `@pytest.mark.live` 手动触发 |
| 凭据泄露 | 安全事故 | 加密存储 + 审计日志 + 设置 UI 不回显完整凭据 |

**用户侧前置条件（开工前须确认）：**
1. Stripe 账户已创建，提供 API key + webhook secret + price IDs
2. Amazon 卖家号就绪（或确认 MS3 延后）
3. Shopify 店铺 + custom app access token（或确认 MS4 延后）

---

## 7. 验收硬指标

| 指标 | 目标 |
|------|------|
| 计费闭环 | 注册→升级→Portal 管理→取消 全流程可走通 |
| Webhook 可靠性 | 事件幂等；签名验证；失败重试不丢状态 |
| 真实数据覆盖 | Amazon 4 Protocol + Shopify 7 Protocol 全部实现 |
| 降级透明 | API 不可用时自动 fallback；上层无感知；日志可追溯 |
| 测试 | test.ps1 全绿；覆盖率 ≥ 70%；mock 测试不受真实 API 影响 |
| 安全 | 凭据加密存储；不明文落盘；审计日志记录凭据访问 |

---

## 8. 执行顺序建议

```
P6-MS1 (计费后端) ──► P6-MS2 (计费前端)     ← 不依赖店铺凭据，可立即开工
         │
         └── 并行 ──► P6-MS3 (Amazon)  ──► P6-MS5 (指标真实化)
                      P6-MS4 (Shopify) ──┘       ← 依赖用户提供凭据
```

- **无凭据时**：先完成 MS1+MS2（计费），MS3/MS4/MS5 挂起等待
- **有凭据时**：MS1+MS2 与 MS3+MS4 并行推进

---

## 9. 目录锁定

| 任务范围 | 可改目录 | 禁止 |
|----------|----------|------|
| P6-01~09 (计费后端) | `apps/api/`、`packages/shared/`、`infra/` | `apps/web/`、`apps/orchestrator/` |
| P6-10~15 (计费前端) | `apps/web/` | `apps/api/` 业务逻辑（仅可加 BFF 代理） |
| P6-16~23 (Amazon) | `packages/integrations/`、`apps/orchestrator/`、`apps/api/` | `apps/web/`（除凭据设置 UI） |
| P6-24~28 (Shopify) | `packages/integrations/`、`apps/orchestrator/`、`apps/api/` | `apps/web/`（除凭据设置 UI） |
| P6-29~32 (指标) | `packages/shared/`、`apps/api/`、`apps/orchestrator/` | — |

---

## 10. 批准

| 角色 | 动作 | 日期 |
|------|------|------|
| AI Agent | 输出本计划 DRAFT | 2026-09-14 |
| 用户 | 批准 | 2026-09-14 |

**用户口令：**
- 「批准 Phase 6」→ 状态改为 APPROVED，P6-MS1 解除阻塞
- 「修订 Phase 6」→ 根据反馈调整后再批准
- 「先做计费」→ 仅启动 P6-MS1/MS2，MS3~MS5 挂起
- 「先做数据迁移」→ 仅启动 P6-MS3/MS4（需凭据），计费延后
