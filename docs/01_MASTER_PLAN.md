# AEO Platform — 总计划（Master Plan）

| 属性 | 值 |
|------|-----|
| **项目代号** | AEO Platform |
| **版本** | v1.1.0 |
| **计划状态** | `APPROVED` — 用户于 2026-08-29 批准开工 |
| **制定日期** | 2026-08-29 |
| **最近修订** | 2026-08-29 — 补充统一开发环境、架构、性能规范 |
| **目标** | **生产商业级** AI 电商自主运营系统，支持多品类跨境 Listing 生成、校验与人工审核；以真实 SKU 试点、可度量 ROI 为验收 |
| **首期业务场景** | 通用跨境 Listing 全链路优化（Amazon 为主，TikTok 为辅；示例品类：消费电子、家居、美妆等） |

---

## 1. 项目愿景与边界

### 1.1 愿景

构建一套 **可本地部署、人机协同、可度量 ROI** 的多 Agent 电商运营系统，实现：

> 市场调研 → 智能选品辅助 → Listing 优化 → 内容 AIGC → 投流建议 → 客服/知识应答 → 数据复盘

首期聚焦 **Listing 优化全链路** 达到生产可用，其余模块预留接口、分阶段接入。

### 1.2 范围内（In Scope）

- 多 Agent 编排（LangGraph）与状态持久化
- RAG 知识库（平台规则、产品资料、运营 SOP）
- 浏览器自动化（竞品调研、后台只读/半自动操作）
- 运营工作台（React/Next.js）：任务提交、Agent Trace、HITL 审核
- 本地部署（Docker Compose）、数据不出域
- 商业化指标埋点：耗时、采纳率、人工介入率

### 1.3 范围外（Out of Scope）— 首期不做

- 全自动开户、全自动大规模投流（仅建议 + 人工确认）
- 多租户 SaaS 计费系统
- 模型微调（LoRA/QLoRA）— 列为 Phase 3 可选
- 国内天猫/京东全自动改价（风控高，Phase 2 评估）
- 直接对接公司内部未授权的生产店铺 API

### 1.4 成功标准（首期上线）

| 指标 | 目标 |
|------|------|
| Listing 生成端到端耗时 | p95 ≤ **180s**（含竞品调研），见 `05_PERFORMANCE_STANDARDS` P-BIZ-01 |
| 人工审核一次通过率 | ≥ 60%（试点 20 个 SKU 后统计） |
| 系统可用性 | 月度 ≥ **99.5%**（P-AVL-01），核心 API 健康检查通过 |
| API 读操作延迟 | p95 ≤ **200ms**（P-API-01） |
| 生产验收可追溯 | 20 SKU 试点报告 + 运营可复现的端到端操作记录（`test.ps1`、批跑 CSV、审计日志） |

---

## 2. 系统架构

### 2.1 逻辑架构

```
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend — 运营工作台 (Next.js)                  │
│   任务管理 │ Agent 实时 Trace │ HITL 审核 │ 指标看板 │ 知识库管理    │
└─────────────────────────────┬────────────────────────────────────┘
                              │ REST / SSE
┌─────────────────────────────▼────────────────────────────────────┐
│                    API Gateway — FastAPI                          │
│   认证 │ 限流 │ 任务 CRUD │ Webhook │ OpenAPI                     │
└─────────────────────────────┬────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│              Orchestrator — LangGraph 编排引擎                       │
│   状态图 │ 检查点持久化 │ 重试/熔断 │ HITL 中断/恢复                  │
└──┬──────────┬──────────┬──────────┬──────────┬──────────────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
 Research   Rules     Generate   Compliance  Review
 Agent      Agent     Agent      Agent       Agent
   │          │          │          │          │
   └──────────┴──────────┴────┬─────┴──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   RAG Service          Tool Service           Browser Service
   (Chroma)            (Function Call)        (Playwright)
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                     ▼                     ▼
   PostgreSQL            Redis                  本地文件存储
   (任务/审计)           (队列/缓存)              (文档/截图)
```

### 2.2 技术栈（锁定，变更需 CR）

