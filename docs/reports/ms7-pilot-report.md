# MS7 元征 SKU 试点报告

| 属性 | 值 |
|------|-----|
| **生成时间** | 2026-08-30 03:23 UTC |
| **测试集** | `launch-aeo\pilot\yuanzheng-sku-testset.json` |
| **批跑 CSV** | `launch-aeo\pilot\reports\ms7-reference.csv` |
| **批跑模式** | dry_run |

## 1. 执行摘要

- 任务总数：**20**
- 完成：**0**；失败：**0**
- HITL 介入率：**0.0%**
- 一次通过率：**0.0%**
- 采纳率：**0.0%**
- 平均耗时：**0 ms**
- p95 耗时：**0 ms**

## 2. 成功标准对照（总计划 §1.4）

| 指标 | 目标 | 实测 | 结果 |
|------|------|------|------|
| P-BIZ-01 端到端耗时 p95 | ≤ 180s | 0.0s | ⏳ 待 live 批跑 |
| 人工审核一次通过率 | ≥ 60% | 0.0% | ⏳ 待 live 批跑 |
| Listing 采纳率 | ≥ 85% 编辑距离 | 0.0% | ⏳ 待 live 批跑 |

## 3. 批跑命令

```powershell
cd launch-aeo
.\scripts\batch_pilot.ps1 --auto-approve
.\scripts\generate_pilot_report.ps1 `
  --summary pilot/reports/batch-<timestamp>.summary.json `
  --csv pilot/reports/batch-<timestamp>.csv
```

## 4. 演示视频

脚本：[`../pilot/demo-video-script.md`](../pilot/demo-video-script.md)

> 视频文件由运营本地录制后归档（本仓库不包含视频二进制）。

## 5. 备注

本报告由 `generate_pilot_report.py` 根据 `batch_pilot` 输出自动生成。
