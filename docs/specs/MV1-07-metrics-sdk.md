# 任务 Spec — MV1-07

**任务：** GMV/ROI 指标采集 SDK 初版（mock 数据路径）

**级别：** L2（新 SDK 包能力）— 须开源调研

## 开源调研（L2）

| 方案 | 类型 | 优点 | 缺点 | 许可 | 决策 |
|------|------|------|------|------|------|
| **A. prometheus_client**（已依赖） | 依赖 + 薄封装 | 项目已有 `GET /metrics`；标准 Counter/Gauge；零新依赖 | 不负责 T+1 聚合，仅暴露时序点 | Apache-2.0 | **采纳（导出层）** |
| **B. pandas** | 依赖 | 日聚合、分组强 | 过重；shared 包不宜为简单 GMV/ROI 引入 | BSD | 拒绝 |
| **C. OpenEC** | 外部平台 | 电商分析插件全 | 超出 MV1 范围；非 SDK 形态；架构不匹配 | Apache-2.0 | 拒绝 |
| **D. 自研 `metrics_sdk`** | 自研 | 贴合 MV1-06 表结构；mock 友好；Decimal 精度 | 需自写聚合逻辑 | — | **采纳（核心层）** |

**采纳决策：** **D（核心）+ A（Prometheus 薄封装）**

- 核心：`aeo_shared.metrics_sdk` — 从 order/ad spend 记录计算 GMV、ROI、日快照
- 导出：`aeo_shared.metrics_prometheus` — 将快照写入已有 `prometheus_client` Gauge（不新增依赖）
- 不引入 pandas / 商业 SDK

**做什么：**
- `compute_gmv()` / `compute_roi()` / `build_daily_snapshot()` 
- `OrderMetricRecord` / `AdSpendMetricRecord` 输入模型（与 MV1-06 字段对齐）
- Prometheus `aeo_biz_*` Gauge 注册与 `publish_snapshot()`
- 单元测试 ≥ 8

**不做什么：**
- 不改 DB schema（MV1-06 已有）
- 不做真实 SP-API ingest
- 不做前端看板（MV4-06）
- 不引入新 pip 依赖

**TDD：** RED → GREEN → REFACTOR

**验收：**
1. mock 订单 + 广告花费 → 快照 GMV/ROI 可复现
2. `test.ps1` 全绿
3. Spec 本文件入库

**分支：** `feat/mv1-07-metrics-sdk`
