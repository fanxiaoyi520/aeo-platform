import { AppShell } from "@/components/layout/app-shell";

export default function TasksPage() {
  return (
    <AppShell title="任务" description="任务列表与创建入口将在 MS3 任务 API 就绪后接入">
      <div className="card">
        <p className="text-sm text-[var(--muted)]">暂无任务数据。请先完成 Agent 任务 API（S3-07）。</p>
      </div>
    </AppShell>
  );
}
