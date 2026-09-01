# 任务 Spec 模板（Task Spec）

> **用途：** 每个开发任务开工前，总控在对话中贴 Spec；用户回复「开始」后 Agent 方可写代码。  
> **工作流：** 单总控 + Spec + Git 分支 + **PR** + CI（见 [`AGENTS.md`](../AGENTS.md)）  
> **任务来源：** [`02_PROGRESS.md`](02_PROGRESS.md)

---

## 使用流程（进阶档）

```
1. 用户：「做 S3-05」
2. Agent：读进度表 + 模块文档 → 输出 Spec
3. 用户：「开始」
4. Agent：git checkout -b feat/s3-05-compliance-agent → 开发 → commit
5. 用户：「合并检查」→ test.ps1 全绿
6. 用户：「开 PR」→ push + gh pr create → CI 绿
7. 用户看过 diff → merge PR → 更新 02_PROGRESS.md
```

可选：在 GitHub 用 **Issue 模板**（`.github/ISSUE_TEMPLATE/task.yml`）建任务跟踪，PR 描述里填 `关联 Issue: #N`。

大任务（估时 > 2h 或跨模块）：用户说 **「探索 {任务ID}」** 时，先走下方「设计探索」，确认后再出标准 Spec。

---

## 设计探索（大任务可选）

> 对应 Superpowers `brainstorming` 思路；**不替代**总计划与模块文档，仅在 Spec 前补充方案对比。

**触发：** 用户说「探索 S3-05」或任务明显复杂、有多种实现路径。

```markdown
## 设计探索 — {任务ID}

**目标：** {一句话}

**澄清问题：**（一次只问一个，等用户回答）
1. {问题 1}

**方案对比：**
| 方案 | 优点 | 缺点 | 复杂度 |
|------|------|------|--------|
| A | … | … | 低/中/高 |
| B | … | … | … |

**推荐：** 方案 {X} — {理由}

---
确认方案后，我将输出标准 Task Spec；用户回复「开始」后再写代码。
```

**规则：** 未确认方案前 **禁止写代码**；方案不得超出 `01_MASTER_PLAN` 范围（超出须走 CR）。

---

## 开源优先（分级，统一治理）

> 规则全文：`.cursor/rules/oss-first-implementation.mdc` · 架构原则 **A8**

| 级别 | 何时 | Spec / PR 要求 |
|------|------|----------------|
| **L0** | bugfix、纯文档/配置、<30min 小改 | 不写调研 |
| **L1** | 新脚本、单文件工具、adapter 薄封装 | **开源参考（L1）：** 2～3 行（项目 + 采纳方式） |
| **L2** | 新包、新 Agent 能力、外部系统集成 | **开源调研（L2）：** Top 3 表 + 采纳决策 |

**L2 对比表模板：**

| 项目 | Stars | License | 可借鉴点 | 为何不直接采用 |
|------|-------|---------|----------|----------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

**采纳决策：** 依赖 / 薄封装 / 复制（注明来源）/ 自研（附理由）

**已有选型无需重复调研：** LangGraph、Chroma、Playwright、FastAPI、Next.js。

---

## TDD 纪律（功能开发强制）

> 对应 Superpowers `test-driven-development`。合并前 `test.ps1` 全绿是底线；**开发过程**须遵守 RED → GREEN → REFACTOR。

| 阶段 | 要求 | 证据 |
|------|------|------|
| **RED** | 先写失败测试 | 贴出失败输出（pytest 报错或 `FAILED`） |
| **GREEN** | 写最少实现使测试通过 | 贴出该测试通过输出 |
| **REFACTOR** | 整理代码，行为不变 | `test.ps1` 仍全绿 |

**违规处理：** 若先写了实现再补测试 → **删除实现**，从 RED 重来。

**例外（须在 Spec 写明）：** 纯 UI 样式、仅文档、仅配置 — 可跳过 TDD，但须有其他可测验收项。

---

## 标准版（复制填空）

```markdown
## 任务 Spec — {任务ID}

**任务：** {一句话目标}

**做什么：**
- {要点 1}
- {要点 2}

**不做什么：**
- {边界 1}
- {边界 2}

**TDD：** 按 §TDD 纪律 — 先 RED 再 GREEN（功能开发默认强制）

**开源：** L0 / L1 / L2（见 §开源优先）— L1 简表或 L2 完整对比表

**验收标准：**
1. {可测条件 1}
2. `cd aeo-platform; .\scripts\test.ps1` 全绿
3. {可测条件 3}
4. 完成时附证据：`test.ps1` 输出或关键命令实测结果

**相关文件：**
- 进度表：[`02_PROGRESS.md`](docs/02_PROGRESS.md) §{Sprint}
- 模块文档：`docs/modules/{Mxx-xxx.md}`
- 代码目录：`{见下方目录锁定表}`

**分支：** `feat/{任务ID小写}-{英文简述}`

---
请确认理解；用户回复「开始」后再写代码。
```

---

## 极简版（小改动、< 30 分钟）

```markdown
## Spec — {任务ID}

做：{一句话}
不做：{边界}
开源：L0（默认）/ L1 一行参考
验收：① {测什么} ② test.ps1 全绿
文件：`docs/modules/{Mxx}.md`、`{代码目录}`
分支：feat/{任务ID}-{简述}

确认后开始。
```

---

## 修 Bug 版（系统化调试，四阶段）

> 对应 Superpowers `systematic-debugging`。禁止未验证根因就改代码。

