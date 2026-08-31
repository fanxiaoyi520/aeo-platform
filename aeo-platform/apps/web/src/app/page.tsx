import { AppShell } from "@/components/layout/app-shell";

export default function DashboardPage() {
  return (
    <AppShell title="仪表盘" description="今日任务概览与系统状态（MS5 后续完善）">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="card">
          <p className="text-sm text-[var(--muted)]">今日任务</p>
          <p className="mt-2 text-3xl font-semibold">—</p>
        </div>
        <div className="card">
          <p className="text-sm text-[var(--muted)]">通过率</p>
          <p className="mt-2 text-3xl font-semibold">—</p>
        </div>
        <div className="card">
          <p className="text-sm text-[var(--muted)]">平均耗时</p>
          <p className="mt-2 text-3xl font-semibold">—</p>
        </div>
      </div>
    </AppShell>
  );
}
