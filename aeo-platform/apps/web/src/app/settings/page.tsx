import { AppShell } from "@/components/layout/app-shell";

export default function SettingsPage() {
  return (
    <AppShell title="设置" description="LLM 与系统配置（只读展示，MS6 完善）">
      <div className="card space-y-3 text-sm">
        <div className="flex justify-between gap-4">
          <span className="text-[var(--muted)]">API</span>
          <span>{process.env.API_BASE_URL ?? "http://127.0.0.1:8000"}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-[var(--muted)]">环境</span>
          <span>{process.env.NODE_ENV}</span>
        </div>
      </div>
    </AppShell>
  );
}
