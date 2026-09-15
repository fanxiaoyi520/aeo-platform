"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import type {
  RiskAuditItem,
  RiskDecision,
  RiskLevel,
  RiskRuleSet,
} from "@/lib/types";

const RISK_LEVEL_STYLES: Record<RiskLevel, string> = {
  L0: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200",
  L1: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  L2: "bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200",
};

const EFFECT_LABELS: Record<string, string> = {
  allow: "自动放行",
  require_hitl: "需人审",
  deny: "拒绝",
};

const ACTION_OPTIONS = [
  "research.read",
  "listing.generate",
  "listing.publish",
  "listing.update",
  "price.update",
  "ads.bid_change",
  "ads.budget_change",
  "order.refund",
  "account.open",
];

type RiskData = {
  rules: RiskRuleSet;
  audit: { items: RiskAuditItem[]; total: number };
};

export default function RiskConfigPage() {
  const [data, setData] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [evalAction, setEvalAction] = useState("listing.publish");
  const [evalContext, setEvalContext] = useState("");
  const [decision, setDecision] = useState<RiskDecision | null>(null);
  const [evaluating, setEvaluating] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("/api/risk");
        const payload = await response.json();
        if (!response.ok) {
          throw new Error(payload.error ?? "加载风控数据失败");
        }
        setData(payload.data as RiskData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "加载风控数据失败");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  async function handleEvaluate() {
    setEvaluating(true);
    setDecision(null);
    try {
      let context: Record<string, unknown> | undefined;
      if (evalContext.trim()) {
        try {
          context = JSON.parse(evalContext);
        } catch {
          setError("Context 必须是合法 JSON");
          setEvaluating(false);
          return;
        }
      }
      const response = await fetch("/api/risk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: evalAction, context }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error ?? "评估失败");
      }
      setDecision(payload.data as RiskDecision);
    } catch (err) {
      setError(err instanceof Error ? err.message : "评估失败");
    } finally {
      setEvaluating(false);
    }
  }

  const groupedRules = data
    ? (["L0", "L1", "L2"] as RiskLevel[]).map((level) => ({
        level,
        rules: data.rules.rules.filter((r) => r.risk_level === level),
      }))
    : [];

  return (
    <AppShell
      title="风控规则配置"
      description="L0/L1/L2 三级风控规则查看与模拟评估（MV1-08）"
    >
      {loading ? <p className="text-sm text-[var(--muted)]">加载中…</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      {data ? (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            <div className="card">
              <p className="text-sm text-[var(--muted)]">规则总数</p>
              <p className="mt-2 text-3xl font-semibold">
                {data.rules.rules.length}
              </p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                v{data.rules.version}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-[var(--muted)]">L0 自动放行</p>
              <p className="mt-2 text-3xl font-semibold text-emerald-600">
                {data.rules.summary.L0}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-[var(--muted)]">L1 需人审</p>
              <p className="mt-2 text-3xl font-semibold text-amber-600">
                {data.rules.summary.L1}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-[var(--muted)]">L2 拒绝</p>
              <p className="mt-2 text-3xl font-semibold text-rose-600">
                {data.rules.summary.L2}
              </p>
            </div>
          </div>

          <div>
            <h2 className="mb-3 text-lg font-semibold">规则列表</h2>
            <div className="space-y-4">
              {groupedRules.map(({ level, rules }) => (
                <div key={level}>
                  <h3 className="mb-2 text-sm font-medium text-[var(--muted)]">
                    {level} — {rules.length} 条规则
                  </h3>
                  <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50 dark:bg-slate-800">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium">
                            规则 ID
                          </th>
                          <th className="px-3 py-2 text-left font-medium">
                            动作
                          </th>
                          <th className="px-3 py-2 text-left font-medium">
                            效果
                          </th>
                          <th className="px-3 py-2 text-left font-medium">
                            优先级
                          </th>
                          <th className="px-3 py-2 text-left font-medium">
                            条件
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                        {rules.map((rule) => (
                          <tr key={rule.rule_id}>
                            <td className="px-3 py-2 font-mono text-xs">
                              {rule.rule_id}
                            </td>
                            <td className="px-3 py-2">
                              <span
                                className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${RISK_LEVEL_STYLES[rule.risk_level]}`}
                              >
                                {rule.action}
                              </span>
                            </td>
                            <td className="px-3 py-2">
                              {EFFECT_LABELS[rule.effect] ?? rule.effect}
                            </td>
                            <td className="px-3 py-2 text-[var(--muted)]">
                              {rule.priority}
                            </td>
                            <td className="px-3 py-2 text-xs text-[var(--muted)]">
                              {rule.conditions.length > 0
                                ? rule.conditions
                                    .map(
                                      (c) =>
                                        `${c.field} ${c.operator} ${String(c.value)}`,
                                    )
                                    .join(", ")
                                : "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h2 className="mb-3 text-lg font-semibold">模拟评估</h2>
            <div className="card space-y-3">
              <div className="flex gap-3">
                <select
                  value={evalAction}
                  onChange={(e) => setEvalAction(e.target.value)}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm dark:border-slate-700"
                >
                  {ACTION_OPTIONS.map((action) => (
                    <option key={action} value={action}>
                      {action}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleEvaluate}
                  disabled={evaluating}
                  className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
                >
                  {evaluating ? "评估中…" : "评估"}
                </button>
              </div>
              <input
                type="text"
                value={evalContext}
                onChange={(e) => setEvalContext(e.target.value)}
                placeholder='Context JSON（可选），如 {"daily_budget": 15000}'
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono dark:border-slate-700"
              />
              {decision ? (
                <div
                  className={`rounded-lg p-3 ${
                    decision.effect === "allow"
                      ? "bg-emerald-50 dark:bg-emerald-900/20"
                      : decision.effect === "deny"
                        ? "bg-rose-50 dark:bg-rose-900/20"
                        : "bg-amber-50 dark:bg-amber-900/20"
                  }`}
                >
                  <p className="text-sm font-medium">
                    {decision.effect === "allow"
                      ? "✓ 自动放行"
                      : decision.effect === "deny"
                        ? "✗ 拒绝"
                        : "⚠ 需人工审核"}
                  </p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    规则：{decision.rule_id} · 风险等级：{decision.risk_level}
                  </p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    {decision.message}
                  </p>
                </div>
              ) : null}
            </div>
          </div>

          <div>
            <h2 className="mb-3 text-lg font-semibold">
              审计日志（最近 20 条）
            </h2>
            {data.audit.items.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">暂无审计记录</p>
            ) : (
              <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 dark:bg-slate-800">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium">时间</th>
                      <th className="px-3 py-2 text-left font-medium">动作</th>
                      <th className="px-3 py-2 text-left font-medium">
                        操作者
                      </th>
                      <th className="px-3 py-2 text-left font-medium">结果</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                    {data.audit.items.map((item) => (
                      <tr key={item.id}>
                        <td className="px-3 py-2 text-xs text-[var(--muted)]">
                          {item.created_at}
                        </td>
                        <td className="px-3 py-2 font-mono text-xs">
                          {item.action}
                        </td>
                        <td className="px-3 py-2">{item.actor}</td>
                        <td className="px-3 py-2 text-xs">
                          {item.detail
                            ? `${String(item.detail.effect ?? "")} / ${String(item.detail.risk_level ?? "")}`
                            : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
