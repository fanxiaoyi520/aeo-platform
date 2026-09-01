# 任务 Spec — P1-03

> **任务 ID：** P1-03 / MV0-02  
> **类型：** 管理门禁 + 技术可行性确认（**非编码任务**，除非 GO 后接真 SP-API）  
> **状态：** `completed` — **NO-GO**（2026-09-01，用户确认暂无卖家号；MV1 走 mock 路径）  
> **依赖：** MS7 ✅、P1-SPAPI-MOCK ✅、P1-SPAPI-ORCH ✅  
> **关联：** [`10_MANAGER_VISION_PROGRESS.md`](../10_MANAGER_VISION_PROGRESS.md) MV0-02

---

## 任务

确认 Amazon SP-API / 试点店数据接入是否 **GO**，解除 MV1 业务编码门禁。

---

## 背景

| 已完成 | 说明 |
|--------|------|
| P1-SPAPI-MOCK | `aeo-integrations` 包，mock 固定数据 |
| P1-SPAPI-ORCH | `research_agent` 自动加载 mock listing 到 `product_info` |
| 默认模式 | `AMAZON_DATA_SOURCE=mock`，无需卖家号即可开发/测试 |

**缺口：** 真店 OAuth、token 刷新、限流、真实 Listing/Orders 读取 — 须 P1-03 GO 后实现 `spapi_adapter.py`。

---

## 做什么

### A. 管理确认（用户填写）

请逐项确认并打勾：

| # | 检查项 | 确认（Y/N） | 备注 |
|---|--------|-------------|------|
| 1 | 已有 **Amazon Professional** 卖家账号 | | |
| 2 | 已注册 **SP-API Developer** 应用 | | |
| 3 | 可获得 **LWA Client ID + Client Secret** | | |
| 4 | 已完成卖家 **Authorize** 并拿到 **Refresh Token** | | |
| 5 | 试点店为 **真实店铺**（非仅沙箱） | | |
| 6 | 明确首期 API 范围（见下表） | | |

**首期 API 范围（勾选需要的）：**

| API | 用途 | 首期需要 |
|-----|------|----------|
| Listings Items | 读/写 Listing | ☐ |
| Orders | 订单只读 | ☐ |
| Catalog Items | 竞品/目录 | ☐ |
| Reports | 广告/库存报表 | ☐ |
| Feeds | 批量上架 | ☐ |

### B. 技术冒烟（GO 后由 Agent 执行）

GO 后下一任务 **P1-SPAPI-REAL**（L2）验收标准：

1. `AMAZON_DATA_SOURCE=spapi` + 有效 token → `get_listing(pilot_sku)` 返回真数据
2. OAuth token 自动刷新，过期前无人工干预
3. 限流/429 有退避重试
4. CI 仍用 mock，不依赖外网
5. `test.ps1` 全绿

### C. 端到端演示（mock 模式，**现在即可跑**）

见 `aeo-platform/scripts/demo_spapi_mock.ps1`：

```powershell
cd aeo-platform
.\scripts\demo_spapi_mock.ps1
```

完整 Listing 生成（需 LLM + Docker 可选）：

```powershell
# 仅 research  enrichment（无 LLM）
$env:AMAZON_DATA_SOURCE = "mock"
uv run python -c "..."  # 见 demo 脚本 Step 2

# 全流程 CLI（需 .env 中 LLM_* 配置）
uv run aeo-orchestrate run --sku HOMEBREW-KETTLE-1L `
  --competitor B07TZ5YHJZ --competitor B08C7KG5LP `
  --auto-approve
```

---

## 不做什么

- 不在 P1-03 内实现完整 SP-API 客户端（属 GO 后 **P1-SPAPI-REAL**）
- 不申请 TikTok Shop API（另开任务）
- 不做广告 API 写操作（MV3 范围）
- 不将 refresh_token 提交到 Git

---

## 决策矩阵

| 结果 | 条件 | 下一步 |
|------|------|--------|
| **GO** | 检查项 1–4 均为 Y，API 范围已勾选 | 用户回复「P1-03 GO」→ 出 **P1-SPAPI-REAL** Spec → 实现 `spapi_adapter` |
| **PARTIAL** | 有开发者账号但无卖家授权 | 继续 mock；并行 MV1 其他模块 |
| **NO-GO** | 无卖家号 / 6 个月内无法拿到 | 维持 mock；MV1 编码用 pilot 数据验收 |

---

## 开源调研（L2，GO 后编码用）

| 项目 | Stars | License | 可借鉴点 | 采纳决策 |
|------|-------|---------|----------|----------|
| [python-amazon-sp-api](https://github.com/saleweaver/python-amazon-sp-api) | ~1k+ | MIT | OAuth、Listings/Orders 封装 | **薄封装**（首选） |
| [amzn-sp-api](https://github.com/amzn/selling-partner-api-models) | 官方 | Apache-2.0 | OpenAPI 模型、字段对齐 | 参考 |
| 自研 httpx | — | — | 完全可控 | 仅当库不满足限流/多区域时 |

**已有 mock 骨架：** `packages/integrations` — GO 后只换 adapter，不改 orchestrator。

---

## TDD

P1-03 本身为确认任务，**跳过 TDD**。  
GO 后 **P1-SPAPI-REAL** 按 RED → GREEN，mock 测试保持绿。

---

## 验收标准（P1-03 关闭）

1. 用户填写上方确认表（可贴在本 Issue/对话）
2. 管理岗记录决策：**GO / PARTIAL / NO-GO**
3. `02_PROGRESS.md` 中 P1-03 → `completed`
4. 若 GO：`10_MANAGER_VISION_PROGRESS.md` MV0-02 → `completed`，MV1 解除 blocked

---

## 用户口令

| 说 | 效果 |
|----|------|
| **P1-03 GO** | 确认可行 → 出 P1-SPAPI-REAL Spec |
| **P1-03 NO-GO** | 维持 mock，更新进度表 |
| **跑 mock 演示** | 执行 `demo_spapi_mock.ps1` |

---

## 决策记录

| 日期 | 决策 | 说明 |
|------|------|------|
| 2026-09-01 | **NO-GO** | 用户确认暂无 Amazon 卖家号；维持 `AMAZON_DATA_SOURCE=mock`；MV1 其他模块可开工 |

**后续触发：** 获得卖家号 + SP-API 授权后，新开 **P1-SPAPI-REAL** 任务（不重新开 P1-03）。

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-09-01 | 初版 Spec；mock 骨架 + orchestrator 已就绪 |
| 2026-09-01 | 用户决策 **NO-GO**；P1-03 关闭 |
