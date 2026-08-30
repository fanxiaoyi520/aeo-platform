# 管理岗愿景 — 进度表（Manager Vision Progress）

> **非当前执行来源。** 在 [`10_MANAGER_VISION_PLAN.md`](10_MANAGER_VISION_PLAN.md) 状态为 `APPROVED` 之前，AI Agent **不得**执行本表任务。  
> **当前唯一执行来源：** [`02_PROGRESS.md`](02_PROGRESS.md)（Launch AEO 首期）

| 属性 | 值 |
|------|-----|
| **计划状态** | `ON_HOLD` — 未开启 |
| **需求来源** | `Desktop/111/` 管理岗 JD |
| **最后更新** | 2026-08-30 |
| **前置条件** | Launch AEO **MS7 完成**（推荐） |
| **整体完成度** | **0%**（0 / 89 任务） |

---

## 总览

| 里程碑 | 状态 | 计划周 | 实际完成日 | 依赖 |
|--------|------|--------|------------|------|
| MV0 计划批准 | `pending` | — | — | 用户决策 |
| MV1 平台与风控底座 | `blocked` | W1–W8 | — | MV0 + Launch MS7 |
| MV2 选品 + 内容扩展 | `blocked` | W9–W18 | — | MV1 |
| MV3 投放与运维 | `blocked` | W19–W30 | — | MV2 |
| MV4 客服 + 复盘 | `blocked` | W31–W40 | — | MV3 |
| MV5 全链路试点 | `blocked` | W41–W48 | — | MV4 |

---

## 模块进度

| 模块 | 名称 | 状态 | 完成度 | 阶段 |
|------|------|------|--------|------|
| MV-M01 | 多 Agent 平台与调度 | `blocked` | 0% | MV1 |
| MV-M02 | 风控与决策分级 | `blocked` | 0% | MV1 |
| MV-M03 | 选品与市场情报 | `blocked` | 0% | MV2 |
| MV-M04 | 内容 AIGC（全媒介） | `blocked` | 0% | MV2 |
| MV-M05 | 广告投放与 ROI | `blocked` | 0% | MV3 |
| MV-M06 | 店铺运维自动化 | `blocked` | 0% | MV3 |
| MV-M07 | 客服与履约 | `blocked` | 0% | MV4 |
| MV-M08 | 独立站 / DTC | `blocked` | 0% | MV3–MV4 |
| MV-M09 | 商业指标与复盘闭环 | `blocked` | 0% | MV1 基础 / MV4 完整 |
| MV-M10 | 数据集成层 | `blocked` | 0% | MV1 起并行 |

---

## Launch AEO 复用映射（已完成 / 进行中）

> MV 开启后可复用，**不计入 MV 完成度**。

| Launch AEO | 状态 | 复用到 MV |
|------------|------|-----------|
| MS1 工程底座 | `completed` | 全部模块 |
| MS2 RAG | `in_progress` | A03/A05 知识库 |
| MS3 Agent 核心 | `completed` | A03 Listing 子链、编排模式 |
| MS4 浏览器 | `pending` | A01 竞品、A04 运维 |
| MS5 工作台 | `in_progress` | 指挥台扩展 |
| MS6 生产加固 | `blocked` | MV 生产基线 |
| MS7 试点 | `blocked` | MV 试点方法论 |

**Launch AEO 对 MV 的贡献度（粗估）：** ~15%（技术地基，非业务全链路）

---

## Sprint 计划

### MV0 — 决策门控

| ID | 任务 | 状态 | 负责人 | 备注 |
|----|------|------|--------|------|
| MV0-01 | 用户审阅 `10_MANAGER_VISION_PLAN.md` | `pending` | 用户 | — |
| MV0-02 | 确认试点平台与数据接入可行性 | `pending` | 用户 | SP-API 等 |
| MV0-03 | 用户回复「批准 MV 计划」或「开启管理岗愿景」 | `pending` | 用户 | 状态 → APPROVED |

### MV1 — 平台与风控底座（+8 周）

| ID | 任务 | 模块 | 状态 | 依赖 |
|----|------|------|------|------|
| MV1-01 | 多 Agent 注册表与能力声明 Schema | MV-M01 | `blocked` | MV0 |
| MV1-02 | 跨 Agent 任务调度器（优先级队列） | MV-M01 | `blocked` | MV1-01 |
| MV1-03 | 多图编排：父任务 → 子 Agent 图 | MV-M01 | `blocked` | MV1-02 |
| MV1-04 | L0/L1/L2 风控规则 DSL 设计 | MV-M02 | `blocked` | MV0 |
| MV1-05 | 风控引擎 + 审计日志扩展 | MV-M02 | `blocked` | MV1-04 |
| MV1-06 | 经营数据表骨架（订单/广告占位） | MV-M10 | `blocked` | MV0 |
| MV1-07 | GMV/ROI 指标采集 SDK 初版 | MV-M09 | `blocked` | MV1-06 |
| MV1-08 | 前端：风控规则配置页（简版） | MV-M02 | `blocked` | MV1-05 |
| MV1-09 | MV1 集成验收：3 Agent 联调 | ALL | `blocked` | MV1-01~08 |

