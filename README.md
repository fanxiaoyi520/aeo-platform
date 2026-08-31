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
| Phase 2（MV1–MV5） | **blocked**（待 MV0-02 SP-API） |
| 代码目录 | `aeo-platform/` |

## 参与贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md) — 分支命名、Lane 目录锁定、PR 与验收要求。

## AI Agent 必读

**任何 AI / Agent 开始工作前，必须先阅读：**

1. [AGENTS.md](AGENTS.md)
2. [docs/00_GOVERNANCE.md](docs/00_GOVERNANCE.md)
3. [docs/01_MASTER_PLAN.md](docs/01_MASTER_PLAN.md)
4. [docs/02_PROGRESS.md](docs/02_PROGRESS.md)

## 文档索引

| 文档 | 说明 |
|------|------|
| [总计划](docs/01_MASTER_PLAN.md) | 范围、架构、里程碑（锁定） |
| [治理规则](docs/00_GOVERNANCE.md) | 变更控制、AI 工作协议 |
| [开发环境规范](docs/03_DEV_ENVIRONMENT.md) | 版本锁定、工具链、端口、CI（锁定） |
| [架构规范](docs/04_ARCHITECTURE_STANDARDS.md) | 分层、API 契约、数据模型、Agent 规范（锁定） |
| [性能规范](docs/05_PERFORMANCE_STANDARDS.md) | SLA、超时、并发、压测（锁定） |
| [进度表](docs/02_PROGRESS.md) | Sprint 任务与状态 |
| [任务 Spec 模板](docs/06_TASK_SPEC.md) | 开工前 Spec + PR 流程 + 口令 |
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