> **完整版本号、工具链、端口、环境变量命名见 [`03_DEV_ENVIRONMENT.md`](03_DEV_ENVIRONMENT.md)**

| 层级 | 选型 | 锁定版本 |
|------|------|----------|
| 语言 | Python / TypeScript | `3.11.9` / `5.6.x` |
| 包管理 | uv（Python）/ pnpm（Node） | `0.4.18` / `9.12.0` |
| 后端框架 | FastAPI | latest stable（uv lock 锁定） |
| Agent 编排 | LangGraph + LangChain | latest stable（uv lock 锁定） |
| 向量库 | Chroma（本地持久化） | embedded |
| 关系库 | PostgreSQL | `16.4` |
| 缓存/队列 | Redis | `7.4` |
| 浏览器自动化 | Playwright (Python) | `1.48.0`，chromium only |
| 前端 | Next.js 14 App Router + Tailwind + shadcn/ui | `14.2.x` |
| 部署 | Docker Compose | 分 dev / prod profile |
| LLM | **可配置适配器**（OpenAI 兼容 / 公司内网网关） | 抽象 `LLMProvider` 接口 |
| 可观测 | structlog + Prometheus metrics（可选 Grafana） | |

### 2.3 统一规范文档（强制，与总计划同级约束）

| 文档 | 内容 |
|------|------|
| [`03_DEV_ENVIRONMENT.md`](03_DEV_ENVIRONMENT.md) | 编程环境、版本锁定、工具链、端口、CI、`.env` 命名 |
| [`04_ARCHITECTURE_STANDARDS.md`](04_ARCHITECTURE_STANDARDS.md) | 分层架构、包职责、API 契约、数据模型、Agent 规范 |
| [`05_PERFORMANCE_STANDARDS.md`](05_PERFORMANCE_STANDARDS.md) | SLA、超时、并发配额、压测、监控阈值 |

**所有模块开发与 Code Review 必须遵守上述三份规范；冲突时以总计划为准，细则以对应规范文档为准。**

### 2.4 目录结构（规划）

```
aeo-platform/
├── apps/
│   ├── api/                 # FastAPI 主服务
│   ├── orchestrator/        # LangGraph 图与 Agent 定义
│   ├── browser/             # Playwright 服务
│   └── web/                 # Next.js 前端
├── packages/
│   ├── shared/              # 共享类型、工具
│   └── llm/                 # LLM 适配器
├── infra/
│   ├── docker/              # Dockerfile
│   └── compose/             # docker-compose.yml
├── knowledge/               # RAG 源文档（git 可跟踪的公开资料）
├── tests/
├── docs/                    # 项目文档（本计划所在处）
└── scripts/                 # 初始化、迁移脚本
```

---

## 3. 模块划分

| 模块 ID | 名称 | 优先级 | 详细计划 |
|---------|------|--------|----------|
| M01 | 基础设施与工程化 | P0 | [M01-infrastructure.md](modules/M01-infrastructure.md) |
| M02 | RAG 知识库 | P0 | [M02-rag-knowledge.md](modules/M02-rag-knowledge.md) |
| M03 | Agent 编排引擎 | P0 | [M03-agent-orchestration.md](modules/M03-agent-orchestration.md) |
| M04 | 浏览器自动化 | P1 | [M04-browser-automation.md](modules/M04-browser-automation.md) |
| M05 | 运营工作台 | P0 | [M05-frontend-workbench.md](modules/M05-frontend-workbench.md) |
| M06 | 部署与安全 | P0 | [M06-deployment-security.md](modules/M06-deployment-security.md) |
| M07 | 可观测与商业指标 | P1 | [M07-observability-metrics.md](modules/M07-observability-metrics.md) |

**依赖关系：** M01 → M02、M03 → M04、M05；M06 贯穿；M07 在 M03/M05 之后。

---

## 4. 里程碑与进度总表

> 自用户批准总计划之日起计算。详细周任务见 `02_PROGRESS.md`。