```markdown
## Bug Spec — {简述}

**Phase 1 复现**
- 现象：{报错或错误行为}
- 命令：{复现步骤}
- 实际输出：{粘贴日志/报错}

**Phase 2 隔离**
- 最小复现路径：{缩减后的步骤}
- 已排除：{试过但不相关的方向}

**Phase 3 根因**
- 假设：{根因猜测}
- 验证：{如何证明}
- 确认根因：{一句话}（未确认前禁止改代码）

**Phase 4 修复**
- 方案：{改什么、为什么}
- 防回归测试：{新增或更新的测试名}

**范围：** 只改 `{文件或目录}`，不动计划外目录

**验收：**
1. 原复现步骤不再失败
2. 防回归测试绿
3. `cd aeo-platform; .\scripts\test.ps1` 全绿
4. 附 `test.ps1` 输出作为证据

用户确认 Phase 3 根因后再进入 Phase 4 改代码。
```

---

## 目录锁定（Lane 速查）

| Lane | 典型任务 | 可改目录 | 禁止（除非总控点名） |
|------|----------|----------|----------------------|
| A | S2-xx、S1-xx 基础设施 | `aeo-platform/infra/`、`aeo-platform/scripts/dev-up*` | `apps/*` |
| B | S3-xx Agent | `aeo-platform/apps/orchestrator/` | `apps/web/`、`packages/shared` 改动 |
| D | S5-xx 前端 | `aeo-platform/apps/web/` | `apps/orchestrator/` |
| E | Docker 安装脚本 | `aeo-platform/scripts/install-docker*` | — |

**总控专属：** `packages/shared`、DB migration、`docs/02_PROGRESS.md` 里程碑状态。

---

## 模块文档速查

| 任务前缀 | 模块文档 |
|----------|----------|
| S1-xx、S2-xx | `docs/modules/M01-infrastructure.md`、`M02-rag-knowledge.md` |
| S3-xx | `docs/modules/M03-agent-orchestration.md` |
| S4-xx | `docs/modules/M04-browser-automation.md` |
| S5-xx | `docs/modules/M05-frontend-workbench.md` |
| S6-xx | `docs/modules/M06-deployment-security.md` |
| S7-xx | `docs/modules/M07-observability-metrics.md` |

---

## 填好的示例 — S3-05 compliance_agent

```markdown
## 任务 Spec — S3-05

**任务：** 实现 compliance_agent：校验 generate 输出，不通过则回流 generate（最多 3 次）

**做什么：**
- 校验标题字数、禁用词、Bullet 条数、HTML 标签
- 输出 `passed`、`issues[]`；失败时尝试 `fixed_output` 或标记回流
- 接入 LangGraph 图，与 generate_agent 形成重试回路

**不做什么：**
- 不改 `apps/web/`
- 不改 DB schema / migration
- 不实现 HITL（属 S3-06）

**验收标准：**
1. 单测覆盖：通过样例、禁用词、条数不足、超 3 次重试停止
2. `cd aeo-platform; .\scripts\test.ps1` 全绿
3. 图执行 compliance 节点后 state 含 `compliance_result`

**相关文件：**
- 模块文档：`docs/modules/M03-agent-orchestration.md` §2.4
- 代码目录：`aeo-platform/apps/orchestrator/`

**分支：** `feat/s3-05-compliance-agent`

---
请确认理解；用户回复「开始」后再写代码。
```

---

## 总控口令

| 说 | 效果 |
|----|------|
| **做 S3-05** | Agent 读进度表 + 模块文档，输出 Spec，**不写代码** |
| **探索 S3-05** | 大任务先输出「设计探索」，确认后再出 Spec |
| **开始** | 在 `feat/*` 分支按 Spec 开发（功能任务遵守 §TDD 纪律） |
| **合并检查** | 跑 `test.ps1`，列改动文件，报是否可开 PR |
| **开 PR** | push 分支，`gh pr create` 填模板，等 CI |
| **合 PR** | CI 绿 + diff 确认后 merge，更新进度表 |

---

## Commit 格式

```
feat(orchestrator): S3-05 compliance_agent + retry loop
fix(web): S5-02 task list loading state
docs: add 06_TASK_SPEC PR workflow
```

格式：`类型(范围): 任务ID 简述`

| 类型 | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `test` | 仅测试 |
| `docs` | 仅文档 |
| `chore` | 工具链、依赖、杂项 |

---

## 进阶档自检（每任务结束前）

- [ ] Spec 已确认，改动未超出「不做什么」
- [ ] L1/L2 任务：Spec 或 PR 含开源调研（见 §开源优先）
- [ ] 功能开发已走 TDD（RED → GREEN → REFACTOR，有失败测试证据）
- [ ] `test.ps1` 全绿，且已贴完整输出作为证据
- [ ] commit message 符合格式
- [ ] 已开 PR，CI 绿
- [ ] 看过 `git diff main` 无计划外文件
- [ ] 工人模式：已完成 `SESSIONS.md` §两阶段审查
- [ ] merge 后 `02_PROGRESS.md` 已更新

---

## Agent 规则

1. 用户未说「开始」→ **禁止写代码**，只输出 Spec、设计探索或答疑  
2. Spec 必须引用 `02_PROGRESS.md` 中对应任务 ID 与模块文档  
3. 「不做什么」须包含 Lane 目录边界（见上表）  
4. 验收标准至少一条业务可测 + **test.ps1 全绿** + **完成证据**（输出/日志）  
5. 功能开发默认遵守 §TDD 纪律；Bug 修复遵守 §修 Bug 版四阶段
6. 大任务用户说「探索」→ 先设计探索，确认后再出 Spec
7. L1/L2 功能须在 Spec 中写开源参考或对比表（§开源优先）；L0 可跳过
