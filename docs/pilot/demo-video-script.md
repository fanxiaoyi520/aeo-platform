# MS7 端到端演示视频脚本（约 10 分钟）

> **用途：** 总计划 §1.4「演示完整性」— 录制后链接填入 [`ms7-pilot-report.md`](../reports/ms7-pilot-report.md)  
> **环境：** 生产 Compose 或 dev-up + web dev（画面需清晰展示工作台）

---

## 0. 准备（录前 5 分钟，不入画）

| 项 | 命令 / 检查 |
|----|-------------|
| 启动 | `cd launch-aeo; .\scripts\prod-up.ps1` 或 `dev-up.ps1` + `pnpm dev` |
| 冒烟 | `.\scripts\demo.ps1` |
| 浏览器 | `http://127.0.0.1:3000` |
| API Key | `.env.prod` 中 `AUTH_API_KEY` 已配置 |

---

## 1. 开场 — 项目与目标（0:00 – 1:00）

**画面：** 工作台首页或 README 架构图

**旁白要点：**

- Launch AEO：元征汽摩配跨境 Listing 自主运营 Agent
- 本期范围：调研 → 规则 → 生成 → 合规 → 人工审核 → 导出
- 本次演示：单 SKU 端到端 + 批跑指标入口

---

## 2. 生产环境与健康检查（1:00 – 2:00）

**画面：** 终端运行 `demo.ps1` 输出；浏览器打开 `/settings` 或 API `/health`

**操作：**

1. 展示 `demo.ps1` 五项检查全绿  
2. 打开 `http://127.0.0.1:8000/docs`，指出认证与审计 API  

---

## 3. 创建任务 — Web 工作台（2:00 – 4:30）

**画面：** `/tasks/new`

**操作：**

1. SKU：`X431-PRO`  
2. 平台：Amazon US  
3. 竞品 ASIN：`B07JFSRMBH`（可填一个）  
4. 关键词：`obd2 scanner`, `launch x431`  
5. 提交 → 跳转任务详情  

**画面：** `/tasks/{id}` Trace 时间线（SSE 实时事件）

**旁白：** 说明 research / rules / generate / compliance / review 各 Agent 节点

---

## 4. HITL 人工审核（4:30 – 6:30）

**画面：** `/tasks/{id}/review`

**操作：**

1. 展示 AI 生成标题与五点描述  
2. 微调标题（可选）→ **批准**  
3. 回到详情确认状态 `completed`  

**旁白：** 人机协同 — 合规与业务最终由人确认

---

## 5. 结果导出（6:30 – 7:30）

**画面：** `/tasks/{id}/result`

**操作：**

1. **复制到剪贴板** — 展示 Seller Central 粘贴格式  
2. 下载 **JSON** 与 **CSV**  

---

## 6. 批跑与试点指标（7:30 – 9:00）

**画面：** 终端

**操作：**

```powershell
cd launch-aeo
.\scripts\batch_pilot.ps1 --auto-approve --limit 3
type pilot\reports\batch-*.summary.json
.\scripts\generate_pilot_report.ps1 --summary pilot\reports\batch-xxx.summary.json --csv pilot\reports\batch-xxx.csv
```

**旁白：** 20 SKU 测试集、一次通过率、p95 耗时、采纳率 — 对齐招聘 JD 商业指标

---

## 7. 收尾 — 安全与部署（9:00 – 10:00）

**画面：** `docs/DEPLOYMENT.md` 或 `backup.ps1` 执行片段

**要点：**

- API Key 认证、限流、CORS、日志脱敏  
- `backup.sh` 数据可恢复  
- 下一步：MS7 试点报告与里程碑验收  

**结束语：** Launch AEO 已具备生产级 Listing 优化闭环，感谢观看。

---

## 录制检查清单

- [ ] 分辨率 ≥ 1080p，字体放大便于阅读  
- [ ] 全程无敏感 Key / 密码入镜  
- [ ] Trace SSE 至少可见 3 个 Agent 事件  
- [ ] HITL 批准前后状态一致  
- [ ] 批跑 summary.json 指标清晰可见  
- [ ] 总时长 8–12 分钟  
