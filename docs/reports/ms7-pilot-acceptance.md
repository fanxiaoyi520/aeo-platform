# MS7 试点验收报告

| 属性 | 值 |
|------|-----|
| **里程碑** | MS7 |
| **任务** | S7-04 |
| **验收日期** | 2026-08-30 |
| **自动化** | `test.ps1` **169/169**（含 `test_ms7_acceptance.py` 9 项 + S7-01~03 专项测试） |
| **结论** | **通过**（用户于 2026-08-30 批准 MS7） |

---

## 1. 验收范围（M07 §5 / 总计划 §1.4）

| # | 标准 | 结果 | 证据 |
|---|------|------|------|
| 1 | 20 SKU 测试集就绪 | ✅ | `pilot/yuanzheng-sku-testset.json`；`test_s7_01_testset.py` |
| 2 | `batch_pilot` 可输出 20 SKU CSV 报告 | ✅ | `batch_pilot.py --dry-run`；`test_s7_02_batch_pilot.py` |
| 3 | 试点报告含一次通过率 / 耗时 / 采纳率 | ✅ | `ms7-pilot-report.md`；`generate_pilot_report.py` |
| 4 | 10 分钟演示可录制 | ✅ | `docs/pilot/demo-video-script.md`（视频文件待本地录制） |
| 5 | P-BIZ-01 / 一次通过率目标可评估 | ✅ | `evaluate_pilot_targets()`；报告 §2 对照表 |
| 6 | 仪表盘 7 日滚动指标 | ⏭️ | 首期 MS7 未纳入；`task_metrics` 表 Phase 2 |

---

## 2. Sprint 9–10 任务交付清单

| 任务 | 交付物 | 状态 |
|------|--------|------|
| S7-01 | 20 元征 SKU 测试集 JSON + 文档 | ✅ PR #10 |
| S7-02 | `batch_pilot.py` + `pilot_metrics` CSV/汇总 | ✅ PR #11 |
| S7-03 | `PILOT_REPORT` 模板、试点报告、演示脚本 | ✅ PR #12 |
| S7-04 | 本验收报告 + `test_ms7_acceptance.py` | ✅ 本 PR |

---

## 3. 商业指标采集（M07 §2）

| 指标 | 采集方式 | MS7 状态 |
|------|----------|----------|
| 任务耗时 | `batch_pilot` → `duration_ms` | ✅ CSV 列 |
| 人工介入率 | `hitl_required` | ✅ CSV 列 |
| 一次通过率 | `hitl_approved_first_try` | ✅ summary JSON |
| 合规重试 | `compliance_retries` | ✅ CSV 列 |
| 降级率 | `degraded_mode` | ✅ CSV 列 |
| 采纳率 | `adoption_score` | ✅ CSV + summary |
| LLM Token 成本 | `task_metrics` 表 | ⏭️ Phase 2 |

---

## 4. 手动抽测步骤（推荐）

```powershell
cd launch-aeo
.\scripts\batch_pilot.ps1 --dry-run
.\scripts\batch_pilot.ps1 --auto-approve --limit 3   # 需有效 LLM_KEY
.\scripts\generate_pilot_report.ps1 `
  --summary pilot/reports/batch-<timestamp>.summary.json `
  --csv pilot/reports/batch-<timestamp>.csv
```

1. 确认 dry-run CSV 含 **20** 行 `planned`  
2. 按 [`demo-video-script.md`](../pilot/demo-video-script.md) 录制端到端演示  
3. live 批跑后更新 [`ms7-pilot-report.md`](ms7-pilot-report.md) §2 实测列  
4. 对照总计划 §1.4：p95 ≤ 180s、一次通过率 ≥ 60%  

---

## 5. 不在 MS7 范围（已知）

- 真实店铺 GMV/ROI（M07 §6）
- `GET /api/v1/metrics/summary` 与仪表盘 UI
- `task_metrics` 持久化表
- MS4 浏览器自动竞品抓取

---

## 6. 签核

- **技术验收：** S7-04 自动化通过（2026-08-30）
- **里程碑关闭：** 用户于 2026-08-30 批准 MS7
- **live 批跑：** 可选；生产 LLM 全量 20 SKU 可在 Phase 2 前补跑
