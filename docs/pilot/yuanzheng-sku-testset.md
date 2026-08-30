# 元征 SKU 试点测试集（S7-01）

| 属性 | 值 |
|------|-----|
| **任务** | S7-01 |
| **里程碑** | MS7 |
| **数量** | 20 SKU |
| **机器可读** | [`launch-aeo/pilot/yuanzheng-sku-testset.json`](../../launch-aeo/pilot/yuanzheng-sku-testset.json) |
| **创建日期** | 2026-08-30 |

---

## 1. 选型原则

对齐总计划 §1.4（20 SKU 试点）与 M07 批跑需求：

1. **业务真实性** — 元征 LAUNCH 公开在售诊断仪/汽摩配 SKU，Amazon US 为主
2. **产品线覆盖** — X431 / CRP / Creader / 专用工具（电瓶、TPMS、重卡）
3. **平台分布** — Amazon 16 项 + TikTok 4 项（验证双平台 generate 模板）
4. **路径覆盖** — 14 项含竞品 ASIN；6 项无竞品（测试 research 降级）
5. **RAG 映射** — 5 项映射 `knowledge/products/launch-x431.md`；其余依赖平台规则 + 关键词

---

## 2. SKU 清单

| ID | SKU | 产品名 | 平台 | 产品线 | 竞品 ASIN | 降级路径 |
|----|-----|--------|------|--------|-----------|----------|
| YZ-001 | X431-PRO | LAUNCH X431 PRO | amazon | X431 | 2 | — |
| YZ-002 | X431-PRO3 | LAUNCH X431 PRO3 | amazon | X431 | 2 | — |
| YZ-003 | X431-PRO5 | LAUNCH X431 PRO5 | amazon | X431 | 2 | — |
| YZ-004 | X431-PAD7 | LAUNCH X431 PAD VII | amazon | X431 | 2 | — |
| YZ-005 | X431-V-PLUS | LAUNCH X431 V+ | amazon | X431 | 1 | — |
| YZ-006 | CRP129E | LAUNCH CRP129E | amazon | CRP | 2 | — |
| YZ-007 | CRP919E | LAUNCH CRP919E | amazon | CRP | 1 | — |
| YZ-008 | CRP123E | LAUNCH CRP123E | amazon | CRP | 1 | — |
| YZ-009 | CREADER-3001 | LAUNCH Creader 3001 | amazon | Creader | 1 | — |
| YZ-010 | CREADER-601 | LAUNCH Creader 601 | amazon | Creader | 1 | — |
| YZ-011 | CREADER-VII-PLUS | LAUNCH Creader VII+ | amazon | Creader | 1 | — |
| YZ-012 | CR919 | LAUNCH CR919 | amazon | CR | 1 | — |
| YZ-013 | MD808-PRO | LAUNCH MD808 Pro | amazon | MD | 1 | — |
| YZ-014 | X431-HDIII | LAUNCH X431 HDIII | amazon | X431 | 0 | ✅ |
| YZ-015 | BST-360 | LAUNCH BST-360 | amazon | BST | 1 | — |
| YZ-016 | CRT5011X | LAUNCH CRT5011X | amazon | CRT | 0 | ✅ |
| YZ-017 | X431-PRO-TK | LAUNCH X431 PRO | tiktok | X431 | 0 | ✅ |
| YZ-018 | CRP129E-TK | LAUNCH CRP129E | tiktok | CRP | 0 | ✅ |
| YZ-019 | CREADER-3001-TK | LAUNCH Creader 3001 | tiktok | Creader | 0 | ✅ |
| YZ-020 | BST-360-TK | LAUNCH BST-360 | tiktok | BST | 0 | ✅ |

---

## 3. 与下游任务衔接

| 任务 | 用法 |
|------|------|
| **S7-02** | `scripts/batch_pilot.py --auto-approve` 读取本 JSON，输出 `pilot/reports/batch-*.csv` |
| **S7-03** | 试点报告引用本清单，统计一次通过率 / 耗时 |
| **S7-04** | MS7 验收对照总计划 §1.4 成功标准 |

### 创建单条任务示例（API）

```json
{
  "sku": "X431-PRO",
  "platform": "amazon",
  "market": "US",
  "product_info": {
    "competitor_asins": ["B07JFSRMBH", "B0892SKJYK"],
    "keywords": ["obd2 scanner", "launch x431", "car diagnostic tool"]
  }
}
```

### 批跑示例（S7-02）

```powershell
cd launch-aeo
.\scripts\batch_pilot.ps1 --dry-run          # 校验测试集，输出 planned CSV
.\scripts\batch_pilot.ps1 --auto-approve   # 全量 20 SKU 批跑 + 指标 CSV
.\scripts\batch_pilot.ps1 --auto-approve --limit 3
```

输出：`pilot/reports/batch-<timestamp>.csv` + `.summary.json`

---

## 4. 不在 S7-01 范围

- 批量跑批与指标采集（S7-02）
- 补充 15 个 SKU 的独立 RAG 产品文档（可后续增量 ingest）
- 真实店铺 GMV/ROI 数据

---

## 5. 签核

- **交付：** 20 SKU JSON + 本文档（2026-08-30）
- **自动化：** `test_s7_01_testset.py`