### MV2 — 选品 + 内容扩展（+10 周）

| ID | 任务 | 模块 | 状态 | 依赖 |
|----|------|------|------|------|
| MV2-01 | 选品评分模型与竞品池持久化 | MV-M03 | `blocked` | MV1 |
| MV2-02 | A01 选品 Agent：趋势 + 竞品 + 评分报告 | MV-M03 | `blocked` | MV2-01 |
| MV2-03 | 市场情报定时任务（cron） | MV-M03 | `blocked` | MV2-01 |
| MV2-04 | A03 扩展：主图/场景图文案 | MV-M04 | `blocked` | MV1 |
| MV2-05 | A03 扩展：TikTok 短视频脚本 + 分镜 | MV-M04 | `blocked` | MV2-04 |
| MV2-06 | 多平台内容模板库（Amazon/TikTok） | MV-M04 | `blocked` | MV2-04 |
| MV2-07 | 选品 → 内容 AIGC 自动任务链 | MV-M01 | `blocked` | MV2-02, MV2-05 |
| MV2-08 | MV2 验收：选品报告 + 图文/脚本 demo | ALL | `blocked` | MV2-01~07 |

### MV3 — 投放与运维（+12 周）

| ID | 任务 | 模块 | 状态 | 依赖 |
|----|------|------|------|------|
| MV3-01 | Amazon SP-API 只读接入（广告/库存） | MV-M10 | `blocked` | MV1 |
| MV3-02 | A02 投放 Agent：结构建议 + 出价模拟 | MV-M05 | `blocked` | MV3-01 |
| MV3-03 | 预算分配与 ROI 预估引擎 | MV-M05 | `blocked` | MV3-02 |
| MV3-04 | A04 运维 Agent：调价/库存建议（L1 人审） | MV-M06 | `blocked` | MV3-01 |
| MV3-05 | 浏览器辅助：Seller Central 只读巡检 | MV-M06 | `blocked` | Launch MS4 |
| MV3-06 | Shopify Store API 只读（独立站） | MV-M08 | `blocked` | MV1 |
| MV3-07 | 投放 ↔ 库存联动策略（文档 + 原型） | MV-M05 | `blocked` | MV3-02, MV3-04 |
| MV3-08 | 前端：广告建议 + 审批执行页 | MV-M05 | `blocked` | MV3-02 |
| MV3-09 | MV3 验收：Amazon 广告建议 + 人审改价闭环 | ALL | `blocked` | MV3-01~08 |

### MV4 — 客服 + 复盘（+10 周）

| ID | 任务 | 模块 | 状态 | 依赖 |
|----|------|------|------|------|
| MV4-01 | 订单/物流数据 ingest | MV-M10 | `blocked` | MV3 |
| MV4-02 | A05 客服 Agent：RAG + 订单工具 | MV-M07 | `blocked` | MV4-01 |
| MV4-03 | 售后话术库与升级人工规则 | MV-M07 | `blocked` | MV4-02 |
| MV4-04 | A06 复盘 Agent：日报/周报生成 | MV-M09 | `blocked` | MV1-07 |
| MV4-05 | 策略建议 → 下轮任务自动创建 | MV-M09 | `blocked` | MV4-04, MV1-02 |
| MV4-06 | GMV/ROI/人工替代率看板 | MV-M09 | `blocked` | MV1-07 |
| MV4-07 | 六 Agent 指挥台（前端） | MV-M01 | `blocked` | MV1-03 |
| MV4-08 | MV4 验收：客服应答 + 日报 + 看板 | ALL | `blocked` | MV4-01~07 |

### MV5 — 全链路试点（+8 周）

| ID | 任务 | 模块 | 状态 | 依赖 |
|----|------|------|------|------|
| MV5-01 | 50 SKU 多平台测试集 | — | `blocked` | MV4 |
| MV5-02 | 批跑脚本与指标采集 | MV-M09 | `blocked` | MV5-01 |
| MV5-03 | 人工替代率 / ROI 对比报告 | MV-M09 | `blocked` | MV5-02 |
| MV5-04 | 风控事故复盘与规则调优 | MV-M02 | `blocked` | MV5-02 |
| MV5-05 | 生产部署与 7×24 试运行 | MV-M10 | `blocked` | MV5-03 |
| MV5-06 | MV5 验收：替代率 ≥ 40%、ROI 可对比 | ALL | `blocked` | MV5-01~05 |

---

## 阻塞项

| ID | 描述 | 状态 |
|----|------|------|
| MV-B001 | 用户未批准 MV 计划 | `open` |
| MV-B002 | Launch AEO MS7 未完成 | `open` |
| MV-B003 | SP-API / 店铺数据接入方案未确认 | `open` |

---

## 用户口令

| 说 | 效果 |
|----|------|
| **开启管理岗愿景** / **批准 MV 计划** | MV0 完成，MV1 解除阻塞 |
| **暂停 MV** | 全部任务 `on_hold`，不写 MV 代码 |
| **推进 MV2** | 在 MV1 完成后执行 MV2 任务 |
| **MV 进度** | 读本表汇报 |

---

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-08-30 | 初版：自管理岗 JD 拆解 5 里程碑、89 项任务，状态 ON_HOLD |
