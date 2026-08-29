# M04 — 浏览器自动化

| 属性 | 值 |
|------|-----|
| **模块 ID** | M04 |
| **优先级** | P1 |
| **里程碑** | MS4（W7） |
| **状态** | `blocked` |
| **依赖** | M01, M03 |

---

## 1. 目标

通过 Playwright 实现 Amazon 公开页面竞品调研，为 research_agent 提供结构化数据。

## 2. 范围边界

### 2.1 首期做

- 根据关键词/ASIN 抓取 **公开** 商品页：标题、要点、价格区间、评分
- 截图存档（本地 `data/screenshots/`）供审计
- 请求频率限制：≤ 1 req / 3s，单任务最多 5 个竞品

### 2.2 首期不做

- 登录卖家后台
- 自动改价、投流、上架
- 大规模并发爬取
- 绕过验证码（遇到验证码 → 失败降级）

## 3. 交付物

- [ ] `apps/browser/` Playwright 服务
- [ ] `search_competitors(keyword, platform, limit)` 工具
- [ ] `fetch_listing(asin)` 工具
- [ ] 反爬应对：User-Agent 轮换、随机延迟、失败重试 2 次
- [ ] 接入 M03 research_agent
- [ ] 降级策略文档

## 4. 技术规范

### 4.1 服务形态

- 独立 Python 进程或 FastAPI 子路由
- Browser 实例池：max 2 concurrent contexts
- Headless chromium，Docker 内安装依赖

### 4.2 输出 Schema

```json
{
  "asin": "B0XXXX",
  "title": "...",
  "bullets": ["...", "..."],
  "price": "$29.99",
  "rating": 4.5,
  "review_count": 1234,
  "screenshot_path": "data/screenshots/xxx.png",
  "fetched_at": "iso8601"
}
```

### 4.3 合规

- 仅抓取 robots.txt 允许的路径
- 遵守 Amazon 服务条款（仅公开信息、低频、非商业转售数据）
- 日志不记录用户 Cookie

## 5. 验收标准

1. 稳定抓取 3 个指定 ASIN（连续 10 次测试 ≥ 8 次成功）
2. 失败时 research_agent 正确进入 degraded_mode
3. Docker 内 Playwright 可运行
4. 单次调研耗时 < 90s

## 6. Phase 2 预留（不在 MS4）

- TikTok Shop 公开页抓取
- Amazon SP-API 只读对接（需卖家授权）
