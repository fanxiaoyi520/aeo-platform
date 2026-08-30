# MS7 试点报告模板

> 复制本模板，将 `{占位符}` 替换为 `batch_pilot` + `generate_pilot_report.py` 输出，或手工填写。

---

## 元信息

| 字段 | 值 |
|------|-----|
| **里程碑** | MS7 |
| **测试集** | `{testset_path}` |
| **批跑 CSV** | `{batch_csv_path}` |
| **生成日期** | `{date}` |
| **批跑模式** | `live` / `dry_run` |

---

## 1. 执行摘要

| 指标 | 值 |
|------|-----|
| 任务总数 | {total} |
| 完成 / 失败 | {completed} / {failed} |
| HITL 介入率 | {hitl_rate}% |
| 一次通过率 | {first_pass_rate}% |
| 采纳率 | {adoption_rate}% |
| 平均耗时 | {avg_duration_ms} ms |
| p95 耗时 | {p95_duration_ms} ms |

---

## 2. 成功标准对照（总计划 §1.4）

| 指标 | 目标 | 实测 | 结果 |
|------|------|------|------|
| P-BIZ-01 端到端 p95 | ≤ 180s | {p95_seconds}s | {p95_pass} |
| 人工审核一次通过率 | ≥ 60% | {first_pass_rate}% | {first_pass_pass} |
| Listing 采纳率 | ≥ 85% 编辑距离 | {adoption_rate}% | {adoption_pass} |

---

## 3. SKU 明细（摘自 CSV）

| pilot_id | sku | platform | status | duration_ms | hitl | degraded | adoption |
|----------|-----|----------|--------|-------------|------|----------|----------|
| {rows} |

---

## 4. 演示视频

- **脚本：** `docs/pilot/demo-video-script.md`
- **视频链接：** `{video_url}`（录制后填写）

---

## 5. 结论与后续

- **结论：** {conclusion}
- **后续：** S7-04 MS7 验收 / MS7 里程碑批准

---

## 自动生成

```powershell
cd launch-aeo
.\scripts\batch_pilot.ps1 --auto-approve
.\scripts\generate_pilot_report.ps1 `
  --summary pilot/reports/batch-<timestamp>.summary.json `
  --csv pilot/reports/batch-<timestamp>.csv
```
