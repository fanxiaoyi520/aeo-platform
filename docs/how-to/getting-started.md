# How-to：本地跑起来（约 15 分钟）

面向第一次克隆仓库的开发者。命令以 Windows PowerShell 为例。

## 1. 前置

- Windows 10+（或文档中的 Linux/macOS 基线，见 [`../03_DEV_ENVIRONMENT.md`](../03_DEV_ENVIRONMENT.md)）
- 建议内存 ≥ 16 GB
- 可访问 LLM API（若要跑 Agent；仅看 Web/API 骨架可先不配）

## 2. 克隆与进入代码目录

仓库根含 `docs/`；**可执行应用在 `aeo-platform/`**。

```powershell
git clone https://github.com/fanxiaoyi520/aeo-platform.git
cd aeo-platform
```

若你已在 monorepo 根目录：

```powershell
cd aeo-platform
```

## 3. 一键安装与启动

完整步骤与备选方式（无 Docker / 全容器）见：

→ **[`../../aeo-platform/README.md`](../../aeo-platform/README.md)** §快速开始

摘要：

```powershell
.\scripts\setup.ps1          # 仅首次：uv + pnpm + 依赖
.\scripts\dev-start.ps1      # Postgres/Redis + API + Web
```

浏览器：

- http://127.0.0.1:3000 — Web
- http://127.0.0.1:8000/docs — API（OpenAPI）

停止：`.\scripts\dev-stop.ps1`

## 4. 合并前自检

```powershell
.\scripts\test.ps1
```

须全绿；云端同等检查见 PR 上的 GitHub Actions CI。

## 5. 接下来写代码

1. 读 [`../../AGENTS.md`](../../AGENTS.md)（分层阅读）
2. 看 [`../02_PROGRESS.md`](../02_PROGRESS.md) 顶部：当前任务
3. 按 [`../06_TASK_SPEC.md`](../06_TASK_SPEC.md) 出 Spec，等用户「开始」

更多角色入口：[`../README.md`](../README.md)。
