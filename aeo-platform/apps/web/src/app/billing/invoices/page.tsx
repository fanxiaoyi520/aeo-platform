"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import type { Invoice } from "@/lib/billing-types";

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("/api/billing/invoices");
        if (res.ok) {
          const json = await res.json();
          setInvoices(json.data?.items ?? json.items ?? []);
        } else {
          setError("加载发票失败");
        }
      } catch {
        setError("网络错误");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  function formatCurrency(amount: number, currency: string) {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency.toUpperCase(),
    }).format(amount / 100);
  }

  function formatDate(dateStr: string | null) {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("zh-CN");
  }

  function getStatusLabel(status: string) {
    switch (status) {
      case "paid":
        return { label: "已支付", className: "text-green-600 bg-green-50 dark:bg-green-900/20" };
      case "open":
        return { label: "待支付", className: "text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20" };
      case "void":
        return { label: "已作废", className: "text-gray-600 bg-gray-50 dark:bg-gray-900/20" };
      case "uncollectible":
        return { label: "无法收取", className: "text-red-600 bg-red-50 dark:bg-red-900/20" };
      default:
        return { label: status, className: "text-gray-600 bg-gray-50 dark:bg-gray-900/20" };
    }
  }

  if (loading) {
    return (
      <AppShell title="发票" description="查看和下载您的账单发票">
        <p className="text-sm text-[var(--muted)]">加载中...</p>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell title="发票" description="查看和下载您的账单发票">
        <p className="text-sm text-red-600">{error}</p>
      </AppShell>
    );
  }

  return (
    <AppShell title="发票" description="查看和下载您的账单发票">
      <div className="space-y-4">
        {invoices.length === 0 ? (
          <div className="card text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-[var(--muted)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p className="mt-4 text-sm text-[var(--muted)]">暂无发票记录</p>
          </div>
        ) : (
          <div className="card overflow-hidden">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
              <thead className="bg-slate-50 dark:bg-slate-800/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[var(--muted)] uppercase tracking-wider">
                    发票编号
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[var(--muted)] uppercase tracking-wider">
                    金额
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[var(--muted)] uppercase tracking-wider">
                    账单周期
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[var(--muted)] uppercase tracking-wider">
                    状态
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[var(--muted)] uppercase tracking-wider">
                    支付日期
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-[var(--muted)] uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700 bg-white dark:bg-slate-900">
                {invoices.map((invoice) => {
                  const status = getStatusLabel(invoice.status);
                  return (
                    <tr key={invoice.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="px-4 py-3 text-sm font-mono text-[var(--foreground)]">
                        {invoice.stripe_invoice_id}
                      </td>
                      <td className="px-4 py-3 text-sm text-[var(--foreground)]">
                        {formatCurrency(invoice.amount_due, invoice.currency)}
                      </td>
                      <td className="px-4 py-3 text-sm text-[var(--muted)]">
                        {formatDate(invoice.period_start)} - {formatDate(invoice.period_end)}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${status.className}`}>
                          {status.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-[var(--muted)]">
                        {formatDate(invoice.paid_at)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {invoice.invoice_pdf ? (
                          <a
                            href={invoice.invoice_pdf}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-brand-600 hover:underline"
                          >
                            下载 PDF
                          </a>
                        ) : invoice.hosted_invoice_url ? (
                          <a
                            href={invoice.hosted_invoice_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-brand-600 hover:underline"
                          >
                            查看
                          </a>
                        ) : (
                          <span className="text-sm text-[var(--muted)]">-</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  );
}
