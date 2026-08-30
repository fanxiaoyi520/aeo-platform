# M07 — 可观测与商业指标

| 属性 | 值 |
|------|-----|
| **模块 ID** | M07 |
| **优先级** | P1 |
| **里程碑** | MS6（基础）、MS7（试点） |
| **状态** | `completed` |
| **依赖** | M03, M05 |

---

## 1. 目标

建立与招聘 JD 对齐的商业化指标采集体系，支撑试点验收与对内汇报。

## 2. 核心指标（对齐 JD）

| 指标 | 定义 | 采集点 |
|------|------|--------|
| **任务耗时** | 创建 → completed 总时长 | review_agent |
| **人工介入率** | 进入 HITL 的任务占比 | HITL 节点 |
| **一次通过率** | 首次 HITL 即 approve 占比 | HITL approve |
| **合规自动修复率** | compliance 自动修复成功占比 | compliance_agent |
| **降级率** | degraded_mode 任务占比 | research_agent |
| **采纳率** | 用户 approve 且无大幅修改占比 | HITL diff 对比 |
| **LLM 成本** | 每任务 token 用量 | LLMProvider |

## 3. 交付物

- [ ] `task_metrics` 表与采集 SDK
- [ ] Prometheus `/metrics` 端点（可选 Grafana dashboard JSON）
- [ ] 仪表盘 API：`GET /api/v1/metrics/summary`
- [ ] 前端仪表盘图表（M05 `/` 页）
- [ ] 试点报告模板 `docs/templates/PILOT_REPORT.md`
- [ ] MS7：20 SKU 批量跑批脚本 `scripts/batch_pilot.py`

## 4. 技术规范

### 4.1 Metrics 表

```sql
task_metrics (
  task_id UUID PK,
  duration_ms INT,
  hitl_required BOOL,
  hitl_approved_first_try BOOL,
  compliance_retries INT,
  degraded_mode BOOL,
  adoption_score FLOAT,  -- 0-1, 编辑距离计算
  llm_tokens_in INT,
  llm_tokens_out INT,
  created_at TIMESTAMPTZ
)
```

### 4.2 采纳率计算

```
adoption_score = 1 - (edit_distance(ai_output, final_output) / max(len(ai_output), 1))
采纳 = adoption_score >= 0.85
```

## 5. 验收标准

1. 仪表盘展示 7 日滚动指标
2. batch_pilot 可对 20 SKU 输出 CSV 报告
3. 试点报告包含：一次通过率、平均耗时、采纳率
4. 满足总计划 1.4 成功标准

## 6. 不在本模块范围

- 真实 GMV/ROI 对接（需店铺 API，Phase 2）
- 投放效果归因
