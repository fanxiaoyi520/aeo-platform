# AEO Platform

**AEO** = **A**utonomous **E**commerce **O**perator（自主电商运营系统）

> 不是 SEO 圈的 Answer Engine Optimization（答引擎优化）。

开源、可自部署的多 Agent 电商运营平台 — 首期聚焦 Listing 生成、合规校验与人工审核（Amazon / TikTok）。

**GitHub:** [github.com/fanxiaoyi520/aeo-platform](https://github.com/fanxiaoyi520/aeo-platform)  
**License:** [MIT](LICENSE)

## 状态

| 文档 | 状态 |
|------|------|
| 总计划 v1.1.0 | **APPROVED** |
| Phase 1（MS0–MS7） | **已完成** |
| Phase 1 扩展 P1-01 | **已完成**（知识库上传，PR #14） |
| Phase 2（MV1–MV5） | **已完成**（mock 路径，MV0-02 NO-GO） |
| Phase 3（DTC 独立站） | **已完成**（P3-01~09，PR #52） |
| Phase 4（生产部署加固） | **已完成**（PR #53） |
| Phase 6（计费与真实数据） | **进行中** — 见 [进度表](docs/02_PROGRESS.md) 与 [Phase 6 计划](docs/11_PHASE6_BILLING_DATA_PLAN.md) |
| 代码目录 | `aeo-platform/` |

## 参与贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md) — 分支命名、Lane 目录锁定、PR 与验收要求。

## AI Agent 必读

**分层阅读**（详见 [AGENTS.md §分层阅读](AGENTS.md)）：

1. [AGENTS.md](AGENTS.md)
2. [docs/02_PROGRESS.md](docs/02_PROGRESS.md)（顶部状态即可）
3. 当前任务 Spec / 模块 / 扩展计划相关节  
   — `00`–`05` 等规范按改动范围按需加载，勿默认全文通读

## 文档索引

按角色导航见 **[docs/README.md](docs/README.md)**。新人上手：[docs/how-to/getting-started.md](docs/how-to/getting-started.md)。

| 文档 | 说明 |
|------|------|
| [总计划](docs/01_MASTER_PLAN.md) | 范围、架构、里程碑（锁定） |
| [治理规则](docs/00_GOVERNANCE.md) | 变更控制、AI 工作协议 |
| [开发环境规范](docs/03_DEV_ENVIRONMENT.md) | 版本锁定、工具链、端口、CI（锁定） |
| [架构规范](docs/04_ARCHITECTURE_STANDARDS.md) | 分层、API 契约、数据模型、Agent 规范（锁定） |
| [性能规范](docs/05_PERFORMANCE_STANDARDS.md) | SLA、超时、并发、压测（锁定） |
| [进度表](docs/02_PROGRESS.md) | Sprint 任务与状态 |
| [任务 Spec 模板](docs/06_TASK_SPEC.md) | 开工前 Spec + PR 流程 + 口令 |
| [ADR 索引](docs/adr/README.md) | 架构决策记录 |
| [L2 Spec 存档](docs/specs/README.md) | 开源调研 Spec |
| [管理岗愿景计划](docs/10_MANAGER_VISION_PLAN.md) | Phase 2 生产扩展 |
| [管理岗愿景进度](docs/10_MANAGER_VISION_PROGRESS.md) | MV 进度 |
| [Phase 6 计费与数据](docs/11_PHASE6_BILLING_DATA_PLAN.md) | Stripe / 真实店铺 API |
| [生产部署](docs/DEPLOYMENT.md) | 生产环境部署 |
| [运维手册](docs/RUNBOOK.md) | 日常巡检与应急 |
| [验收报告](docs/reports/) | MS/MV 验收证据 |
| [贡献指南](CONTRIBUTING.md) | 多人协作、Lane 认领、PR 检查清单 |
| [M01 基础设施](docs/modules/M01-infrastructure.md) | |
| [M02 RAG 知识库](docs/modules/M02-rag-knowledge.md) | |
| [M03 Agent 编排](docs/modules/M03-agent-orchestration.md) | |
| [M04 浏览器自动化](docs/modules/M04-browser-automation.md) | |
| [M05 运营工作台](docs/modules/M05-frontend-workbench.md) | |
| [M06 部署与安全](docs/modules/M06-deployment-security.md) | |
| [M07 可观测与指标](docs/modules/M07-observability-metrics.md) | |

## 用户审批

审核总计划后请回复：

- **「批准总计划」** — 开始 Sprint 1
- **「修改：{意见}」** — 修订后重新提交
- **「驳回」** — 重新规划
