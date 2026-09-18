"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { useAuth } from "@/contexts/auth-context";
import type { TenantInfo, TenantQuota } from "@/lib/types";
import type { Subscription } from "@/lib/billing-types";

type TenantMember = {
  id: string;
  email: string;
  display_name: string | null;
  role: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
};

export default function SettingsPage() {
  const { user } = useAuth();
  const [tenant, setTenant] = useState<TenantInfo | null>(null);
  const [quota, setQuota] = useState<TenantQuota | null>(null);
  const [members, setMembers] = useState<TenantMember[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [portalLoading, setPortalLoading] = useState(false);

  const [shopifyCreds, setShopifyCreds] = useState<Array<{
    id: string;
    shop_name: string;
    store_url_masked: string;
    access_token_masked: string;
    is_active: boolean;
  }>>([]);
  const [showShopifyForm, setShowShopifyForm] = useState(false);
  const [shopifyStoreUrl, setShopifyStoreUrl] = useState("");
  const [shopifyAccessToken, setShopifyAccessToken] = useState("");
  const [shopifyShopName, setShopifyShopName] = useState("");
  const [shopifySaving, setShopifySaving] = useState(false);
  const [shopifyError, setShopifyError] = useState("");
  const [shopifySuccess, setShopifySuccess] = useState("");
  const [shopifyTesting, setShopifyTesting] = useState(false);
  const [shopifyTestResult, setShopifyTestResult] = useState<{
    success: boolean;
    shop_name?: string;
    granted_scopes?: string[];
    missing_required_scopes?: string[];
    error?: string;
  } | null>(null);

  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [tenantRes, quotaRes, membersRes, subRes, shopifyRes] = await Promise.all([
          fetch("/api/tenant"),
          fetch("/api/tenant/quota"),
          fetch("/api/tenant/members"),
          fetch("/api/billing/subscription"),
          fetch("/api/v1/shopify/credentials"),
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
        if (subRes.ok) {
          const json = await subRes.json();
          const data = json.data ?? json;
          if (data.has_subscription && data.subscription) {
            setSubscription(data.subscription);
          }
        }
        if (shopifyRes.ok) {
          const json = await shopifyRes.json();
          setShopifyCreds(json.data?.credentials ?? []);
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

  async function handlePortal() {
    setPortalLoading(true);
    try {
      const res = await fetch("/api/billing/portal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (res.ok) {
        const json = await res.json();
        const url = json.data?.portal_url ?? json.portal_url;
        if (url) {
          window.location.href = url;
          return;
        }
      }
    } finally {
      setPortalLoading(false);
    }
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

  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviting, setInviting] = useState(false);
  const [memberError, setMemberError] = useState("");
  const [memberSuccess, setMemberSuccess] = useState("");
  const [actingId, setActingId] = useState("");

  async function loadMembers() {
    try {
      const res = await fetch("/api/tenant/members");
      if (res.ok) {
        const json = await res.json();
        setMembers(json.data.items);
      }
    } catch {
      /* ignore */
    }
  }

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    const email = inviteEmail.trim();
    if (!email) {
      setMemberError("邮箱不能为空");
      return;
    }
    setInviting(true);
    setMemberError("");
    try {
      const res = await fetch("/api/tenant/members", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, role: inviteRole }),
      });
      const json = (await res.json()) as { error?: string };
      if (!res.ok) {
        if (res.status === 403) {
          setMemberError("MEMBER_LIMIT");
        } else {
          setMemberError(json.error || "邀请失败");
        }
        return;
      }
      setShowInvite(false);
      setInviteEmail("");
      setInviteRole("member");
      setMemberSuccess("邀请成功");
      setTimeout(() => setMemberSuccess(""), 3000);
      await loadMembers();
    } catch {
      setMemberError("网络错误，请重试");
    } finally {
      setInviting(false);
    }
  }

  async function handleRoleChange(memberId: string, newRole: string) {
    setActingId(memberId);
    setMemberError("");
    try {
      const res = await fetch(`/api/tenant/members/${encodeURIComponent(memberId)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: newRole }),
      });
      const json = (await res.json()) as { error?: string };
      if (!res.ok) {
        setMemberError(json.error || "修改角色失败");
        return;
      }
      setMemberSuccess("角色已更新");
      setTimeout(() => setMemberSuccess(""), 3000);
      await loadMembers();
    } catch {
      setMemberError("网络错误，请重试");
    } finally {
      setActingId("");
    }
  }

  async function handleDeactivate(memberId: string) {
    setActingId(memberId);
    setMemberError("");
    try {
      const res = await fetch(`/api/tenant/members/${encodeURIComponent(memberId)}`, {
        method: "DELETE",
      });
      const json = (await res.json()) as { error?: string };
      if (!res.ok) {
        setMemberError(json.error || "停用失败");
        return;
      }
      setMemberSuccess("成员已停用");
      setTimeout(() => setMemberSuccess(""), 3000);
      await loadMembers();
    } catch {
      setMemberError("网络错误，请重试");
    } finally {
      setActingId("");
    }
  }

  async function loadShopifyCreds() {
    try {
      const res = await fetch("/api/v1/shopify/credentials");
      if (res.ok) {
        const json = await res.json();
        setShopifyCreds(json.data?.credentials ?? []);
      }
    } catch {
      /* ignore */
    }
  }

  async function handleShopifySave(e: React.FormEvent) {
    e.preventDefault();
    if (!shopifyStoreUrl.trim() || !shopifyAccessToken.trim()) {
      setShopifyError("Store URL 和 Access Token 不能为空");
      return;
    }
    setShopifySaving(true);
    setShopifyError("");
    setShopifySuccess("");
    setShopifyTestResult(null);
    try {
      const res = await fetch("/api/v1/shopify/credentials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          store_url: shopifyStoreUrl.trim(),
          access_token: shopifyAccessToken.trim(),
          shop_name: shopifyShopName.trim(),
        }),
      });
      if (!res.ok) {
        const json = await res.json();
        setShopifyError(json.error || "保存失败");
        return;
      }
      setShopifySuccess("凭据已保存");
      setShowShopifyForm(false);
      setShopifyStoreUrl("");
      setShopifyAccessToken("");
      setShopifyShopName("");
      setTimeout(() => setShopifySuccess(""), 3000);
      await loadShopifyCreds();
    } catch {
      setShopifyError("网络错误，请重试");
    } finally {
      setShopifySaving(false);
    }
  }

  async function handleShopifyTest(credId?: string) {
    setShopifyTesting(true);
    setShopifyTestResult(null);
    setShopifyError("");
    try {
      const body = credId ? { credential_id: credId } : {
        store_url: shopifyStoreUrl.trim(),
        access_token: shopifyAccessToken.trim(),
      };
      const res = await fetch("/api/v1/shopify/credentials/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      setShopifyTestResult(json.data);
    } catch {
      setShopifyError("测试请求失败");
    } finally {
      setShopifyTesting(false);
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

        <section className="card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">订阅管理</h3>
            <Link
              href="/pricing"
              className="rounded-md px-3 py-1.5 text-xs font-medium text-brand-600 hover:bg-brand-50 dark:text-brand-400 dark:hover:bg-brand-900/20 transition"
            >
              查看方案
            </Link>
          </div>

          {subscription ? (
            <div className="grid gap-3 text-sm">
              <div className="flex justify-between gap-4">
                <span className="text-[var(--muted)]">当前方案</span>
                <span className="rounded bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700 dark:bg-brand-900/20 dark:text-brand-300">
                  {subscription.plan}
                </span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-[var(--muted)]">订阅状态</span>
                <span className={
                  subscription.status === "active"
                    ? "text-green-600"
                    : subscription.status === "trialing"
                    ? "text-blue-600"
                    : "text-yellow-600"
                }>
                  {subscription.status === "active" ? "活跃" :
                   subscription.status === "trialing" ? "试用中" :
                   subscription.status}
                </span>
              </div>
              {subscription.current_period_end && (
                <div className="flex justify-between gap-4">
                  <span className="text-[var(--muted)]">下次续费</span>
                  <span>{new Date(subscription.current_period_end).toLocaleDateString("zh-CN")}</span>
                </div>
              )}
              {subscription.cancel_at_period_end && (
                <p className="text-xs text-yellow-600">
                  订阅将于当前周期结束后取消
                </p>
              )}
              <div className="pt-2 flex gap-2">
                <button
                  type="button"
                  onClick={handlePortal}
                  disabled={portalLoading}
                  className="rounded-md bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-900 hover:bg-slate-200 dark:bg-slate-800 dark:text-white dark:hover:bg-slate-700 disabled:opacity-50 transition"
                >
                  {portalLoading ? "跳转中..." : "管理订阅"}
                </button>
                <Link
                  href="/billing/invoices"
                  className="rounded-md px-3 py-1.5 text-xs font-medium text-[var(--muted)] hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                >
                  查看发票
                </Link>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-[var(--muted)]">
                {tenant?.plan === "free" ? "当前使用免费版" : "暂无活跃订阅"}
              </p>
              <Link
                href="/pricing"
                className="inline-block rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition"
              >
                升级方案
              </Link>
            </div>
          )}
        </section>

        <section className="card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Shopify 店铺连接</h3>
            {!showShopifyForm && (
              <button
                type="button"
                onClick={() => { setShowShopifyForm(true); setShopifyError(""); setShopifyTestResult(null); }}
                className="rounded-md px-3 py-1.5 text-xs font-medium text-brand-600 hover:bg-brand-50 dark:text-brand-400 dark:hover:bg-brand-900/20 transition"
              >
                {shopifyCreds.length > 0 ? "更新凭据" : "添加店铺"}
              </button>
            )}
          </div>

          {shopifySuccess && (
            <p className="rounded-md bg-green-50 dark:bg-green-900/20 px-3 py-2 text-xs text-green-700 dark:text-green-400">
              {shopifySuccess}
            </p>
          )}
          {shopifyError && (
            <p className="rounded-md bg-red-50 dark:bg-red-900/20 px-3 py-2 text-xs text-red-700 dark:text-red-400">
              {shopifyError}
            </p>
          )}

          {showShopifyForm && (
            <form onSubmit={handleShopifySave} className="space-y-3 rounded-md border border-slate-200 dark:border-slate-700 p-3">
              <div>
                <label htmlFor="shopify-store-url" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Store URL
                </label>
                <input
                  id="shopify-store-url"
                  type="text"
                  value={shopifyStoreUrl}
                  onChange={(e) => setShopifyStoreUrl(e.target.value)}
                  placeholder="your-store.myshopify.com"
                  className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>
              <div>
                <label htmlFor="shopify-access-token" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Admin API Access Token
                </label>
                <input
                  id="shopify-access-token"
                  type="password"
                  value={shopifyAccessToken}
                  onChange={(e) => setShopifyAccessToken(e.target.value)}
                  placeholder="shpat_xxxxxxxxxxxx"
                  className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>
              <div>
                <label htmlFor="shopify-shop-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  店铺名称（可选）
                </label>
                <input
                  id="shopify-shop-name"
                  type="text"
                  value={shopifyShopName}
                  onChange={(e) => setShopifyShopName(e.target.value)}
                  placeholder="My Shopify Store"
                  className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={shopifySaving}
                  className="rounded-md bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700 disabled:opacity-50 transition"
                >
                  {shopifySaving ? "保存中..." : "保存凭据"}
                </button>
                <button
                  type="button"
                  onClick={() => { setShowShopifyForm(false); setShopifyError(""); }}
                  disabled={shopifySaving}
                  className="rounded-md px-3 py-1.5 text-xs font-medium text-[var(--muted)] hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 transition"
                >
                  取消
                </button>
                <button
                  type="button"
                  onClick={() => void handleShopifyTest()}
                  disabled={shopifyTesting || !shopifyStoreUrl.trim() || !shopifyAccessToken.trim()}
                  className="rounded-md px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 disabled:opacity-50 transition"
                >
                  {shopifyTesting ? "测试中..." : "测试连接"}
                </button>
              </div>
            </form>
          )}

          {shopifyTestResult && (
            <div className={`rounded-md p-3 text-xs ${shopifyTestResult.success ? "bg-green-50 dark:bg-green-900/20" : "bg-red-50 dark:bg-red-900/20"}`}>
              {shopifyTestResult.success ? (
                <div className="space-y-2">
                  <p className="font-medium text-green-700 dark:text-green-400">连接成功</p>
                  {shopifyTestResult.shop_name && (
                    <p className="text-green-600 dark:text-green-300">店铺: {shopifyTestResult.shop_name}</p>
                  )}
                  {shopifyTestResult.granted_scopes && (
                    <div>
                      <p className="text-green-600 dark:text-green-300">已授权 scopes: {shopifyTestResult.granted_scopes.join(", ") || "无"}</p>
                    </div>
                  )}
                  {shopifyTestResult.missing_required_scopes && shopifyTestResult.missing_required_scopes.length > 0 && (
                    <p className="text-yellow-600 dark:text-yellow-400">
                      缺少必需 scopes: {shopifyTestResult.missing_required_scopes.join(", ")}
                    </p>
                  )}
                  {shopifyTestResult.all_required_present && (
                    <p className="text-green-600 dark:text-green-300">所有必需 scopes 已授权</p>
                  )}
                </div>
              ) : (
                <p className="text-red-700 dark:text-red-400">连接失败: {shopifyTestResult.error}</p>
              )}
            </div>
          )}

          {!showShopifyForm && shopifyCreds.length > 0 && (
            <div className="divide-y">
              {shopifyCreds.map((cred) => (
                <div key={cred.id} className="flex items-center justify-between gap-3 py-2 text-sm">
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{cred.shop_name || "未命名店铺"}</p>
                    <p className="truncate text-xs text-[var(--muted)]">
                      {cred.store_url_masked} · Token: {cred.access_token_masked}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`rounded px-2 py-0.5 text-xs ${cred.is_active ? "bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400" : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"}`}>
                      {cred.is_active ? "活跃" : "停用"}
                    </span>
                    <button
                      type="button"
                      onClick={() => void handleShopifyTest(cred.id)}
                      disabled={shopifyTesting}
                      className="rounded-md px-2 py-1 text-xs text-brand-600 hover:bg-brand-50 dark:text-brand-400 dark:hover:bg-brand-900/20 disabled:opacity-50 transition"
                    >
                      测试
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {!showShopifyForm && shopifyCreds.length === 0 && (
            <p className="text-sm text-[var(--muted)]">
              未配置 Shopify 店铺凭据。添加凭据以连接真实店铺数据。
            </p>
          )}
        </section>

        <section className="card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">团队成员</h3>
            {!showInvite && (
              <button
                type="button"
                onClick={() => { setShowInvite(true); setMemberError(""); }}
                className="rounded-md px-3 py-1.5 text-xs font-medium text-brand-600 hover:bg-brand-50 dark:text-brand-400 dark:hover:bg-brand-900/20 transition"
              >
                邀请成员
              </button>
            )}
          </div>

          {memberSuccess && (
            <p className="rounded-md bg-green-50 dark:bg-green-900/20 px-3 py-2 text-xs text-green-700 dark:text-green-400">
              {memberSuccess}
            </p>
          )}
          {memberError && memberError !== "MEMBER_LIMIT" && (
            <p className="rounded-md bg-red-50 dark:bg-red-900/20 px-3 py-2 text-xs text-red-700 dark:text-red-400">
              {memberError}
            </p>
          )}
          {memberError === "MEMBER_LIMIT" && (
            <div className="rounded-md bg-yellow-50 dark:bg-yellow-900/20 px-3 py-3">
              <p className="text-xs text-yellow-700 dark:text-yellow-400">
                已达到当前方案的成员上限，请升级以添加更多成员。
              </p>
              <Link
                href="/pricing"
                className="mt-2 inline-block text-xs font-medium text-brand-600 hover:underline dark:text-brand-400"
              >
                查看升级方案 →
              </Link>
            </div>
          )}

          {showInvite && (
            <form onSubmit={handleInvite} className="space-y-3 rounded-md border border-slate-200 dark:border-slate-700 p-3">
              <div>
                <label htmlFor="invite-email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  邮箱
                </label>
                <input
                  id="invite-email"
                  type="email"
                  required
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  autoFocus
                  className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  placeholder="colleague@example.com"
                />
              </div>
              <div>
                <label htmlFor="invite-role" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  角色
                </label>
                <select
                  id="invite-role"
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="admin">管理员</option>
                  <option value="member">成员</option>
                  <option value="viewer">观察者</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={inviting}
                  className="rounded-md bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700 disabled:opacity-50 transition"
                >
                  {inviting ? "发送中..." : "发送邀请"}
                </button>
                <button
                  type="button"
                  onClick={() => { setShowInvite(false); setMemberError(""); }}
                  disabled={inviting}
                  className="rounded-md px-3 py-1.5 text-xs font-medium text-[var(--muted)] hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 transition"
                >
                  取消
                </button>
              </div>
            </form>
          )}

          {members.length > 0 ? (
            <div className="divide-y">
              {members.map((m) => {
                const isSelf = user?.id === m.id;
                return (
                  <div key={m.id} className="flex items-center justify-between gap-3 py-2 text-sm">
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium">
                        {m.display_name || m.email}
                        {isSelf && <span className="ml-1 text-xs text-[var(--muted)]">(我)</span>}
                      </p>
                      <p className="truncate text-xs text-[var(--muted)]">{m.email}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <select
                        value={m.role}
                        onChange={(e) => void handleRoleChange(m.id, e.target.value)}
                        disabled={actingId === m.id}
                        className="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-gray-800 px-2 py-1 text-xs focus:border-brand-500 focus:outline-none disabled:opacity-50"
                      >
                        <option value="owner">拥有者</option>
                        <option value="admin">管理员</option>
                        <option value="member">成员</option>
                        <option value="viewer">观察者</option>
                      </select>
                      {!isSelf && (
                        <button
                          type="button"
                          onClick={() => void handleDeactivate(m.id)}
                          disabled={actingId === m.id}
                          className="rounded-md px-2 py-1 text-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50 transition"
                          title="停用成员"
                        >
                          停用
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-[var(--muted)]">暂无成员</p>
          )}
        </section>

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