| 里程碑 | 名称 | 目标周 | 交付物 | 验收 |
|--------|------|--------|--------|------|
| **MS0** | 计划批准 | W0 | 本总计划 `APPROVED` | 用户签字/回复批准 |
| **MS1** | 工程底座 | W1–W2 | Monorepo、CI、DB、LLM 适配器、健康检查 | `docker compose up` 全绿 |
| **MS2** | RAG 可用 | W3 | 知识库 ingest + 检索 API + 管理界面 | 规则问答准确率人工抽检 ≥ 80% |
| **MS3** | Agent 核心 | W4–W6 | 5 Agent 图跑通、HITL、状态持久化 | CLI + API 端到端生产验收 |
| **MS4** | 浏览器调研 | W7 | Playwright 竞品抓取接入 Research Agent | 稳定抓取 3 个 ASIN |
| **MS5** | 运营工作台 | W8–W9 | 完整 UI：任务、Trace、审核、导出 | 运营人员可独立操作 |
| **MS6** | 生产加固 | W10 | 安全审计、测试、prod compose、文档 | 测试通过、prod 冒烟验收 |
| **MS7** | 试点验收 | W11–W12 | 20 个通用 SKU 试点报告 | 成功标准 1.4 达标 |

**总工期：12 周（3 个月）** — 按每周 15–20 小时投入估算；全职可压缩至 6–8 周。

---

## 5. Agent 拓扑（首期锁定）

```
START
  → research_agent      # 竞品/关键词调研（Playwright + 搜索）
  → rules_agent         # RAG 检索平台规则与产品资料
  → generate_agent      # 生成 Title / Bullets / Search Terms
  → compliance_agent    # 字数、禁用词、格式校验
  → [HITL 人工审核]      # 中断，等待前端 approve/reject
  → review_agent        # 汇总、版本存档、指标记录
END
```

**失败策略：**
- `research_agent` 失败 → 降级为「仅 RAG + 用户输入竞品信息」，记录 `degraded_mode`
- `compliance_agent` 不通过 → 自动回流 `generate_agent`，最多 3 次
- 3 次仍失败 → 转 HITL 并标记 `needs_manual`

---

## 6. 数据与安全

| 原则 | 实现 |
|------|------|
| 数据本地化 | 所有向量、任务、截图存本地卷，默认禁用外发 |
| 密钥管理 | `.env` + Docker secrets，不入 Git |
| 日志脱敏 | 价格、供应商、API Key 打码 |
| 审计 | 所有 HITL 操作写入 `audit_log` 表 |
| LLM 调用 | 通过 `LLMProvider`，支持切换内网/公网，调用可审计 |

---

## 7. 风险登记

| ID | 风险 | 概率 | 影响 | 缓解 |
|----|------|------|------|------|
| R1 | 平台反爬导致 Playwright 不稳定 | 高 | 中 | 降级模式 + 缓存 + 请求频率限制 |
| R2 | LLM 生成不合规 Listing | 中 | 高 | compliance_agent + HITL 强制 |
| R3 | 工期超出 12 周 | 中 | 中 | 严格首期范围，M04/M07 可延后 |
| R4 | 公司内网 LLM 接口不兼容 | 中 | 中 | LLMProvider 抽象，开发期可用公网 |
| R5 | 用户使用未授权内部数据 | 低 | 高 | 治理规则 + 仅用公开产品资料 |

---

## 8. 审核清单（请用户逐项确认）

- [ ] 项目范围（首期 Listing 优化，不含全自动投流）
- [ ] 技术栈（FastAPI + LangGraph + Next.js + Playwright + PostgreSQL + Chroma）
- [ ] 统一规范（开发环境 `03` / 架构 `04` / 性能 `05`）
- [ ] 12 周里程碑
- [ ] 7 个模块划分
- [ ] Agent 五节点 + HITL 拓扑
- [ ] 首期平台：Amazon 主、TikTok 辅
- [ ] 数据本地、不出域原则

---

## 9. 修订记录

| 版本 | 日期 | 变更 | 审批人 |
|------|------|------|--------|
| v1.0.0 | 2026-08-29 | 初稿 | 待用户审批 |
| v1.1.0 | 2026-08-29 | 新增统一开发环境、架构、性能规范三份文档 | 待用户审批 |
