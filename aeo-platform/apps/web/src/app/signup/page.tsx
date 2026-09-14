"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function SignupPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    display_name: "",
    tenant_name: "",
    tenant_slug: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function updateField(field: string, value: string) {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }

  function slugify(name: string): string {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          tenant_slug: formData.tenant_slug || slugify(formData.tenant_name),
        }),
      });

      const data = (await res.json()) as { error?: string };

      if (!res.ok) {
        setError(data.error || "注册失败");
        return;
      }

      router.push("/");
      router.refresh();
    } catch {
      setError("网络错误，请重试");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4 py-12">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AEO Platform</h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            创建新账户
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4">
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="tenant_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                团队/公司名称
              </label>
              <input
                id="tenant_name"
                type="text"
                required
                value={formData.tenant_name}
                onChange={(e) => updateField("tenant_name", e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-900 dark:text-white placeholder-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                placeholder="我的团队"
              />
            </div>

            <div>
              <label htmlFor="display_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                您的姓名（选填）
              </label>
              <input
                id="display_name"
                type="text"
                value={formData.display_name}
                onChange={(e) => updateField("display_name", e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-900 dark:text-white placeholder-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                placeholder="张三"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                邮箱
              </label>
              <input
                id="email"
                type="email"
                required
                value={formData.email}
                onChange={(e) => updateField("email", e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-900 dark:text-white placeholder-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                密码（至少 6 位）
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={6}
                value={formData.password}
                onChange={(e) => updateField("password", e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-900 dark:text-white placeholder-gray-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "注册中..." : "注册"}
          </button>

          <p className="text-center text-sm text-gray-600 dark:text-gray-400">
            已有账户？{" "}
            <Link href="/login" className="font-medium text-brand-600 hover:text-brand-500">
              立即登录
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
