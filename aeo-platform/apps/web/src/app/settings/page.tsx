"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import type { TenantInfo, TenantQuota } from "@/lib/types";

type TenantMember = {
  id: string;
  email: string;
  display_name: string | null;
  role: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
};

const ROLE_LABELS: Record<string, string> = {
  owner: "拥有者",
  admin: "管理员",
  member: "成员",
  viewer: "观察者",
};

export default function SettingsPage() {
  const [tenant, setTenant] = useState<TenantInfo | null>(null);
  const [quota, setQuota] = useState<TenantQuota | null>(null);
  const [members, setMembers] = useState<TenantMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [tenantRes, quotaRes, membersRes] = await Promise.all([
          fetch("/api/tenant"),
          fetch("/api/tenant/quota"),
          fetch("/api/tenant/members"),
        ]);

        if (tenantRes.ok) {
          const json = await tenantRes.json();
          setTenant(json.data);
        }
        if (quotaRes.ok) {
          const json = await quotaRes.json();
          setQuota(json.data);
        }
        if (membersRes.ok) {
          const json = await membersRes.json();
          setMembers(json.data.items);
        }
      } catch {
        setError("加载设置失败");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  function startEdit() {
    if (!tenant) return;
    setEditName(tenant.name);
    setSaveError("");
    setSaveSuccess(false);
    setEditing(true);
  }

  function cancelEdit() {
    setEditing(false);
    setSaveError("");
    setSaveSuccess(false);
  }

  async function saveEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!tenant) return;
    const trimmed = editName.trim();
    if (!trimmed) {
      setSaveError("团队名称不能为空");
      return;
    }
    setSaving(true);
    setSaveError("");
    try {
      const res = await fetch("/api/tenant", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: trimmed }),
      });
      const json = (await res.json()) as { data?: TenantInfo; error?: string };
      if (!res.ok) {
        setSaveError(json.error || "保存失败");
        return;
      }
      setTenant(json.data ?? { ...tenant, name: trimmed });
      setEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch {
      setSaveError("网络错误，请重试");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <AppShell title="设置" description="租户信息与系统配置">
        <p className="text-sm text-[var(--muted)]">加载中...</p>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell title="设置" description="租户信息与系统配置">
        <p className="text-sm text-red-600">{error}</p>
      </AppShell>
    );
  }

  return (
    <AppShell title="设置" description="租户信息与系统配置">
      <div className="space-y-8">
        {tenant && (
          <section className="card space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">租户信息</h3>
              {!editing && (
                <button
                  type="button"
                  onClick={startEdit}
                  className="rounded-md px-3 py-1.5 text-xs font-medium text-brand-600 hover:bg-brand-50 dark:text-brand-400 dark:hover:bg-brand-900/20 transition"
                >
                  编辑
                </button>
              )}
            </div>

            {saveSuccess && !editing && (
              <p className="rounded-md bg-green-50 dark:bg-green-900/20 px-3 py-2 text-xs text-green-700 dark:text-green-400">
                保存成功
              </p>
            )}

            {editing ? (
              <form onSubmit={saveEdit} className="space-y-3">
                <div>
                  <label htmlFor="tenant-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    团队名称
                  </label>
                  <input
                    id="tenant-name"
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    autoFocus
                    className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                {saveError && (
                  <p className="text-xs text-red-600">{saveError}</p>
                )}
                <div className="flex gap-2">
                  <button
                    type="submit"
                    disabled={saving}
                    className="rounded-md bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700 disabled:opacity-50 transition"
                  >
                    {saving ? "保存中..." : "保存"}
                  </button>
                  <button
                    type="button"
                    onClick={cancelEdit}
                    disabled={saving}
                    className="rounded-md px-3 py-1.5 text-xs font-medium text-[var(--muted)] hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 transition"
                  >
                    取消
                  </button>
                </div>
              </form>
            ) : (
              <div className="grid gap-3 text-sm">
                <div className="flex justify-between gap-4">
                  <span className="text-[var(--muted)]">团队名称</span>
                  <span>{tenant.name}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-[var(--muted)]">标识</span>
                  <span className="font-mono text-xs">{tenant.slug}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-[var(--muted)]">套餐</span>
                  <span className="rounded bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700 dark:bg-brand-900/20 dark:text-brand-300">
                    {tenant.plan}
                  </span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-[var(--muted)]">状态</span>
                  <span className={tenant.is_active ? "text-green-600" : "text-red-600"}>
                    {tenant.is_active ? "活跃" : "停用"}
                  </span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-[var(--muted)]">创建时间</span>
                  <span>{new Date(tenant.created_at).toLocaleDateString("zh-CN")}</span>
                </div>
              </div>
            )}
          </section>
        )}

        {quota && (
          <section className="card space-y-3">
            <h3 className="text-lg font-semibold">配额使用</h3>
            <p className="text-xs text-[var(--muted)]">{quota.description}</p>
            <div className="grid gap-3 text-sm">
              <div className="flex justify-between gap-4">
                <span className="text-[var(--muted)]">任务数</span>
                <span>
                  {quota.tasks.used} / {quota.tasks.limit ?? "无限制"}
                  {quota.tasks.remaining !== null && (
                    <span className="ml-2 text-xs text-[var(--muted)]">
                      (剩余 {quota.tasks.remaining})
                    </span>
                  )}
                </span>
              </div>
              {quota.tasks.exceeded && (
                <p className="text-xs text-red-600">任务配额已超限</p>
              )}
              <div className="flex justify-between gap-4">
                <span className="text-[var(--muted)]">成员上限</span>
                <span>{quota.users.limit} 人</span>
              </div>
            </div>
          </section>
        )}

        {members.length > 0 && (
          <section className="card space-y-3">
            <h3 className="text-lg font-semibold">团队成员</h3>
            <div className="divide-y">
              {members.map((m) => (
                <div key={m.id} className="flex items-center justify-between py-2 text-sm">
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">
                      {m.display_name || m.email}
                    </p>
                    <p className="truncate text-xs text-[var(--muted)]">{m.email}</p>
                  </div>
                  <span className="ml-4 rounded bg-slate-100 px-2 py-0.5 text-xs dark:bg-slate-800">
                    {ROLE_LABELS[m.role] ?? m.role}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="card space-y-3">
          <h3 className="text-lg font-semibold">系统信息</h3>
          <div className="grid gap-3 text-sm">
            <div className="flex justify-between gap-4">
              <span className="text-[var(--muted)]">API 地址</span>
              <span className="font-mono text-xs">
                {process.env.API_BASE_URL ?? "http://127.0.0.1:8000"}
              </span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-[var(--muted)]">环境</span>
              <span>{process.env.NODE_ENV}</span>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
