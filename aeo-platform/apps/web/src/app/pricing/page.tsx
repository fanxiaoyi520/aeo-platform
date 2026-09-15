"use client";

import { useState } from "react";
import Link from "next/link";
import type { Plan } from "@/lib/billing-types";

const PLANS: Plan[] = [
  {
    name: "free",
    display_name: "免费版",
    description: "适合个人卖家试用",
    monthly_tasks: 10,
    max_users: 3,
    features: [
      "每月 10 个任务",
      "最多 3 个团队成员",
      "基础 AI listing 生成",
      "社区支持",
    ],
    price_monthly: 0,
    price_yearly: 0,
    stripe_price_monthly: null,
    stripe_price_yearly: null,
  },
  {
    name: "pro",
    display_name: "专业版",
    description: "适合成长中的卖家团队",
    monthly_tasks: 100,
    max_users: 10,
    features: [
      "每月 100 个任务",
      "最多 10 个团队成员",
      "高级 AI listing 优化",
      "竞品分析",
      "关键词研究",
      "优先邮件支持",
    ],
    price_monthly: 49,
    price_yearly: 470,
    stripe_price_monthly: "price_pro_monthly",
    stripe_price_yearly: "price_pro_yearly",
    popular: true,
  },
  {
    name: "enterprise",
    display_name: "企业版",
    description: "适合大型卖家和品牌",
    monthly_tasks: null,
    max_users: 100,
    features: [
      "无限任务",
      "最多 100 个团队成员",
      "全部 AI 功能",
      "高级数据分析",
      "API 访问",
      "专属客户经理",
      "SLA 保障",
    ],
    price_monthly: 199,
    price_yearly: 1910,
    stripe_price_monthly: "price_enterprise_monthly",
    stripe_price_yearly: "price_enterprise_yearly",
  },
];

export default function PricingPage() {
  const [billing, setBilling] = useState<"monthly" | "yearly">("monthly");
  const [loading, setLoading] = useState<string | null>(null);

  async function handleCheckout(priceId: string | null) {
    if (!priceId) return;
    setLoading(priceId);
    try {
      const res = await fetch("/api/billing/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ price_id: priceId }),
      });
      if (res.ok) {
        const json = await res.json();
        window.location.href = json.data?.checkout_url ?? json.checkout_url;
      }
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-950">
      <header className="border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-7xl px-4 py-4 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-brand-600 dark:text-brand-400">
            AEO Platform
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm text-[var(--muted)] hover:text-[var(--foreground)] transition">
              登录
            </Link>
            <Link
              href="/signup"
              className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition"
            >
              免费注册
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-[var(--foreground)] mb-4">
            选择适合您的方案
          </h1>
          <p className="text-lg text-[var(--muted)] max-w-2xl mx-auto">
            从免费试用到企业级解决方案，满足不同规模卖家需求
          </p>

          <div className="mt-8 inline-flex items-center rounded-lg border border-slate-200 dark:border-slate-700 p-1">
            <button
              type="button"
              onClick={() => setBilling("monthly")}
              className={`rounded-md px-4 py-2 text-sm font-medium transition ${
                billing === "monthly"
                  ? "bg-brand-600 text-white"
                  : "text-[var(--muted)] hover:text-[var(--foreground)]"
              }`}
            >
              月付
            </button>
            <button
              type="button"
              onClick={() => setBilling("yearly")}
              className={`rounded-md px-4 py-2 text-sm font-medium transition ${
                billing === "yearly"
                  ? "bg-brand-600 text-white"
                  : "text-[var(--muted)] hover:text-[var(--foreground)]"
              }`}
            >
              年付
              <span className="ml-1.5 rounded bg-green-100 dark:bg-green-900/30 px-1.5 py-0.5 text-xs text-green-700 dark:text-green-400">
                省 20%
              </span>
            </button>
          </div>
        </div>

        <div className="grid gap-8 md:grid-cols-3">
          {PLANS.map((plan) => {
            const price = billing === "monthly" ? plan.price_monthly : plan.price_yearly;
            const period = billing === "monthly" ? "/月" : "/年";
            const priceId = billing === "monthly" ? plan.stripe_price_monthly : plan.stripe_price_yearly;

            return (
              <div
                key={plan.name}
                className={`relative rounded-2xl border p-8 ${
                  plan.popular
                    ? "border-brand-500 shadow-lg shadow-brand-500/10"
                    : "border-slate-200 dark:border-slate-700"
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="rounded-full bg-brand-600 px-3 py-1 text-xs font-medium text-white">
                      最受欢迎
                    </span>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-xl font-semibold text-[var(--foreground)]">
                    {plan.display_name}
                  </h3>
                  <p className="mt-1 text-sm text-[var(--muted)]">{plan.description}</p>
                </div>

                <div className="mb-6">
                  <span className="text-4xl font-bold text-[var(--foreground)]">
                    ${price}
                  </span>
                  <span className="text-[var(--muted)]">{period}</span>
                </div>

                <button
                  type="button"
                  onClick={() => handleCheckout(priceId)}
                  disabled={loading === priceId || !priceId || price === 0}
                  className={`w-full rounded-lg py-3 text-sm font-medium transition ${
                    plan.popular
                      ? "bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50"
                      : "bg-slate-100 text-slate-900 hover:bg-slate-200 dark:bg-slate-800 dark:text-white dark:hover:bg-slate-700 disabled:opacity-50"
                  }`}
                >
                  {loading === priceId ? "跳转中..." : price === 0 ? "当前方案" : "开始订阅"}
                </button>

                <ul className="mt-8 space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3 text-sm">
                      <svg
                        className="h-5 w-5 flex-shrink-0 text-brand-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-[var(--foreground)]">{feature}</span>
                    </li>
                  ))}
                </ul>

                <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-700">
                  <dl className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <dt className="text-[var(--muted)]">任务配额</dt>
                      <dd className="font-medium text-[var(--foreground)]">
                        {plan.monthly_tasks === null ? "无限" : `${plan.monthly_tasks}/月`}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-[var(--muted)]">团队成员</dt>
                      <dd className="font-medium text-[var(--foreground)]">
                        最多 {plan.max_users} 人
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-16 text-center">
          <p className="text-sm text-[var(--muted)]">
            所有方案均包含 14 天免费试用，无需信用卡
          </p>
          <p className="mt-2 text-sm text-[var(--muted)]">
            有问题？
            <a href="mailto:support@aeo-platform.com" className="ml-1 text-brand-600 hover:underline">
              联系我们
            </a>
          </p>
        </div>
      </main>
    </div>
  );
}
