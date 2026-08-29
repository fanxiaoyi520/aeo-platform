# M05 — 运营工作台

| 属性 | 值 |
|------|-----|
| **模块 ID** | M05 |
| **优先级** | P0 |
| **里程碑** | MS5（W8–W9） |
| **状态** | `blocked` |
| **依赖** | M01, M03（M02 知识库页依赖 M02） |

---

## 1. 目标

构建生产级运营工作台，使非开发人员可独立完成 Listing 优化任务的全流程操作。

## 2. 页面规划

| 路由 | 功能 |
|------|------|
| `/` | 仪表盘：今日任务数、通过率、平均耗时 |
| `/tasks` | 任务列表：筛选、状态、创建 |
| `/tasks/new` | 新建任务：SKU、平台、产品信息、可选竞品 ASIN |
| `/tasks/[id]` | 任务详情：Agent Trace 时间线、中间结果 |
| `/tasks/[id]/review` | HITL 审核：对比竞品、编辑、批准/驳回 |
| `/tasks/[id]/result` | 最终结果：一键复制各字段、导出 JSON/CSV |
| `/knowledge` | 知识库文档列表、上传、重建索引 |
| `/settings` | LLM 配置（只读展示）、系统状态 |

## 3. 交付物

- [ ] Next.js 14 App Router 项目（`apps/web/`）
- [ ] UI：Tailwind + shadcn/ui，深色/浅色主题
- [ ] API 客户端：类型安全（openapi-typescript 或 tRPC）
- [ ] SSE 订阅 Agent Trace 实时更新
- [ ] HITL 审核交互：diff 视图、批注
- [ ] 响应式布局（桌面优先，平板可用）

## 4. 交互规范

### 4.1 Agent Trace 展示

```
[09:01:02] research_agent  started
[09:01:45] research_agent  completed — 3 competitors found
[09:01:46] rules_agent      started
...
[09:03:10] ⏸ waiting for human review
```

- 进行中：蓝色脉冲
- 成功：绿色
- 失败/降级：橙色
- 等待人工：黄色

### 4.2 HITL 审核

- 左侧：AI 生成内容（可编辑）
- 右侧：竞品参考、规则提示
- 操作：「批准发布」「驳回并备注」「保存草稿」

## 5. 验收标准

1. 运营人员无需 CLI 可完成一次完整任务
2. Trace 实时更新延迟 < 2s
3. 审核后任务状态与后端一致
4. 导出格式符合 Amazon Seller Central 粘贴习惯
5. Lighthouse 性能分 ≥ 80（桌面）

## 6. 不在本模块范围

- 多用户权限体系（MS6 基础认证即可）
- 移动端 App
