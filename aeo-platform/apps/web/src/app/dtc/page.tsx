"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import type { DTCDashboardData } from "@/lib/types";

function formatMoney(value: string | null): string {
  if (value === null) return "—";
  const num = parseFloat(value);
  if (Number.isNaN(num)) return value;
  return `$${num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatPercent(value: number | null): string {
  if (value === null) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card">
      <p className="text-sm text-[var(--muted)]">{label}</p>
      <p className="mt-2 text-3xl font-semibold">{value}</p>
    </div>
  );
}

export default function DTCPage() {
  const [data, setData] = useState<DTCDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("/api/dtc");
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error ?? "加载独立站数据失败");
        }
        setData(payload.data as DTCDashboardData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "加载独立站数据失败");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  return (
    <AppShell
      title="独立站看板"
      description="Shopify DTC 店铺概览 — 转化率 / 弃购率 / CLV / 邮件打开率（MV-M08）"
    >
      {loading ? <p>加载中…</p> : null}
      {error ? <p className="text-rose-600">{error}</p> : null}
      {data ? (
        <div className="space-y-8">
          <section>
            <h3 className="mb-4 text-lg font-semibold">店铺概览</h3>
            <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
              <KpiCard
                label="总产品"
                value={String(data.storefront.total_products)}
              />
              <KpiCard
                label="活跃产品"
                value={String(data.storefront.active_products)}
              />
              <KpiCard
                label="总订单"
                value={String(data.storefront.total_orders)}
              />
              <KpiCard
                label="已付款"
                value={String(data.storefront.paid_orders)}
              />
              <KpiCard
                label="低库存"
                value={String(data.storefront.low_stock_items)}
              />
              <KpiCard
                label="活跃折扣"
                value={String(data.storefront.active_discounts)}
              />
            </div>
          </section>

          <section>
            <h3 className="mb-4 text-lg font-semibold">DTC 核心指标</h3>
            <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
              <KpiCard
                label="转化率"
                value={formatPercent(data.kpis.avg_conversion_rate)}
              />
              <KpiCard
                label="弃购率"
                value={formatPercent(data.kpis.avg_cart_abandonment_rate)}
              />
              <KpiCard
                label="客单价"
                value={formatMoney(
                  data.kpis.avg_order_value !== null
                    ? String(data.kpis.avg_order_value)
                    : null,
                )}
              />
              <KpiCard label="总营收" value={formatMoney(data.kpis.total_revenue)} />
              <KpiCard
                label="客户终身价值"
                value={formatMoney(data.kpis.customer_lifetime_value)}
              />
              <KpiCard
                label="复购率"
                value={formatPercent(
                  data.kpis.repeat_purchase_rate !== null
                    ? parseFloat(data.kpis.repeat_purchase_rate)
                    : null,
                )}
              />
              <KpiCard
                label="邮件订阅率"
                value={formatPercent(
                  data.kpis.email_marketing_opt_in_rate !== null
                    ? parseFloat(data.kpis.email_marketing_opt_in_rate)
                    : null,
                )}
              />
              <KpiCard
                label="弃购购物车"
                value={String(data.kpis.abandoned_cart_count)}
              />
            </div>
          </section>

          <section>
            <h3 className="mb-4 text-lg font-semibold">弃购挽回</h3>
            <div className="grid gap-4 md:grid-cols-3">
              <KpiCard
                label="弃购总数"
                value={String(data.abandoned_carts_summary.total)}
              />
              <KpiCard
                label="已发挽回邮件"
                value={String(data.abandoned_carts_summary.recovery_email_sent)}
              />
              <KpiCard
                label="弃购总金额"
                value={formatMoney(data.abandoned_carts_summary.total_value)}
              />
            </div>
          </section>

          <section>
            <h3 className="mb-4 text-lg font-semibold">数据概要</h3>
            <div className="card">
              <p className="text-sm text-[var(--muted)]">
                统计周期 {data.kpis.metric_days} 天 | 客户数{" "}
                {data.kpis.customer_count} | 总访问{" "}
                {data.kpis.total_sessions.toLocaleString()} | 总订单{" "}
                {data.kpis.total_orders}
              </p>
            </div>
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}
