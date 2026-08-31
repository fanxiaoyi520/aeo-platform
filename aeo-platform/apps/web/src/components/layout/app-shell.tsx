import { SidebarNav } from "@/components/layout/sidebar-nav";

type AppShellProps = {
  title: string;
  description?: string;
  children: React.ReactNode;
};

export function AppShell({ title, description, children }: AppShellProps) {
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="border-b p-6 lg:min-h-screen lg:border-b-0 lg:border-r" style={{ borderColor: "var(--border)" }}>
        <div className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-600">AEO Platform</p>
          <h1 className="mt-2 text-lg font-semibold">运营工作台</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">Autonomous Ecommerce Operator</p>
        </div>
        <SidebarNav />
      </aside>

      <main className="p-6 lg:p-10">
        <header className="mb-8">
          <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
          {description ? <p className="mt-2 text-sm text-[var(--muted)]">{description}</p> : null}
        </header>
        {children}
      </main>
    </div>
  );
}
