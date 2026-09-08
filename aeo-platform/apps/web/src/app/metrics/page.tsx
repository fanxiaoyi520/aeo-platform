"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import type { DashboardData, DashboardTrendEntry } from "@/lib/types";

function formatMoney(value: string | null): string {
  if (value === null) return "—";
  const num = parseFloat(value);
  if (Number.isNaN(num)) return value;
  return `$${num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatPercent(value: string | null): string {
  if (value === null) return "—";
  const num = parseFloat(value);
  if (Number.isNaN(num)) return value;
  return `${(num * 100).toFixed(1)}%`;
}

function formatRatio(value: string | null): string {
  if (value === null) return "—";
  return value;
}

function TrendBar({ entries, field }: { entries: DashboardTrendEntry[]; field: "gmv" }) {
  const values = entries.map((e) => parseFloat(e[field]));
  const max = Math.max(...values, 1);

  return (
    <div className="flex items-end gap-1 h-32">
      {entries.map((entry, i) => {
        const value = parseFloat(entry[field]);
        const height = Math.max((value / max) * 100, 4);
        return (
          <div key={entry.date} className="flex flex-1 flex-col items-center gap-1">
            <div
              className="w-full rounded-t bg-brand-500 transition-all hover:bg-brand-600"
              style={{ height: `${height}%` }}
              title={`${entry.date}: ${formatMoney(entry[field])}`}
            />
            {i % 5 === 0 ? (
              <span className="text-[10px] text-[var(--muted)]">
                {entry.date.slice(5)}
              </span>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

export default function MetricsPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("/api/metrics");
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error ?? "加载指标失败");
        }
        setData(payload.data as DashboardData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "加载指标失败");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  const trendReversed = data ? [...data.trend].reverse() : [];

  return (
    <AppShell
      title="业务指标"
      description="GMV / ROI / 人工替代率看板（MV4-06）"
    >
      {loading ? <p className="text-sm text-[var(--muted)]">加载中…</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      {data ? (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            <div className="card">
              <p className="text-sm text-[var(--muted)]">GMV（{data.period_days}天）</p>
              <p className="mt-2 text-3xl font-semibold">{formatMoney(data.gmv)}</p>
            </div>
            <div className="card">
              <p className="text-sm text-[var(--muted)]">平均 ROI</p>
              <p className="mt-2 text-3xl font-semibold">{formatRatio(data.roi)}</p>
            </div>
            <div className="card">
              <p className="text-sm text-[var(--muted)]">广告花费</p>
              <p className="mt-2 text-3xl font-semibold">{formatMoney(data.ad_spend)}</p>
            </div>
            <div className="card">
              <p className="text-sm text-[var(--muted)]">人工替代率</p>
              <p className="mt-2 text-3xl font-semibold text-emerald-600">
                {formatPercent(data.automation_rate)}
              </p>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="card">
              <p className="text-sm text-[var(--muted)]">订单总数</p>
              <p className="mt-2 text-3xl font-semibold">{data.order_count}</p>
            </div>
            <div className="card">
              <p className="text-sm text-[var(--muted)]">统计天数</p>
              <p className="mt-2 text-3xl font-semibold">{data.period_days}</p>
            </div>
          </div>

          {trendReversed.length > 0 ? (
            <div className="card">
              <h3 className="mb-4 text-lg font-semibold">GMV 趋势</h3>
              <TrendBar entries={trendReversed} field="gmv" />
            </div>
          ) : null}

          {trendReversed.length > 0 ? (
            <div className="card">
              <h3 className="mb-4 text-lg font-semibold">每日明细</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b text-[var(--muted)]" style={{ borderColor: "var(--border)" }}>
                      <th className="pb-2 pr-4">日期</th>
                      <th className="pb-2 pr-4">GMV</th>
                      <th className="pb-2 pr-4">ROI</th>
                      <th className="pb-2 pr-4">订单</th>
                      <th className="pb-2">替代率</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trendReversed.slice(0, 10).map((entry) => (
                      <tr key={entry.date} className="border-b" style={{ borderColor: "var(--border)" }}>
                        <td className="py-2 pr-4">{entry.date}</td>
                        <td className="py-2 pr-4">{formatMoney(entry.gmv)}</td>
                        <td className="py-2 pr-4">{formatRatio(entry.roi)}</td>
                        <td className="py-2 pr-4">{entry.order_count}</td>
                        <td className="py-2">{formatPercent(entry.automation_rate)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </AppShell>
  );
}
